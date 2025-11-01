import chipwhisperer as cw
import numpy as np
import matplotlib.pyplot as plt
from tqdm import trange

SCOPETYPE = 'CWNANO'
PLATFORM = 'CWNANO'


try:
    if not scope.connectStatus:
        scope.con()
except NameError:
    scope = cw.scope()

try:
    if SS_VER == "SS_VER_2_1":
        target_type = cw.targets.SimpleSerial2
    elif SS_VER == "SS_VER_2_0":
        raise OSError("SS_VER_2_0 is deprecated. Use SS_VER_2_1")
    else:
        target_type = cw.targets.SimpleSerial
except:
    SS_VER="SS_VER_1_1"
    target_type = cw.targets.SimpleSerial

try:
    target = cw.target(scope, target_type)
except:
    print("INFO: Caught exception on reconnecting to target - attempting to reconnect to scope first.")
    print("INFO: This is a work-around when USB has died without Python knowing. Ignore errors above this line.")
    scope = cw.scope()
    target = cw.target(scope, target_type)

if "STM" in PLATFORM or PLATFORM == "CWLITEARM" or PLATFORM == "CWNANO":
    prog = cw.programmers.STM32FProgrammer
elif PLATFORM == "CW303" or PLATFORM == "CWLITEXMEGA":
    prog = cw.programmers.XMEGAProgrammer
elif "neorv32" in PLATFORM.lower():
    prog = cw.programmers.NEORV32Programmer
elif "SAM4S" in PLATFORM or PLATFORM == "CWHUSKY":
    prog = cw.programmers.SAM4SProgrammer
else:
    prog = None

import time
time.sleep(0.05)
scope.default_setup()

def reset_target(scope):
    if PLATFORM == "CW303" or PLATFORM == "CWLITEXMEGA":
        scope.io.pdic = 'low'
        time.sleep(0.1)
        scope.io.pdic = 'high_z' #XMEGA doesn't like pdic driven high
        time.sleep(0.1) #xmega needs more startup time
    elif "neorv32" in PLATFORM.lower():
        raise IOError("Default iCE40 neorv32 build does not have external reset - reprogram device to reset")
    elif PLATFORM == "CW308_SAM4S" or PLATFORM == "CWHUSKY":
        scope.io.nrst = 'low'
        time.sleep(0.25)
        scope.io.nrst = 'high_z'
        time.sleep(0.25)
    else:  
        scope.io.nrst = 'low'
        time.sleep(0.05)
        scope.io.nrst = 'high_z'
        time.sleep(0.05)

fw_path = "../../../challenges/set1/sortersSong-CWNANO.hex".format(PLATFORM)
cw.program_target(scope, prog, fw_path)

print("Resetting target...")
reset_target(scope)
print("Target is now running.")

N = 256
k = 0
all_traces = []
N_TRACES = 100

print('capturing tracesi...')

for i in range(N):
    avg_trace = np.zeros(scope.adc.samples)
    payload = bytearray([1, i, 0, k])

    for _ in trange(N_TRACES, desc = 'capturing traces'):
        target.simpleserial_write('p', payload)
        target.simpleserial_read('r', 2)

        scope.arm()
        target.simpleserial_write('c', b'')
        ret = scope.capture()

        if ret:
            print('timeout')
            continue


        target.simpleserial_read('r', 1)

        trace = scope.get_last_trace()
        if _ >= 9:
            avg_trace = np.add(avg_trace, trace)

    avg_trace /= (N_TRACES - 10)
    all_traces.append(np.abs(avg_trace))

print('traces captured')


print('evaluating SAD metric')
sad_values = [] 
ref_wave = all_traces[0]

for j in all_traces:
    sad = np.sum(np.abs(current_wave - ref_trace_wave))
    sad_values.append(sad)


print('metric evaluation done')


plt.figure()
for j in all_traces:
    plt.plot(j, alpha = 0.05, color = 'blue')
plt.plot(ref_trace_wave, alpha = 0.9, color = 'red')

plt.title('trace overlay')
plt.xlabel("Sample Point")
plt.ylabel("Power")
plt.legend()
plt.savefig("byte0_traces_overlay.png")
plt.close()


plt.figure()
plt.plot(range(N), sad_values)
plt.title('SAD metric vs guess for byte 0')
plt.xlabel('guess')
plt.ylabel('SAD')
plt.grid(True)
plt.savefig('byte0_sad_metric.png')
plt.close()

print('done')


scope.dis()
target.dis()


