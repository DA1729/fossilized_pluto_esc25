import chipwhisperer as cw
import numpy as np
from tqdm import trange
import time

scopetype = 'CWNANO'
platform = 'CWNANO'
ss_ver = 'SS_VER_1_1'
firmware = 'sortersSong-CWNANO.hex'
sample_size = 700
array_length = 15

def setup():
    try:
        scope = cw.scope()
        if not scope.connectStatus:
            scope.con()
    except Exception:
        scope = cw.scope()
    prog = cw.programmers.STM32FProgrammer
    scope.default_setup()
    return scope, prog

def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)

def get_trace_8bit(target, scope, k, guess):
    payload = bytearray([1, guess & 0xff, 0, k])
    target.simpleserial_write('p', payload)
    target.simpleserial_read('r', 2)
    scope.arm()
    target.simpleserial_write('c', b'')
    target.simpleserial_read('r', 1)
    if scope.capture():
        return None
    return scope.get_last_trace()

def get_trace_16bit(target, scope, k, g):
    payload = bytearray([2, g & 0xff, (g >> 8) & 0xff, k])
    target.simpleserial_write('p', payload)
    target.simpleserial_read('r', 2)
    scope.arm()
    target.simpleserial_write('d', b'')
    target.simpleserial_read('r', 1)
    if scope.capture():
        return None
    return scope.get_last_trace()

def attack_byte_binary_search(target, scope, byte_index):
    trace_ref = get_trace_8bit(target, scope, byte_index, 0)
    trace_max = get_trace_8bit(target, scope, byte_index, 255)
    if trace_ref is None or trace_max is None:
        return None
    sad_baseline = int(np.sum(np.abs(trace_max - trace_ref)))
    sad_threshold = sad_baseline // 2
    low = 0
    high = 255
    for _ in trange(8, desc=f'byte {byte_index}', leave=False):
        guess = (low + high) // 2
        trace_guess = get_trace_8bit(target, scope, byte_index, guess)
        if trace_guess is None:
            continue
        sad = int(np.sum(np.abs(trace_guess - trace_ref)))
        if sad > sad_threshold:
            high = guess - 1
        else:
            low = guess + 1
    return high

def attack_16bit_binary_search(target, scope, value_index):
    trace_ref = get_trace_16bit(target, scope, value_index, 0)
    trace_max = get_trace_16bit(target, scope, value_index, 65535)
    if trace_ref is None or trace_max is None:
        return None
    sad_baseline = int(np.sum(np.abs(trace_max - trace_ref)))
    sad_threshold = sad_baseline // 2
    low = 0
    high = 65535
    for _ in trange(16, desc=f'value {value_index}', leave=False):
        g = (low + high) // 2
        trace_g = get_trace_16bit(target, scope, value_index, g)
        if trace_g is None:
            continue
        sad = int(np.sum(np.abs(trace_g - trace_ref)))
        if sad > sad_threshold:
            high = g - 1
        else:
            low = g + 1
    return high

def main():
    attack_start = time.time()
    scope, prog = setup()
    scope.adc.samples = sample_size
    target_type = cw.targets.SimpleSerial2 if ss_ver == 'SS_VER_2_1' else cw.targets.SimpleSerial
    try:
        target = cw.target(scope, target_type)
    except Exception:
        scope = cw.scope()
        target = cw.target(scope, target_type)
    cw.program_target(scope, prog, firmware)
    reset_target(scope)
    target.simpleserial_write('x', b'')
    target.simpleserial_read('r', 1)
    recovered = bytearray()
    for k in range(array_length):
        secret_byte = attack_byte_binary_search(target, scope, k)
        if secret_byte is None:
            print(f'failed at byte {k}')
            break
        recovered.append(secret_byte)
    print(f'array: {list(recovered)}')
    if len(recovered) == array_length:
        target.simpleserial_write('a', recovered)
        response = target.simpleserial_read('r', 20, ack=False)
        if response:
            try:
                flag = response.decode('utf-8')
                if 'thisisnotdaflag' not in flag.lower():
                    print(f'flag: {flag}')
            except Exception:
                print(f'raw: {response}')
    recovered_16bit = []
    for k in range(15):
        secret_value = attack_16bit_binary_search(target, scope, k)
        if secret_value is None:
            print(f'failed at value {k}')
            break
        recovered_16bit.append(secret_value)
    print(f'values: {recovered_16bit}')
    if len(recovered_16bit) == 15:
        final = bytearray()
        for v in recovered_16bit:
            final.append(v & 0xff)
            final.append((v >> 8) & 0xff)
        target.simpleserial_write('b', final)
        response = target.simpleserial_read('r', 20, ack=False)
        if response:
            try:
                flag = response.decode('utf-8')
                if 'q3l!x9bx2f' not in flag.lower():
                    print(f'flag: {flag}')
            except Exception:
                print(f'raw: {response}')
    attack_end = time.time()
    total_time = attack_end - attack_start
    print(f'time: {total_time:.2f}s')
    total_queries = array_length * (2 + 8) + 15 * (2 + 16)
    print(f'queries: {total_queries}')
    try:
        scope.dis()
        target.dis()
    except Exception:
        pass

if __name__ == '__main__':
    main()

