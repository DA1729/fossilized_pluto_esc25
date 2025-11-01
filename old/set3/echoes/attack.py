import chipwhisperer as cw
import numpy as np
import time
from tqdm import trange

SCOPETYPE = 'CWNANO'
PLATFORM = 'CWNANO'

# Fixed N_ANALYSIS for consistent automated recovery
N_ANALYSIS = 1000
SKIP_TRACES = 10

# ChipWhisperer Connection
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
    SS_VER="SS_VER_1_1"
    target_type = cw.targets.SimpleSerial

try:
    target = cw.target(scope, target_type)
except:
    print("INFO: Caught exception on reconnecting to target... reconnecting scope first.")
    scope = cw.scope()
    target = cw.target(scope, target_type)

if "STM" in PLATFORM or PLATFORM == "CWLITEARM" or PLATFORM == "CWNANO":
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
    else:
        scope.io.nrst = 'low'
        time.sleep(0.05)
        scope.io.nrst = 'high_z'
        time.sleep(0.05)

# Program target
fw_path = "../../../challenges/set3/chaos-CWNANO.hex"
print(f"Programming target with {fw_path}...")
cw.program_target(scope, prog, fw_path)
reset_target(scope)
print("Target is now running.\n")

# Optimization parameters
SAMPLE_SIZES = [1500, 2000, 3000, 5000]
WINDOW_CONFIGS = [
    (100, 30), (150, 30), (200, 30), (250, 30),
    (100, 50), (150, 50), (200, 50), (250, 50),
    (300, 50), (400, 50), (500, 50)
]

def capture_traces(guess_val, pos, N, skip):
    """Capture N power traces for a given guess value at position pos"""
    traces = []
    for i in range(N):
        target.simpleserial_write('x', b'')
        target.simpleserial_read('r', 1)
        scope.arm()
        payload = bytearray([3, guess_val & 0xff, (guess_val >> 8) & 0xff, pos])
        target.simpleserial_write('p', payload)
        target.simpleserial_read('r', 1)
        if ret := scope.capture():
            continue
        abs_trace = np.abs(scope.get_last_trace())
        if i >= skip:
            traces.append(abs_trace)
    return np.array(traces)

def optimize_parameters(pos):
    """Find optimal scope.adc.samples and window parameters for position pos"""
    print(f"\n{'='*80}")
    print(f"OPTIMIZING PARAMETERS FOR POSITION {pos}")
    print(f"{'='*80}")

    best_overall_accuracy = 0
    best_config = None

    for samples in SAMPLE_SIZES:
        scope.adc.samples = samples
        print(f"\n--- Testing with scope.adc.samples = {samples} ---")

        traces_low = capture_traces(0, pos, N_ANALYSIS, SKIP_TRACES)
        traces_high = capture_traces(65535, pos, N_ANALYSIS, SKIP_TRACES)

        if len(traces_low) == 0 or len(traces_high) == 0:
            print(f"Warning: No traces captured for sample size {samples}. Skipping.")
            continue

        best_accuracy_this_sample = 0
        best_window_this_sample = (0, 1)

        for win_size, step in WINDOW_CONFIGS:
            max_balanced_score = 0
            best_start = 0

            for start in range(0, samples - win_size, step):
                end = start + win_size
                sums_l = np.array([np.sum(t[start:end]) for t in traces_low])
                sums_h = np.array([np.sum(t[start:end]) for t in traces_high])
                thresh = (np.mean(sums_l) + np.mean(sums_h)) / 2

                len_l = len(sums_l) if len(sums_l) > 0 else 1
                len_h = len(sums_h) if len(sums_h) > 0 else 1

                if np.mean(sums_h) > np.mean(sums_l):
                    acc_low = np.sum(sums_l < thresh) / len_l
                    acc_high = np.sum(sums_h > thresh) / len_h
                else:
                    acc_low = np.sum(sums_l > thresh) / len_l
                    acc_high = np.sum(sums_h < thresh) / len_h

                balanced_score = (acc_low + acc_high) / 2
                if balanced_score > max_balanced_score:
                    max_balanced_score = balanced_score
                    best_start = start

            if max_balanced_score > best_accuracy_this_sample:
                best_accuracy_this_sample = max_balanced_score
                best_window_this_sample = (best_start, best_start + win_size)

        print(f"  Best window: [{best_window_this_sample[0]}:{best_window_this_sample[1]}]")
        print(f"  Balanced accuracy: {best_accuracy_this_sample*100:.2f}%")

        if best_accuracy_this_sample > best_overall_accuracy:
            best_overall_accuracy = best_accuracy_this_sample
            best_config = {
                'samples': samples,
                'window_start': best_window_this_sample[0],
                'window_end': best_window_this_sample[1],
                'traces_low': traces_low,
                'traces_high': traces_high
            }

    return best_config

def get_metric_for_guess(guess_val, pos, window_start, window_end, N, skip):
    """Compute windowed energy metric for a guess"""
    windowed_sum = 0
    traces_captured = 0

    for i in range(N):
        target.simpleserial_write('x', b'')
        target.simpleserial_read('r', 1)
        scope.arm()
        payload = bytearray([3, guess_val & 0xff, (guess_val >> 8) & 0xff, pos])
        target.simpleserial_write('p', payload)
        target.simpleserial_read('r', 1)

        if ret := scope.capture():
            continue

        abs_trace = np.abs(scope.get_last_trace())

        if i >= skip:
            windowed_sum += np.sum(abs_trace[window_start:window_end])
            traces_captured += 1

    if traces_captured == 0:
        return get_metric_for_guess(guess_val, pos, window_start, window_end, N, skip)

    return windowed_sum / traces_captured

def recover_byte(pos, config):
    """Recover the secret value at position pos using binary search"""
    window_start = config['window_start']
    window_end = config['window_end']
    traces_low = config['traces_low']
    traces_high = config['traces_high']

    scope.adc.samples = config['samples']

    sums_low = np.array([np.sum(t[window_start:window_end]) for t in traces_low])
    sums_high = np.array([np.sum(t[window_start:window_end]) for t in traces_high])
    threshold = (np.mean(sums_low) + np.mean(sums_high)) / 2

    if np.mean(sums_high) > np.mean(sums_low):
        oracle_direction = "NORMAL"
    else:
        oracle_direction = "INVERTED"

    print(f"\n{'='*80}")
    print(f"ATTACKING POSITION {pos}")
    print(f"{'='*80}")
    print(f"  scope.adc.samples = {scope.adc.samples}")
    print(f"  Window: [{window_start}:{window_end}]")
    print(f"  Threshold: {threshold:.6f}")
    print(f"  Oracle direction: {oracle_direction}")

    # Binary search
    search_low = 0
    search_high = 65535
    secret_val = 0

    pbar = trange(16, desc=f"Binary search pos={pos}")
    for iteration in pbar:
        mid = (search_low + search_high) // 2

        metric = get_metric_for_guess(mid, pos, window_start, window_end, N_ANALYSIS, SKIP_TRACES)

        is_short_path = False
        if oracle_direction == "NORMAL":
            if metric < threshold:
                is_short_path = True
        else:
            if metric > threshold:
                is_short_path = True

        if is_short_path:
            secret_val = mid
            search_low = mid + 1
            decision = "SHORT"
        else:
            search_high = mid
            decision = "LONG"

        pbar.set_description(f"pos={pos}, range=[{search_low}, {search_high}], {mid}={decision}")

        if search_low >= search_high:
            break

    print(f"\n  Recovered value for position {pos}: {secret_val}")
    return secret_val

# Main attack loop - recover all 15 bytes
print(f"\n{'='*80}")
print(f"AUTOMATED ECHOES ATTACK - RECOVERING ALL 15 BYTES")
print(f"N_ANALYSIS = {N_ANALYSIS}")
print(f"{'='*80}\n")

recovered_array = []

for pos in range(15):
    print(f"\n{'#'*80}")
    print(f"# BYTE {pos}/14")
    print(f"{'#'*80}")

    # Optimize parameters for this position
    config = optimize_parameters(pos)

    # Recover the byte value
    value = recover_byte(pos, config)
    recovered_array.append(value)

    print(f"\n✓ Position {pos} complete: {value}")
    print(f"  Progress: {recovered_array}")

# Display final recovered array
print(f"\n{'='*80}")
print(f"ALL BYTES RECOVERED!")
print(f"{'='*80}")
print(f"\nRecovered array:")
print(f"{recovered_array}")

# Sort and create payload
leaked_array = np.array(recovered_array, dtype=np.uint16)
sorted_array = np.sort(leaked_array)
payload = bytearray(30)
for i, val in enumerate(sorted_array):
    payload[i*2]   = val & 0xff
    payload[i*2+1] = (val >> 8) & 0xff

print(f"\nSorted array:")
print(f"{sorted_array}")
print(f"\nPacked payload (hex): {payload.hex()}")

# Get the flag
print(f"\n{'='*80}")
print(f"RETRIEVING FLAG")
print(f"{'='*80}")

FLAG_LEN = 20
target.simpleserial_write('a', payload)
resp = target.simpleserial_read('r', FLAG_LEN)

if resp:
    try:
        flag_str = resp.decode('utf-8').strip()
        print(f"\n{'='*80}")
        print(f"  SUCCESS! FLAG: {flag_str}")
        print(f"{'='*80}\n")
    except UnicodeDecodeError:
        print(f"\nReceived raw bytes (could not decode): {resp}")
else:
    print("\nFAILURE: No response received.")

# Cleanup
print("Disconnecting from target.")
scope.dis()
target.dis()
