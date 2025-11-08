import chipwhisperer as cw
import numpy as np
import time
import pickle
from tqdm import trange

scopetype = 'CWNANO'
platform = 'CWNANO'

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
scope.adc.samples = 2000

def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)

fw_path = "chaos-CWNANO.hex"
cw.program_target(scope, prog, fw_path)
reset_target(scope)

print("loading ml classifier...")
with open('oracle_classifier.pkl', 'rb') as f:
    clf = pickle.load(f)

print("classifier loaded")

def capture_trace(guess_val, pos):
    target.simpleserial_write('x', b'')
    target.simpleserial_read('r', 1)
    scope.arm()
    payload = bytearray([3, guess_val & 0xff, (guess_val >> 8) & 0xff, pos])
    target.simpleserial_write('p', payload)
    target.simpleserial_read('r', 1)
    if ret := scope.capture():
        return None
    return scope.get_last_trace()

def ml_oracle(guess_val, pos, n_votes=5):
    votes = []
    for _ in range(n_votes):
        trace = capture_trace(guess_val, pos)
        if trace is None:
            continue
        prediction = clf.predict([trace])[0]
        votes.append(prediction)
    if len(votes) == 0:
        return None
    return np.mean(votes) < 0.5

def recover_byte_ml(pos):
    search_low = 0
    search_high = 65535
    secret_val = 0
    pbar = trange(16, desc=f"pos={pos}")
    for iteration in pbar:
        mid = (search_low + search_high) // 2
        is_short_path = ml_oracle(mid, pos, n_votes=5)
        if is_short_path is None:
            continue
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
    value = recover_byte_ml(pos)
    recovered_array.append(value)
    print(f"position {pos}: {value}")

print(f"array: {recovered_array}")

leaked_array = np.array(recovered_array, dtype=np.uint16)
sorted_array = np.sort(leaked_array)
payload = bytearray(30)
for i, val in enumerate(sorted_array):
    payload[i*2]   = val & 0xff
    payload[i*2+1] = (val >> 8) & 0xff

print(f"sorted: {list(sorted_array)}")

flag_len = 20
target.simpleserial_write('a', payload)
resp = target.simpleserial_read('r', flag_len)

if resp:
    try:
        flag_str = resp.decode('utf-8').strip()
        print(f"flag: {flag_str}")
    except UnicodeDecodeError:
        print(f"raw: {resp}")

total_queries = 15 * 16 * 5
print(f"queries: {total_queries}")

scope.dis()
target.dis()
