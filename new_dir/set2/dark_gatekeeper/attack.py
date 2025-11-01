import chipwhisperer as cw
import numpy as np
import time

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
print("password bypass - correlation power analysis (cpa)")
print("="*80)

KEY_LENGTH = 12
RESPONSE_LENGTH = 18

def capture_trace(password):
    scope.arm()
    target.simpleserial_write('a', bytearray(password))
    ret = scope.capture()
    trace = scope.get_last_trace()

    try:
        resp = target.simpleserial_read('r', RESPONSE_LENGTH, timeout=100)
    except:
        resp = None

    return trace, resp

def attack_byte_position(known_bytes, position):
    password = list(known_bytes) + [0] * (KEY_LENGTH - len(known_bytes))

    traces_for_guesses = []
    guess_values = []

    for guess in range(256):
        password[position] = guess
        trace, resp = capture_trace(password)
        traces_for_guesses.append(trace)
        guess_values.append(guess)

        if (guess + 1) % 64 == 0:
            print(f"    progress: {guess + 1}/256")

    traces_array = np.array(traces_for_guesses)

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

    top_indices = np.argsort(combined_score)[::-1][:5]

    print(f"\n  top 5 candidates:")
    for rank, idx in enumerate(top_indices):
        byte_val = guess_values[idx]
        char_repr = chr(byte_val) if 32 <= byte_val < 127 else '?'
        print(f"    {rank + 1}. value: {byte_val:3d} (0x{byte_val:02x}, '{char_repr}')  score: {combined_score[idx]:.4f}")

    best_guess = guess_values[top_indices[0]]
    return best_guess

print("\nstarting byte-by-byte cpa attack...")
print("-" * 80)

recovered_password = []

for byte_pos in range(KEY_LENGTH):
    print(f"\nattacking byte position {byte_pos}...")
    print(f"  capturing traces for all 256 values...")
    best_byte = attack_byte_position(recovered_password, byte_pos)
    recovered_password.append(best_byte)

    password_str = ''
    for b in recovered_password:
        if 32 <= b < 127:
            password_str += chr(b)
        else:
            password_str += f'\\x{b:02x}'

    print(f"\n  recovered so far: {recovered_password}")
    print(f"  as string: {password_str}")
    print(f"  as hex: {' '.join([f'{b:02x}' for b in recovered_password])}")

print("\n" + "="*80)
print("verifying recovered password...")
print("-" * 80)

final_password_str = ''.join([chr(b) if 32 <= b < 127 else f'\\x{b:02x}' for b in recovered_password])
print(f"\nrecovered password: {recovered_password}")
print(f"as string: {final_password_str}")
print(f"as hex: {' '.join([f'{b:02x}' for b in recovered_password])}")

_, response = capture_trace(recovered_password)

if response:
    result_str = response.decode('utf-8', errors='replace').strip()
    print(f"\nserver response: {result_str}")

    if "access denied" not in result_str.lower():
        print(f"\n{'='*80}")
        print(f"success! flag: {result_str}")
        print(f"{'='*80}")
    else:
        print(f"\n{'='*80}")
        print(f"failed - password incorrect")
        print(f"{'='*80}")
else:
    print("\nno response received from target")

print(f"\ntotal password attempts: {256 * KEY_LENGTH}")

scope.dis()
target.dis()
print("\nattack complete!")
