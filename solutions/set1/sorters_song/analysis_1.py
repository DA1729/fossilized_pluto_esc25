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

scope.adc.samples = 700
k = 1
payload_0 = bytearray([1, 0, 0, k])
payload_255 = bytearray([1, 255, 0, k])

N_TRACES = 100
trace_0 = np.zeros(scope.adc.samples)
trace_255 = np.zeros(scope.adc.samples)

target.simpleserial_write('p', payload_0)
target.simpleserial_read('r', 2)
for _ in trange(N_TRACES, desc = 'capturing traces for guess 0'):
    scope.arm()
    target.simpleserial_write('c', b'')
    target.simpleserial_read('r', 1)
    ret = scope.capture()
    if ret:
        print('timeout')
        continue
    trace = scope.get_last_trace()

    if _ >= 9:
        trace_0 = np.add(trace_0, trace)

trace_0 /= (N_TRACES - 10)


target.simpleserial_write('p', payload_255)
target.simpleserial_read('r', 2)
for _ in trange(N_TRACES, desc = 'capturing traces for guess 255'):
    scope.arm()
    target.simpleserial_write('c', b'')
    target.simpleserial_read('r', 1)
    ret = scope.capture()
    if ret:
        print('timeout')
        continue
    trace = scope.get_last_trace()

    if _ >= 9:
        trace_255 = np.add(trace_255, trace)

trace_255 /= (N_TRACES - 10)

trace_254 = np.zeros(scope.adc.samples)

payload_254 = bytearray([1, 254, 0, k])
target.simpleserial_write('p', payload_254)
target.simpleserial_read('r', 2)
for _ in trange(N_TRACES, desc = 'capturing traces for guess 254'):
    scope.arm()
    target.simpleserial_write('c', b'')
    target.simpleserial_read('r', 1)
    ret = scope.capture()
    if ret:
        print('timeout')
        continue
    trace = scope.get_last_trace()

    if _ >= 9:
        trace_254 = np.add(trace_254, trace)

trace_254 /= (N_TRACES - 10)

plt.figure(figsize=(10, 6))

# Top subplot: trace_0
plt.subplot(2, 1, 1)
plt.plot(trace_0)
plt.title("Trace for Payload 0")
plt.xlabel("Sample")
plt.ylabel("Amplitude")

# Bottom subplot: trace_255
plt.subplot(2, 1, 2)
plt.plot(trace_255)
plt.title("Trace for Payload 255")
plt.xlabel("Sample")
plt.ylabel("Amplitude")

plt.tight_layout()
plt.savefig("traces_comparison.png", dpi=300)
plt.close()

print("Saved figure as traces_comparison.png")


plt.subplot(2, 1, 1)
plt.plot(np.abs(trace_0))
plt.title("Trace for Payload 0")
plt.xlabel("Sample")
plt.ylabel("Amplitude")

# Bottom subplot: trace_255
plt.subplot(2, 1, 2)
plt.plot(np.abs(trace_255))
plt.title("Trace for Payload 255")
plt.xlabel("Sample")
plt.ylabel("Amplitude")

plt.tight_layout()
plt.savefig("traces_comparison_abs.png", dpi=300)
plt.close()

power_1 = 0
power_2 = 0
for i in range(0, 400):
    power_1 += np.abs(trace_0)[i]
    power_2 += np.abs(trace_255)[i]

print(power_1)
print(power_2)

print("Calculating trace difference...")
# Subtract the averaged traces to isolate the difference
trace_diff = np.abs(trace_255) - np.abs(trace_0)

# Plot the difference
plt.figure(figsize=(10, 4))
plt.plot(trace_diff)
plt.title("Difference Plot (trace_255 - trace_0)")
plt.xlabel("Sample")
plt.ylabel("Difference in Amplitude")
plt.grid(True)
plt.savefig("traces_difference.png", dpi=300)
plt.close()


trace_diff1 = np.abs(trace_255) - np.abs(trace_254)

# Plot the difference
plt.figure(figsize=(10, 4))
plt.plot(trace_diff1)
plt.title("Difference Plot (trace_255 - trace_254)")
plt.xlabel("Sample")
plt.ylabel("Difference in Amplitude")
plt.grid(True)
plt.savefig("traces_difference1.png", dpi=300)
plt.close()


dff_pow1 = 0
dff_pow2 = 0

for i in range(0, 400):
    dff_pow1 += np.abs(trace_diff)[i]
    dff_pow2 += np.abs(trace_diff1)[i]

print(dff_pow1)
print(dff_pow2)

scope.dis()
target.dis()


