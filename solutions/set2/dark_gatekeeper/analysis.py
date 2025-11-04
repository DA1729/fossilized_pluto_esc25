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
    print("reconnecting to scope...")
    scope = cw.scope()
    target = cw.target(scope, target_type)

prog = cw.programmers.STM32FProgrammer
time.sleep(0.05)
scope.default_setup()

fw_path = "../../../challenges/set2/darkGatekeeper-CWNANO.hex"
cw.program_target(scope, prog, fw_path)

print("="*80)
print("dark gatekeeper - differential power analysis")
print("="*80)

KEY_LENGTH = 12

def capture_trace(password):
    scope.arm()
    target.simpleserial_write('a', bytearray(password))
    ret = scope.capture()
    trace = scope.get_last_trace()

    try:
        resp = target.simpleserial_read('r', 18, timeout=100)
    except:
        resp = None

    return trace, resp

print("\nvulnerability: byte-by-byte comparison with power leakage")
print("attack vector: differential power analysis reveals correct bytes\n")

print("analyzing byte position 0...")
password_template = [0] * KEY_LENGTH

print("  capturing traces for sample values...")
sample_traces = {}
sample_values = [0, 50, 100, 150, 200, 250]

for val in sample_values:
    password_template[0] = val
    trace, _ = capture_trace(password_template)
    sample_traces[val] = trace
    print(f"    captured trace for value {val}")

print("\nvisualizing power differences...")
plt.figure(figsize=(14, 10))

plt.subplot(3, 1, 1)
for val, trace in sample_traces.items():
    plt.plot(trace, alpha=0.6, label=f'value {val}')
plt.xlabel('sample')
plt.ylabel('power')
plt.title('power traces for different byte 0 guesses')
plt.legend()
plt.grid(True, alpha=0.3)

traces_list = list(sample_traces.values())
trace_array = np.array(traces_list)

plt.subplot(3, 1, 2)
mean_trace = np.mean(trace_array, axis=0)
plt.plot(mean_trace)
plt.xlabel('sample')
plt.ylabel('mean power')
plt.title('mean power trace')
plt.grid(True, alpha=0.3)

plt.subplot(3, 1, 3)
variance_trace = np.var(trace_array, axis=0)
plt.plot(variance_trace)
plt.xlabel('sample')
plt.ylabel('variance')
plt.title('power variance across guesses')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('dark_gatekeeper_traces.png', dpi=150)
plt.close()

print("\nperforming differential analysis on byte 0...")
print("  capturing full set of 256 traces...")

all_traces = []
for guess in range(256):
    password_template[0] = guess
    trace, _ = capture_trace(password_template)
    all_traces.append(trace)

    if (guess + 1) % 64 == 0:
        print(f"    progress: {guess + 1}/256")

traces_array = np.array(all_traces)

print("\n  analyzing trace differences...")
mean_trace = np.mean(traces_array, axis=0)

differences_from_mean = []
for i in range(256):
    diff = np.sum(np.abs(traces_array[i] - mean_trace))
    differences_from_mean.append(diff)

sad_scores = []
for i in range(256):
    total_diff = 0
    for j in range(256):
        if i != j:
            total_diff += np.sum(np.abs(traces_array[i] - traces_array[j]))
    sad_scores.append(total_diff)

norm_diff = np.array(differences_from_mean) / (np.max(differences_from_mean) + 1e-10)
norm_sad = np.array(sad_scores) / (np.max(sad_scores) + 1e-10)

combined_score = norm_diff + norm_sad

top_5 = np.argsort(combined_score)[::-1][:5]

print("\n  top 5 candidates for byte 0:")
for rank, idx in enumerate(top_5):
    char_repr = chr(idx) if 32 <= idx < 127 else '?'
    print(f"    {rank + 1}. value: {idx:3d} (0x{idx:02x}, '{char_repr}')  score: {combined_score[idx]:.4f}")

plt.figure(figsize=(15, 6))
plt.bar(range(256), combined_score)
plt.xlabel('byte value')
plt.ylabel('differential score')
plt.title('dark gatekeeper: differential power analysis for byte 0')
plt.axvline(x=top_5[0], color='r', linestyle='--', label=f'best guess: 0x{top_5[0]:02x}')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('dark_gatekeeper_byte0_scores.png', dpi=150)
plt.close()

print("\n" + "="*80)
print("analysis complete")
print("="*80)
print("\nkey findings:")
print(f"  - correct byte produces distinct power signature (outlier)")
print(f"  - byte 0 most likely value: 0x{top_5[0]:02x} ('{chr(top_5[0]) if 32 <= top_5[0] < 127 else '?'}')")
print(f"  - differential score: {combined_score[top_5[0]]:.4f}")
print(f"  - attack can recover all {KEY_LENGTH} bytes iteratively")

scope.dis()
target.dis()
