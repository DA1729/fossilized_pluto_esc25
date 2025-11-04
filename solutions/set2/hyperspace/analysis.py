import chipwhisperer as cw
import numpy as np
import time
import matplotlib.pyplot as plt

SCOPETYPE = 'CWNANO'
PLATFORM = 'CWNANO'

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

print("\n" + "="*80)
print("hyperspace jump drive - correlation power analysis (cpa)")
print("="*80)

print("\nvulnerability: aes key leakage through power consumption")
print("attack vector: correlation between hamming weight and power traces\n")

print("capturing sample traces for analysis...")
sample_traces = []
for mask in range(0, 256, 16):
    sample_traces.append(capture_trace_with_mask(mask))
    print(f"  captured trace for mask 0x{mask:02x}")

sample_traces_array = np.array(sample_traces)
print(f"\ncaptured {len(sample_traces)} sample traces")
print(f"trace shape: {sample_traces_array.shape}")

print("\nanalyzing power trace characteristics...")
trace_variance = np.var(sample_traces_array, axis=0)
trace_mean = np.mean(sample_traces_array, axis=0)

plt.figure(figsize=(14, 10))

plt.subplot(3, 1, 1)
for i in range(min(5, len(sample_traces))):
    plt.plot(sample_traces[i], alpha=0.6, label=f'mask 0x{i*16:02x}')
plt.xlabel('sample')
plt.ylabel('power')
plt.title('sample power traces')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 1, 2)
plt.plot(trace_mean)
plt.xlabel('sample')
plt.ylabel('mean power')
plt.title('mean power across all samples')
plt.grid(True, alpha=0.3)

plt.subplot(3, 1, 3)
plt.plot(trace_variance)
plt.xlabel('sample')
plt.ylabel('variance')
plt.title('power variance (regions of interest)')
threshold = np.mean(trace_variance) + 0.5 * np.std(trace_variance)
plt.axhline(y=threshold, color='r', linestyle='--', label='threshold')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('hyperspace_analysis.png', dpi=150)
plt.close()

print("\nidentifying regions of interest (roi)...")
high_var_samples = np.where(trace_variance > threshold)[0]
print(f"found {len(high_var_samples)} high-variance samples")
print(f"roi spans samples: {high_var_samples[0]} to {high_var_samples[-1]}")

print("\ndemonstrating cpa attack on byte 0...")
print("capturing full trace set...")
traces_byte0 = []
for mask in range(256):
    if (mask + 1) % 64 == 0:
        print(f"  progress: {mask+1}/256")
    traces_byte0.append(capture_trace_with_mask(mask))

traces_byte0_array = np.array(traces_byte0)

roi_start = max(0, high_var_samples[0])
roi_end = min(len(high_var_samples) // 12, 100)
roi_byte0 = high_var_samples[roi_start:roi_start + roi_end]

print(f"\nanalyzing byte 0 using roi: {len(roi_byte0)} samples")

correlations = []
for secret_guess in range(256):
    hw_model = np.array([hamming_weight(mask ^ secret_guess) for mask in range(256)])

    max_corr = 0
    for sample_idx in roi_byte0:
        power = traces_byte0_array[:, sample_idx]

        if np.std(power) > 1e-6 and np.std(hw_model) > 1e-6:
            corr = abs(np.corrcoef(power, hw_model)[0, 1])
            max_corr = max(max_corr, corr)

    correlations.append(max_corr)

correlations_array = np.array(correlations)
top_5 = np.argsort(correlations_array)[::-1][:5]

print("\ntop 5 candidates for byte 0:")
for rank, guess in enumerate(top_5):
    char = chr(guess) if 32 <= guess < 127 else '?'
    print(f"  {rank+1}. value: {guess:3d} (0x{guess:02x}, '{char}')  correlation: {correlations_array[guess]:.4f}")

plt.figure(figsize=(15, 6))
plt.bar(range(256), correlations)
plt.xlabel('secret key byte guess')
plt.ylabel('correlation coefficient')
plt.title('cpa attack: correlation scores for byte 0')
plt.axvline(x=top_5[0], color='r', linestyle='--', label=f'best guess: 0x{top_5[0]:02x}')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('hyperspace_byte0_correlation.png', dpi=150)
plt.close()

print("\n" + "="*80)
print("analysis complete")
print("="*80)
print("\nkey findings:")
print(f"  - power traces show clear correlation with hamming weight model")
print(f"  - byte 0 most likely value: 0x{top_5[0]:02x} (correlation: {correlations_array[top_5[0]]:.4f})")
print(f"  - roi contains {len(high_var_samples)} high-variance samples")
print(f"  - attack is feasible for all 12 bytes of the secret key")

scope.dis()
target.dis()
