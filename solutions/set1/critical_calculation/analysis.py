import chipwhisperer as cw
import time
import matplotlib.pyplot as plt
import os

SCOPETYPE = 'CWNANO'
PLATFORM = 'CWNANO'

# Setup scope and target (same initialization as before)
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
    SS_VER = "SS_VER_1_1"
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

time.sleep(0.05)
scope.default_setup()

def reboot_flush():
    scope.io.nrst = False
    time.sleep(0.05)
    scope.io.nrst = "high_z"
    time.sleep(0.05)
    target.flush()

fw_path = "../../../challenges/set1/criticalCalculation-CWNANO.hex".format(PLATFORM)
cw.program_target(scope, prog, fw_path)

scope.io.clkout = 7.5E6

from tqdm import trange
import numpy as np
import time


trace_array = []

N = 20  # Reduced for faster testing

for i in trange(N, desc = 'capturing traces'):
    scope.arm()
    target.simpleserial_write("d", bytearray([]))

    ret = scope.capture()

    if ret:
        print("target timed out")
        continue


    response = target.simpleserial_read_witherrors('r', 26)

    trace_array.append(scope.get_last_trace())

trace_array = np.array(trace_array)

# Save plots
print("Saving plots...")

# Plot all traces
plt.figure(figsize=(12, 6))
for trace in trace_array:
    plt.plot(trace, alpha=0.1, color='blue')
plt.title(f'All {N} Power Traces')
plt.xlabel('Sample')
plt.ylabel('Power')
plt.savefig('all_traces.png', dpi=150, bbox_inches='tight')
print("Saved: all_traces.png")
plt.close()

# Plot average trace
plt.figure(figsize=(12, 6))
avg_trace = np.mean(trace_array, axis=0)
plt.plot(avg_trace)
plt.title('Average Power Trace')
plt.xlabel('Sample')
plt.ylabel('Power')
plt.savefig('average_trace.png', dpi=150, bbox_inches='tight')
print("Saved: average_trace.png")
plt.close()

# Plot first few individual traces
plt.figure(figsize=(12, 6))
for i in range(min(10, len(trace_array))):
    plt.plot(trace_array[i], label=f'Trace {i+1}', alpha=0.7)
plt.title('First 10 Power Traces')
plt.xlabel('Sample')
plt.ylabel('Power')
plt.legend(loc='upper right', fontsize=8)
plt.savefig('first_10_traces.png', dpi=150, bbox_inches='tight')
print("Saved: first_10_traces.png")
plt.close()

scope.dis()
target.dis()
