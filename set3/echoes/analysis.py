import chipwhisperer as cw
import numpy as np
import matplotlib.pyplot as plt
import time
from tqdm import trange
from scipy.signal import savgol_filter

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

fw_path = "../../../challenges/set3/chaos-CWNANO.hex"
cw.program_target(scope, prog, fw_path)

print("Resetting target...")
reset_target(scope)
print("Target is now running.")

# Analysis parameters
scope.adc.samples = 2000
pos_to_check = 0  # Analyze position 0 as example
num_plots = 10
guesses = np.linspace(0, 65535, num_plots, dtype=np.uint16)

N = 100        # Number of traces per guess
skip_traces = 10

print(f"\nAnalyzing power consumption for position {pos_to_check}")
print(f"Capturing {N} traces per guess (averaging last {N - skip_traces})...\n")

# Setup plots
fig, axs = plt.subplots(5, 2, figsize=(15, 20))
axs = axs.flatten()

all_avg_traces = []
windowed_sums = []

# Window to analyze (will be optimized per position in attack)
WINDOW_START = 0
WINDOW_END = 400

for i, guess_val in enumerate(guesses):
    print(f"Processing Guess {i+1}/{num_plots} (Value = {guess_val})...")
    avg_abs_trace = np.zeros(scope.adc.samples, dtype=np.float32)
    traces_captured = 0

    for j in trange(N, desc=f"Capturing for guess {guess_val}", leave=False):
        target.simpleserial_write('x', b'')
        target.simpleserial_read('r', 1)

        scope.arm()

        payload = bytearray([3, guess_val & 0xff, (guess_val >> 8) & 0xff, pos_to_check])

        target.simpleserial_write('p', payload)
        target.simpleserial_read('r', 1)

        ret = scope.capture()
        if ret:
            continue

        abs_trace = np.abs(scope.get_last_trace())

        # Apply preprocessing filter
        processed_trace = savgol_filter(abs_trace, window_length=11, polyorder=2)

        if j >= skip_traces:
            avg_abs_trace += processed_trace
            traces_captured += 1

    if traces_captured > 0:
        avg_abs_trace /= traces_captured

    all_avg_traces.append(avg_abs_trace)

    # Plot average traces
    axs[i].plot(avg_abs_trace)
    axs[i].axvline(WINDOW_START, color='r', linestyle='--', alpha=0.5, label='Window Start')
    axs[i].axvline(WINDOW_END, color='r', linestyle='--', alpha=0.5, label='Window End')
    axs[i].set_title(f'Avg. Filtered Power for Guess = {guess_val}')
    axs[i].set_xlabel('Sample Index')
    axs[i].set_ylabel('Avg. |Power|')
    axs[i].grid(True)
    axs[i].legend()

    # Calculate windowed sum
    window_sum = np.sum(avg_abs_trace[WINDOW_START:WINDOW_END])
    windowed_sums.append(window_sum)

plt.tight_layout()
plt.savefig('power_traces_analysis.png', dpi=150, bbox_inches='tight')
print("\nSaved: power_traces_analysis.png")
plt.close()

# Plot windowed sums vs guess values
plt.figure(figsize=(12, 6))
plt.plot(guesses, windowed_sums, 'bo-', linewidth=2, markersize=8)
plt.title(f'Windowed Energy Sum vs Guess Value (Position {pos_to_check})')
plt.xlabel('Guess Value')
plt.ylabel(f'Sum of |Power| in Window [{WINDOW_START}:{WINDOW_END}]')
plt.grid(True)
plt.savefig('windowed_energy_vs_guess.png', dpi=150, bbox_inches='tight')
print("Saved: windowed_energy_vs_guess.png")
plt.close()

# Plot difference from minimum energy guess
all_avg_traces = np.array(all_avg_traces)
min_energy_idx = np.argmin(windowed_sums)
reference_trace = all_avg_traces[min_energy_idx]

plt.figure(figsize=(15, 8))
for i, guess_val in enumerate(guesses):
    diff = all_avg_traces[i] - reference_trace
    plt.plot(diff, label=f'Guess {guess_val}', alpha=0.7)

plt.axhline(0, color='k', linestyle='--', alpha=0.3)
plt.title(f'Difference from Minimum Energy Trace (Reference: Guess {guesses[min_energy_idx]})')
plt.xlabel('Sample Index')
plt.ylabel('Power Difference')
plt.legend(loc='upper right', fontsize=8)
plt.grid(True)
plt.savefig('power_trace_differences.png', dpi=150, bbox_inches='tight')
print("Saved: power_trace_differences.png")
plt.close()

# Summary statistics
print(f"\n{'='*60}")
print(f"ANALYSIS SUMMARY FOR POSITION {pos_to_check}")
print(f"{'='*60}")
print(f"Windowed Energy Statistics:")
print(f"  Min: {np.min(windowed_sums):.2f} (Guess {guesses[np.argmin(windowed_sums)]})")
print(f"  Max: {np.max(windowed_sums):.2f} (Guess {guesses[np.argmax(windowed_sums)]})")
print(f"  Mean: {np.mean(windowed_sums):.2f}")
print(f"  Std: {np.std(windowed_sums):.2f}")
print(f"  Range: {np.max(windowed_sums) - np.min(windowed_sums):.2f}")
print(f"\nThis analysis shows the timing side-channel leakage.")
print(f"Different guess values result in different execution times,")
print(f"which can be exploited via binary search in the attack phase.")
print(f"{'='*60}\n")

# Cleanup
scope.dis()
target.dis()
