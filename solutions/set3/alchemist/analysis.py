import chipwhisperer as cw
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from tqdm import trange
import secrets
import time
import sys

SCOPETYPE = 'CWNANO'
PLATFORM = 'CWNANO'
N_TRACE = 1000
FW_PATH = "../../../challenges/set3/alchemistInfuser-CWNANO.hex"
TRACE_FILE = 'traces.npy'
ANALYSIS_END_SAMPLE = 3250
PEAK_DISTANCE = 100
PEAK_HEIGHT_FRACTION = 0.15

try:
    scope = cw.scope()
except Exception as e:
    print(f"error: could not connect to scope: {e}")
    sys.exit(1)

try:
    try:
        if SS_VER == "SS_VER_2_1":
            target_type = cw.targets.SimpleSerial2
        else:
            target_type = cw.targets.SimpleSerial
    except NameError:
        target_type = cw.targets.SimpleSerial

    target = cw.target(scope, target_type)
except Exception as e:
    print(f"error: could not connect to target: {e}")
    scope.dis()
    sys.exit(1)

if "STM" in PLATFORM or PLATFORM == "CWLITEARM" or PLATFORM == "CWNANO":
    prog = cw.programmers.STM32FProgrammer
else:
    prog = None

time.sleep(0.05)
try:
    scope.default_setup()
    scope.adc.samples = 5000
    num_samples = scope.adc.samples
except Exception as e:
    print(f"error: could not setup scope: {e}")
    scope.dis()
    target.dis()
    sys.exit(1)

def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)

try:
    print("programming target...")
    cw.program_target(scope, prog, FW_PATH)
    print("resetting target...")
    reset_target(scope)
    print("target is now running.")
except Exception as e:
    print(f"error: programming/reset failed: {e}")
    scope.dis()
    target.dis()
    sys.exit(1)

print(f"\ncapturing {N_TRACE} traces...")
all_traces = np.zeros((N_TRACE, num_samples), dtype=np.float32)
all_plaintexts = np.zeros((N_TRACE, 8), dtype=np.uint8)

capture_errors = 0
for i in trange(N_TRACE, desc='capturing traces'):
    pt_data = bytearray(secrets.token_bytes(8))
    scope.arm()

    target.simpleserial_write('e', pt_data)
    ret = scope.capture()
    if ret:
        print(f'timeout on trace {i}')
        capture_errors += 1
        all_traces[i] = np.zeros(num_samples, dtype=np.float32)
        all_plaintexts[i] = np.zeros(8, dtype=np.uint8)
        continue

    all_traces[i] = scope.get_last_trace()
    all_plaintexts[i] = pt_data

print(f"capture complete. {capture_errors} errors encountered.")

print(f"\nsaving traces to {TRACE_FILE}...")
np.save(TRACE_FILE, all_traces)
print("traces saved successfully.")

print(f"\nanalyzing traces from {TRACE_FILE} (samples 0-{ANALYSIS_END_SAMPLE})...")
num_traces, num_samples = all_traces.shape
print(f"loaded {num_traces} traces with {num_samples} samples each.")

if ANALYSIS_END_SAMPLE >= num_samples:
    print(f"warning: analysis_end_sample ({ANALYSIS_END_SAMPLE}) >= num_samples ({num_samples}). analyzing full trace.")
    ANALYSIS_END_SAMPLE = num_samples - 1

print("calculating standard deviation...")
std_devs_full = np.std(all_traces, axis=0)
std_devs = std_devs_full[:ANALYSIS_END_SAMPLE + 1]
max_std_dev_in_range = np.max(std_devs)
peak_height_threshold = max_std_dev_in_range * PEAK_HEIGHT_FRACTION

print(f"finding peaks with distance={PEAK_DISTANCE}, height={peak_height_threshold:.4f}...")
peaks, properties = find_peaks(std_devs, distance=PEAK_DISTANCE, height=peak_height_threshold)
num_peaks_found = len(peaks)
print(f"found {num_peaks_found} peaks within samples 0-{ANALYSIS_END_SAMPLE}.")

print("generating combined plot...")
fig, axs = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

x_axis = np.arange(ANALYSIS_END_SAMPLE + 1)

axs[0].plot(x_axis, all_traces[0, :ANALYSIS_END_SAMPLE + 1], label='sample raw trace (trace 0)', linewidth=0.8)
axs[0].set_ylabel("amplitude")
axs[0].set_title(f"sample trace vs. standard deviation & peaks (samples 0-{ANALYSIS_END_SAMPLE})")
axs[0].grid(True, linestyle=':')
axs[0].legend(loc='upper right')
axs[0].set_xlim(0, ANALYSIS_END_SAMPLE)

axs[1].plot(x_axis, std_devs, label='standard deviation', linewidth=1, color='orange')
axs[1].plot(peaks, std_devs[peaks], "rx", markersize=8, label=f'detected peaks ({num_peaks_found})')
axs[1].set_xlabel("sample index")
axs[1].set_ylabel("standard deviation")
axs[1].grid(True, linestyle=':')
axs[1].legend(loc='upper right')
axs[1].set_xlim(0, ANALYSIS_END_SAMPLE)

for i, peak_idx in enumerate(peaks):
    axs[0].axvline(x=peak_idx, color='gray', linestyle='--', linewidth=0.5)
    axs[1].axvline(x=peak_idx, color='gray', linestyle='--', linewidth=0.5)
    axs[1].text(peak_idx + 2, std_devs[peak_idx], f'{i}', fontsize=8, color='red')

plt.tight_layout()
plot_filename = "alchemist_peak_analysis.png"
plt.savefig(plot_filename)
print(f"plot saved to {plot_filename}")
plt.close()

print("\ndetected peak offsets (sample indices):")
print(peaks.tolist())

if num_peaks_found == 16:
    print("\nsuccess: found exactly 16 peaks!")
    print("peak offsets for attack script:")
    print(f"op_offsets = {peaks.tolist()}")
elif num_peaks_found < 16:
    print(f"\nwarning: found fewer than 16 peaks ({num_peaks_found}).")
    print("try decreasing peak_distance or peak_height_fraction.")
else:
    print(f"\nwarning: found more than 16 peaks ({num_peaks_found}).")
    print("try increasing peak_distance or peak_height_fraction.")

print("\nanalysis complete.")

scope.dis()
target.dis()
print("scope and target disconnected.")
