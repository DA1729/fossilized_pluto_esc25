import chipwhisperer as cw
import numpy as np
import time
from tqdm import trange

scopetype = 'CWNANO'
platform = 'CWNANO'

n_analysis = 1000
skip_traces = 10

try:
    if not scope.connectStatus:
        scope.con()
except NameError:
    scope = cw.scope()

try:
    if ss_ver == "SS_VER_2_1":
        target_type = cw.targets.SimpleSerial2
    else:
        target_type = cw.targets.SimpleSerial
except:
    ss_ver="SS_VER_1_1"
    target_type = cw.targets.SimpleSerial

try:
    target = cw.target(scope, target_type)
except:
    scope = cw.scope()
    target = cw.target(scope, target_type)

if "STM" in platform or platform == "CWLITEARM" or platform == "CWNANO":
    prog = cw.programmers.STM32FProgrammer
else:
    prog = None

time.sleep(0.05)
scope.default_setup()

def reset_target(scope):
    if platform == "CW303" or platform == "CWLITEXMEGA":
        scope.io.pdic = 'low'
        time.sleep(0.1)
        scope.io.pdic = 'high_z'
    else:
        scope.io.nrst = 'low'
        time.sleep(0.05)
        scope.io.nrst = 'high_z'
        time.sleep(0.05)

fw_path = "../../../challenges/set3/chaos-CWNANO.hex"
cw.program_target(scope, prog, fw_path)
reset_target(scope)

sample_sizes = [1500, 2000, 3000, 5000]
window_configs = [
    (100, 30), (150, 30), (200, 30), (250, 30),
    (100, 50), (150, 50), (200, 50), (250, 50),
    (300, 50), (400, 50), (500, 50)
]

def capture_traces(guess_val, pos, n, skip):
    traces = []
    for i in range(n):
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
    best_overall_accuracy = 0
    best_config = None
    for samples in sample_sizes:
        scope.adc.samples = samples
        traces_low = capture_traces(0, pos, n_analysis, skip_traces)
        traces_high = capture_traces(65535, pos, n_analysis, skip_traces)
        if len(traces_low) == 0 or len(traces_high) == 0:
            continue
        best_accuracy_this_sample = 0
        best_window_this_sample = (0, 1)
        for win_size, step in window_configs:
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

def get_metric_for_guess(guess_val, pos, window_start, window_end, n, skip):
    windowed_sum = 0
    traces_captured = 0
    for i in range(n):
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
        return get_metric_for_guess(guess_val, pos, window_start, window_end, n, skip)
    return windowed_sum / traces_captured

def recover_byte(pos, config):
    window_start = config['window_start']
    window_end = config['window_end']
    traces_low = config['traces_low']
    traces_high = config['traces_high']
    scope.adc.samples = config['samples']
    sums_low = np.array([np.sum(t[window_start:window_end]) for t in traces_low])
    sums_high = np.array([np.sum(t[window_start:window_end]) for t in traces_high])
    threshold = (np.mean(sums_low) + np.mean(sums_high)) / 2
    if np.mean(sums_high) > np.mean(sums_low):
        oracle_direction = "normal"
    else:
        oracle_direction = "inverted"
    search_low = 0
    search_high = 65535
    secret_val = 0
    pbar = trange(16, desc=f"pos={pos}")
    for iteration in pbar:
        mid = (search_low + search_high) // 2
        metric = get_metric_for_guess(mid, pos, window_start, window_end, n_analysis, skip_traces)
        is_short_path = False
        if oracle_direction == "normal":
            if metric < threshold:
                is_short_path = True
        else:
            if metric > threshold:
                is_short_path = True
        if is_short_path:
            secret_val = mid
            search_low = mid + 1
        else:
            search_high = mid
        if search_low >= search_high:
            break
    return secret_val


recovered_array = []

for pos in range(15):
    config = optimize_parameters(pos)
    value = recover_byte(pos, config)
    recovered_array.append(value)

print(f'array: {recovered_array}')

leaked_array = np.array(recovered_array, dtype=np.uint16)
sorted_array = np.sort(leaked_array)
payload = bytearray(30)
for i, val in enumerate(sorted_array):
    payload[i*2]   = val & 0xff
    payload[i*2+1] = (val >> 8) & 0xff

print(f'sorted: {list(sorted_array)}')

flag_len = 20
target.simpleserial_write('a', payload)
resp = target.simpleserial_read('r', flag_len)

if resp:
    try:
        flag_str = resp.decode('utf-8').strip()
        print(f'flag: {flag_str}')
    except UnicodeDecodeError:
        print(f'raw: {resp}')

total_queries = 15 * (n_analysis * 2 + 16 * n_analysis)
print(f'queries: {total_queries}')

scope.dis()
target.dis()
