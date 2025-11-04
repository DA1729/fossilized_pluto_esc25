import chipwhisperer as cw
import numpy as np
import time

scopetype = 'CWNANO'
platform = 'CWNANO'

try:
    if not scope.connectStatus:
        scope.con()
except NameError:
    scope = cw.scope()

target_type = cw.targets.SimpleSerial
try:
    target = cw.target(scope, target_type)
except:
    scope = cw.scope()
    target = cw.target(scope, target_type)

prog = cw.programmers.STM32FProgrammer
time.sleep(0.05)
scope.default_setup()

fw_path = "../../../challenges/set2/hyperspaceJumpDrive-CWNANO.hex"
cw.program_target(scope, prog, fw_path)

def hamming_weight(n):
    return bin(n & 0xFF).count('1')

def capture_trace_with_mask(mask_value):
    scope.arm()
    target.simpleserial_write('p', bytearray([mask_value]))
    scope.capture()
    _ = target.simpleserial_read('r', 1, timeout=100)
    return scope.get_last_trace()


traces = []
for mask in range(256):
    traces.append(capture_trace_with_mask(mask))

traces_array = np.array(traces)

trace_variance = np.var(traces_array, axis=0)
threshold = np.mean(trace_variance) + 0.5 * np.std(trace_variance)
high_var_samples = np.where(trace_variance > threshold)[0]

roi_per_byte = []
chunk_size = max(1, len(high_var_samples) // 12)
for i in range(12):
    start = i * chunk_size
    end = (i + 1) * chunk_size if i < 11 else len(high_var_samples)
    roi = high_var_samples[start:end]
    if len(roi) > 100:
        roi = roi[::len(roi)//100]
    roi_per_byte.append(roi)

recovered_bytes = []

for byte_idx in range(12):
    roi = roi_per_byte[min(byte_idx, len(roi_per_byte)-1)]
    if len(roi) == 0:
        roi = list(range(100, min(500, traces_array.shape[1])))
    best_guess = 0
    best_corr = -1
    for secret_guess in range(256):
        hw_model = np.array([hamming_weight(mask ^ secret_guess) for mask in range(256)])
        max_corr = 0
        for sample_idx in roi:
            power = traces_array[:, sample_idx]
            if np.std(power) > 1e-6 and np.std(hw_model) > 1e-6:
                corr = abs(np.corrcoef(power, hw_model)[0, 1])
                max_corr = max(max_corr, corr)
        if max_corr > best_corr:
            best_corr = max_corr
            best_guess = secret_guess
    recovered_bytes.append(best_guess)

secret_ints = []
for i in range(3):
    val = (recovered_bytes[i*4] + (recovered_bytes[i*4+1] << 8) +
           (recovered_bytes[i*4+2] << 16) + (recovered_bytes[i*4+3] << 24))
    secret_ints.append(val)

print(f'secret: {secret_ints}')
print(f'hex: {[hex(i) for i in secret_ints]}')

payload = bytearray()
for val in secret_ints:
    payload.extend([val & 0xFF, (val >> 8) & 0xFF,
                    (val >> 16) & 0xFF, (val >> 24) & 0xFF])

target.simpleserial_write('a', payload)
resp = target.simpleserial_read('r', 17, timeout=200)

if resp:
    result = resp.decode('utf-8', errors='replace').strip()
    if "FailureToLaunch" not in result:
        print(f'flag: {result}')

total_queries = 256
print(f'queries: {total_queries}')

scope.dis()
target.dis()
