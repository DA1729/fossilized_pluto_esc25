import chipwhisperer as cw
import numpy as np
from tqdm import trange
import time

scopetype='cwnano'
platform='cwnano'
ss_ver='ss_ver_1_1'
fw_path='../../../challenges/set1/sortersSong-CWNANO.hex'

try:
    scope
except NameError:
    scope=cw.scope()

try:
    if not scope.connectStatus:
        scope.con()
except Exception:
    scope=cw.scope()

if 'stm' in platform.lower() or platform=='cwnano':
    prog=cw.programmers.STM32FProgrammer
else:
    prog=None

scope.default_setup()

def reset_target(scope):
    scope.io.nrst='low'
    time.sleep(0.05)
    scope.io.nrst='high_z'
    time.sleep(0.05)

print('programming target...')
cw.program_target(scope, prog, fw_path)
print('resetting target...')
reset_target(scope)
print('target running')

scope.adc.samples=700
recovered=[]

target_type=cw.targets.SimpleSerial2 if ss_ver=='ss_ver_2_1' else cw.targets.SimpleSerial
try:
    target=cw.target(scope, target_type)
except Exception:
    scope=cw.scope()
    target=cw.target(scope, target_type)

target.simpleserial_write('x', b'')
target.simpleserial_read('r', 1)

def get_trace(k, g):
    payload=bytearray([2, g & 0xff, (g>>8)&0xff, k])
    target.simpleserial_write('p', payload)
    target.simpleserial_read('r', 2)
    scope.arm()
    target.simpleserial_write('d', b'')
    target.simpleserial_read('r', 1)
    if scope.capture():
        print(f'timeout at g={g}, k={k}')
        return None
    return scope.get_last_trace()

for k in range(15):
    print(f'attacking 16-bit value {k}')
    trace_ref=get_trace(k, 0)
    trace_long=get_trace(k, 65535)
    if trace_ref is None or trace_long is None:
        print('failed to get reference traces, aborting')
        break
    sad_baseline=int(np.sum(np.abs(trace_long - trace_ref)))
    sad_threshold=sad_baseline/2
    print(f'sad baseline={sad_baseline}, threshold={sad_threshold:.2f}')
    low=0
    high=65535
    for _ in trange(16, desc=f'binsearch value {k}'):
        g=(low+high)//2
        trace_g=get_trace(k, g)
        if trace_g is None:
            continue
        sad=int(np.sum(np.abs(trace_g - trace_ref)))
        if sad>sad_threshold:
            high=g-1
        else:
            low=g+1
    secret=high
    print(f'recovered value {k}: {secret}')
    recovered.append(secret)

print('recovered array:', recovered)

if len(recovered)==15:
    print('converting to 30-byte payload...')
    final=bytearray()
    for v in recovered:
        final.append(v & 0xff)
        final.append((v>>8)&0xff)
    print('attempting to retrieve flag...')
    target.simpleserial_write('b', final)
    resp=target.simpleserial_read('r', 20, ack=False)
    if resp:
        try:
            flag=resp.decode('utf-8')
            print('response from target:', flag)
            if 'q3l!x9bx2f' not in flag.lower():
                print('cool')
            else:
                print('>>> failed: array incorrect <<<')
        except Exception:
            print('raw response:', resp)
    else:
        print('no response from target')
else:
    print(f'error: recovered {len(recovered)}/15 values')

print('disconnecting')
try:
    scope.dis()
    target.dis()
except Exception:
    pass

