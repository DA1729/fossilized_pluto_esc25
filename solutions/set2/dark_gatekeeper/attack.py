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

fw_path = "../../../challenges/set2/darkGatekeeper-CWNANO.hex"
cw.program_target(scope, prog, fw_path)

key_length = 12
response_length = 18

def capture_trace(password):
    scope.arm()
    target.simpleserial_write('a', bytearray(password))
    ret = scope.capture()
    trace = scope.get_last_trace()
    try:
        resp = target.simpleserial_read('r', response_length, timeout=100)
    except:
        resp = None
    return trace, resp

def attack_byte_position(known_bytes, position):
    password = list(known_bytes) + [0] * (key_length - len(known_bytes))
    traces_for_guesses = []
    guess_values = []
    for guess in range(256):
        password[position] = guess
        trace, resp = capture_trace(password)
        traces_for_guesses.append(trace)
        guess_values.append(guess)
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
    best_guess = guess_values[top_indices[0]]
    return best_guess

recovered_password = []

for byte_pos in range(key_length):
    best_byte = attack_byte_position(recovered_password, byte_pos)
    recovered_password.append(best_byte)

print(f'password: {recovered_password}')
print(f'hex: {" ".join([f"{b:02x}" for b in recovered_password])}')

_, response = capture_trace(recovered_password)

if response:
    result_str = response.decode('utf-8', errors='replace').strip()
    if "access denied" not in result_str.lower():
        print(f'flag: {result_str}')

total_queries = 256 * key_length
print(f'queries: {total_queries}')

scope.dis()
target.dis()
