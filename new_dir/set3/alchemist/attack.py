import chipwhisperer as cw
import numpy as np
from tqdm import trange, tqdm
import secrets
import time
import itertools
import sys

SCOPETYPE = 'CWNANO'
PLATFORM = 'CWNANO'
N_TRACE = 5000
FW_PATH = "../../../challenges/set3/alchemistInfuser-CWNANO.hex"

def hw(n):
    return bin(n).count('1')
v_hw = np.vectorize(hw)

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
    print(f"warning: unknown platform {PLATFORM}, programming may fail.")

time.sleep(0.05)
try:
    scope.default_setup()
    scope.adc.samples = 5000
    num_samples = scope.adc.samples
except Exception as e:
    print(f"error: could not setup scope: {e}")
    if 'target' in locals() and target: target.dis()
    if 'scope' in locals() and scope: scope.dis()
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
if capture_errors > N_TRACE * 0.1:
    print("warning: high number of capture errors. results may be unreliable.")

MAX_SHIFT = 25
OP_WIDTH = 15
OP_OFFSETS = [
    59, 262, 465, 668, 871, 1074, 1277, 1480,
    1684, 1888, 2092, 2296, 2500, 2704, 2908, 3112
]

N = N_TRACE
candidates_0_7 = []

print("\nstarting phase 1 (key bytes 0-7)...")
for i in trange(8, desc='attacking key bytes 0-7'):
    window_start = OP_OFFSETS[i] - (OP_WIDTH // 2)
    window_end = window_start + OP_WIDTH

    if window_start < 0 or window_end >= num_samples:
        print(f"error: alignment window for byte {i} is out of bounds [{window_start}, {window_end}].")
        candidates_0_7.append((0, 0))
        continue

    ref_pattern = all_traces[0, window_start:window_end]
    resynced_traces = np.zeros_like(all_traces)
    resynced_traces[0] = all_traces[0]
    for j in range(1, N_TRACE):
        trace = all_traces[j]
        search_start = max(0, window_start - MAX_SHIFT)
        search_end = min(num_samples - OP_WIDTH, window_start + MAX_SHIFT)
        min_sad = np.inf
        best_shift = 0
        for shift_val in range(search_start, search_end):
            if shift_val + OP_WIDTH > num_samples: continue
            current_window = trace[shift_val : shift_val + OP_WIDTH]
            sad = np.sum(np.abs(ref_pattern - current_window))
            if sad < min_sad:
                min_sad = sad
                best_shift = shift_val - window_start
        new_trace = np.zeros(num_samples)
        if best_shift > 0: new_trace[:-best_shift] = trace[best_shift:]
        elif best_shift < 0: new_trace[-best_shift:] = trace[:best_shift]
        else: new_trace = trace
        resynced_traces[j] = new_trace

    traces_mean = np.mean(resynced_traces, axis=0)
    traces_std = np.std(resynced_traces, axis=0, ddof=1)
    plaintext_for_byte = all_plaintexts[:, i]
    hyp_array = np.zeros((N_TRACE, 256), dtype=np.uint8)
    for k_guess in range(256):
        intermediate_values = plaintext_for_byte ^ k_guess
        hyp_array[:, k_guess] = v_hw(intermediate_values)
    hyp_mean = np.mean(hyp_array, axis=0)
    hyp_std = np.std(hyp_array, axis=0, ddof=1)
    traces_std[traces_std == 0] = 1
    hyp_std[hyp_std == 0] = 1
    correlation_matrix = (resynced_traces.T @ hyp_array - N * traces_mean[:, None] * hyp_mean[None, :]) / ((N - 1) * traces_std[:, None] * hyp_std[None, :])
    correlation_matrix = correlation_matrix.T
    search_area_start = max(0, window_start - MAX_SHIFT)
    search_area_end = min(num_samples, window_end + MAX_SHIFT)
    corr_in_window = correlation_matrix[:, search_area_start : search_area_end]
    if corr_in_window.shape[1] == 0:
        print(f"error: correlation search window for byte {i} is empty!")
        candidates_0_7.append((0, 0))
        continue
    max_corrs_per_guess = np.max(np.abs(corr_in_window), axis=1)

    sorted_indices = np.argsort(max_corrs_per_guess)[::-1]
    top_4_guesses = sorted_indices[0:4]
    top_4_corrs = max_corrs_per_guess[top_4_guesses]

    candidates_0_7.append(top_4_guesses[0:2])

if any((c == 0).all() for c in candidates_0_7):
    print("\nerror: found dummy candidates (0,0) in phase 1 results due to errors.")
    print("attack cannot proceed. check alignment parameters and trace quality.")
    scope.dis()
    target.dis()
    sys.exit(1)

print(f'\nphase 1 done. candidate pairs: {[(hex(c[0]), hex(c[1])) for c in candidates_0_7]}')

print("\nstarting phase 2 & brute-force (2^16 keys)...")
key_half1_generator = itertools.product(*candidates_0_7)
found_flag = None
dummy_flag = b"deadlyWhiteJade!!"
for key_half_1 in tqdm(key_half1_generator, total=256, desc="checking 1st-half keys"):
    key_half_1 = bytearray(key_half_1)
    candidates_8_15 = []
    phase2_error = False
    for i in range(8, 16):
        pt_byte_index = i % 8
        window_start = OP_OFFSETS[i] - (OP_WIDTH // 2)
        window_end = window_start + OP_WIDTH
        if window_start < 0 or window_end >= num_samples:
            phase2_error = True
            break

        ref_pattern = all_traces[0, window_start:window_end]
        resynced_traces = np.zeros_like(all_traces)
        resynced_traces[0] = all_traces[0]
        for j in range(1, N_TRACE):
            trace = all_traces[j]
            search_start = max(0, window_start - MAX_SHIFT)
            search_end = min(num_samples - OP_WIDTH, window_start + MAX_SHIFT)
            min_sad = np.inf
            best_shift = 0
            for shift_val in range(search_start, search_end):
                if shift_val + OP_WIDTH > num_samples: continue
                current_window = trace[shift_val : shift_val + OP_WIDTH]
                sad = np.sum(np.abs(ref_pattern - current_window))
                if sad < min_sad:
                    min_sad = sad
                    best_shift = shift_val - window_start
            new_trace = np.zeros(num_samples)
            if best_shift > 0: new_trace[:-best_shift] = trace[best_shift:]
            elif best_shift < 0: new_trace[-best_shift:] = trace[:best_shift]
            else: new_trace = trace
            resynced_traces[j] = new_trace

        traces_mean = np.mean(resynced_traces, axis=0)
        traces_std = np.std(resynced_traces, axis=0, ddof=1)
        plaintexts_for_byte = all_plaintexts[:, pt_byte_index]
        known_key_byte = key_half_1[pt_byte_index]
        new_data_for_attack = plaintexts_for_byte ^ known_key_byte
        hyp_array = np.zeros((N_TRACE, 256), dtype=np.uint8)
        for k_guess in range(256):
            intermediate_values = new_data_for_attack ^ k_guess
            hyp_array[:, k_guess] = v_hw(intermediate_values)
        hyp_mean = np.mean(hyp_array, axis=0)
        hyp_std = np.std(hyp_array, axis=0, ddof=1)
        traces_std[traces_std == 0] = 1
        hyp_std[hyp_std == 0] = 1
        correlation_matrix = ((resynced_traces.T @ hyp_array - N * traces_mean[:, None] * hyp_mean[None, :]) / ((N - 1) * traces_std[:, None] * hyp_std[None, :])).T
        search_area_start = max(0, window_start - MAX_SHIFT)
        search_area_end = min(num_samples, window_end + MAX_SHIFT)
        corr_in_window = correlation_matrix[:, search_area_start : search_area_end]
        if corr_in_window.shape[1] == 0:
            phase2_error = True
            break
        max_corrs_per_guess = np.max(np.abs(corr_in_window), axis=1)
        sorted_indices = np.argsort(max_corrs_per_guess)[::-1]
        candidates_8_15.append(sorted_indices[0:2])

    if phase2_error: continue

    key_half2_generator = itertools.product(*candidates_8_15)
    for key_half_2 in key_half2_generator:
        key_half_2_bytes = bytearray(key_half_2)
        full_key = key_half_1 + key_half_2_bytes
        target.simpleserial_write('c', full_key)
        resp = target.simpleserial_read('r', 17)
        if resp and resp != dummy_flag:
            found_flag = resp
            print(f"\nkey found!")
            print(f"key (hex): {full_key.hex()}")
            try:
                print(f"flag: {found_flag.decode('utf-8')}")
            except UnicodeDecodeError:
                print(f"flag (hex): {found_flag.hex()}")
            break
    if found_flag: break

if not found_flag:
    print("\nbrute-force complete, no flag found.")
    print("if phase 1 looked good, double-check the op_offsets list or consider increasing n_trace.")

print("\nanalysis complete, disconnecting...")
try:
    scope.dis()
    target.dis()
    print("scope and target disconnected.")
except Exception as e:
    print(f"error during disconnect: {e}")
