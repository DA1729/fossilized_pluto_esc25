import chipwhisperer as cw
import time
import numpy as np
import matplotlib.pyplot as plt
import chipwhisperer.common.api.browser as cwb

# --- Configuration ---
SCOPETYPE = 'CWNANO'
PLATFORM = 'CWNANO'
SS_VER = 'SS_VER_1_1'
FW_PATH = "../../../challenges/set1/sortersSong-CWNANO.hex"

# --- Setup Scope and Target ---
print("Connecting to scope and target...")
try:
    if not scope.connectStatus:
        scope.con()
except NameError:
    scope = cw.scope()

try:
    if SS_VER == "SS_VER_2_1":
        target_type = cw.targets.SimpleSerial2
    else:
        target_type = cw.targets.SimpleSerial
except:
    target_type = cw.targets.SimpleSerial

try:
    target = cw.target(scope, target_type)
except:
    print("INFO: Caught exception on reconnecting to target - re-connecting scope first.")
    scope = cw.scope()
    target = cw.target(scope, target_type)

if "STM" in PLATFORM or PLATFORM == "CWNANO":
    prog = cw.programmers.STM32FProgrammer
else:
    prog = None

time.sleep(0.05)
scope.default_setup()

def reset_target(scope):
    if PLATFORM == "CW303" or PLATFORM == "CWLITEXMEGA":
        scope.io.pdic = 'low'
        time.sleep(0.1)
        scope.io.pdic = 'high_z' 
        time.sleep(0.1)
    else:
        scope.io.nrst = 'low'
        time.sleep(0.05)
        scope.io.nrst = 'high_z'
        time.sleep(0.05)

# --- Program the Target ---
print("Programming target...")
cw.program_target(scope, prog, FW_PATH)
print("Resetting target...")
reset_target(scope)
print("Target is now running.")

# --- Analysis Phase ---

# Turn off interactive plotting
plt.ioff()

# Ensure secrets are initialized and locked by sending one command
print("Initializing secret arrays on target...")
target.simpleserial_write('x', b'')
target.simpleserial_read('r', 1)

N = 256  # Number of guesses (0-255)
k = 0    # We are attacking byte 0 (elements_to_skip = 0)
all_traces = []

print(f"Capturing {N} traces for byte {k}...")
for G in cw.tqdm(range(N), desc='Capturing traces'):
    
    # 1. Setup Phase: Send the 'p' command to set up data_arr1
    # We do NOT capture this part.
    payload = bytearray([1, G, 0, k])  # [array_select, G_low, G_high, k]
    target.simpleserial_write('p', payload)
    target.simpleserial_read('r', 2) # Clear UART buffer
    
    # 2. Capture Phase: Arm scope and capture the 'c' (sort_data1) command
    # This is the vulnerable operation.
    scope.arm()
    target.simpleserial_write('c', b'')
    
    ret = scope.capture(poll_done=True)
    if ret:
        print("Timeout during capture, skipping...")
        continue
    
    target.simpleserial_read('r', 1) # Clear UART buffer
    
    # Store the trace
    trace = scope.get_last_trace()
    all_traces.append(trace)

print("All traces captured.")

# --- Metric Analysis (Sum of Absolute Differences) ---
print("Calculating SAD metric...")
sad_values = []

if not all_traces:
    print("Error: No traces were captured. Exiting.")
    scope.dis()
    target.dis()
    exit()

# Use the trace from G=0 as the reference
ref_trace_wave = all_traces[0].wave
num_samples = len(ref_trace_wave)

for trace in all_traces:
    # Ensure all traces have the same length as the reference
    current_wave = trace.wave
    if len(current_wave) != num_samples:
        print(f"Warning: Trace length mismatch. Got {len(current_wave)}, expected {num_samples}. Truncating/Padding.")
        # Simple padding/truncating to make SAD calculation possible
        if len(current_wave) > num_samples:
            current_wave = current_wave[:num_samples]
        else:
            current_wave = np.pad(current_wave, (0, num_samples - len(current_wave)), 'edge')

    # Calculate Sum of Absolute Differences
    sad = np.sum(np.abs(current_wave - ref_trace_wave))
    sad_values.append(sad)

print("Metric calculation complete.")

# --- Save Plots (as requested) ---

# 1. Plot: Trace Overlay
print("Saving trace overlay plot...")
plt.figure()
for trace in all_traces:
    # Plot with low alpha to see density
    plt.plot(trace.wave, alpha=0.05, color='blue') 
plt.plot(ref_trace_wave, alpha=0.9, color='red', label='G=0 (Reference)') # Highlight ref trace
plt.title("Trace Overlay (All 256 Guesses for Byte 0)")
plt.xlabel("Sample Point")
plt.ylabel("Power")
plt.legend()
plt.savefig("byte0_traces_overlay.png")
plt.close()
print("Saved: byte0_traces_overlay.png")

# 2. Plot: SAD Metric vs. Guess
print("Saving SAD metric plot...")
plt.figure()
plt.plot(range(N), sad_values)
plt.title("SAD Metric vs. Guess (G) for Byte 0")
plt.xlabel("Guess (G)")
plt.ylabel("Sum of Absolute Differences (SAD)")
plt.grid(True)
plt.savefig("byte0_sad_metric.png")
plt.close()
print("Saved: byte0_sad_metric.png")

# --- Final Explanation ---
print("\n--- Analysis Complete ---")
print("Check the generated PNG files:")
print("1. 'byte0_traces_overlay.png': Shows all 256 traces plotted on top of each other.")
print("   You should visually see two distinct 'clumps' of traces, one for 'short' sorts and one for 'long' sorts.")
print("\n2. 'byte0_sad_metric.png': This is the key result.")
print("   It plots the SAD metric (difference from G=0) for each guess 'G'.")
print("   You should see a graph that is low and flat, and then 'jumps' or 'steps' up at a specific 'G' value.")
print("   The secret value of original_arr1[0] is the *last* 'G' value *before* the jump.")

# --- Cleanup ---
print("Disconnecting...")
scope.dis()
target.dis()
