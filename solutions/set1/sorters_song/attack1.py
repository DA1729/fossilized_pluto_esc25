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

if 'stm' in platform or platform=='cwnano':
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
n=256
recovered=bytearray()

target_type = cw.targets.SimpleSerial2 if ss_ver=='ss_ver_2_1' else cw.targets.SimpleSerial
try:
    target=cw.target(scope, target_type)
except Exception:
    scope=cw.scope()
    target=cw.target(scope, target_type)

target.simpleserial_write('x', b'')
target.simpleserial_read('r', 1)

for k in range(15):
    print(f'attacking byte {k}')
    payload=bytearray([1,0,0,k])
    target.simpleserial_write('p', payload)
    target.simpleserial_read('r', 2)
    scope.arm()
    target.simpleserial_write('c', b'')
    target.simpleserial_read('r', 1)
    if scope.capture():
        print('timeout capturing ref trace, aborting')
        break
    trace_ref=scope.get_last_trace()
    if trace_ref is None:
        print('failed to capture ref trace, aborting')
        break
    sad_values=[]
    for g in trange(n, desc=f'byte {k}'):
        payload=bytearray([1, g, 0, k])
        target.simpleserial_write('p', payload)
        target.simpleserial_read('r', 2)
        scope.arm()
        target.simpleserial_write('c', b'')
        target.simpleserial_read('r', 1)
        if scope.capture():
            sad_values.append(0)
            continue
        trace_g=scope.get_last_trace()
        if trace_g is None:
            sad_values.append(0)
            continue
        sad=int(np.sum(np.abs(trace_g - trace_ref)))
        sad_values.append(sad)
    sad_array=np.array(sad_values)
    threshold=np.max(sad_array)/2
    jump_index=int(np.argmax(sad_array>threshold))
    if jump_index==0 and sad_array[0]<threshold:
        print(f'warning: no jump detected for k={k}, assuming 254')
        secret_byte_k=254
    else:
        secret_byte_k=jump_index-1
    print(f'recovered byte {k}: {secret_byte_k}')
    recovered.append(secret_byte_k)

print('full array recovered:', list(recovered))

if len(recovered)==15:
    print('attempting to retrieve flag...')
    target.simpleserial_write('a', recovered)
    resp=target.simpleserial_read('r', 20, ack=False)
    if resp:
        try:
            flag=resp.decode('utf-8')
            print('response from target:', flag)
            if 'thisisnotdaflag' not in flag.lower():
                print('cool')
            else:
                print('>>> failed: array incorrect <<<')
        except Exception:
            print('raw response:', resp)
    else:
        print('no response from target after sending array')
else:
    print(f'error: recovered {len(recovered)}/15 bytes')

print('disconnecting')
try:
    scope.dis()
    target.dis()
except Exception:
    pass

