import chipwhisperer as cw
import numpy as np
import time
from tqdm import trange
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import pickle

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

fw_path = "../../challenges/set2/hyperspaceJumpDrive-CWNANO.hex"
cw.program_target(scope, prog, fw_path)

def hamming_weight(n):
    return bin(n & 0xff).count('1')

def capture_trace_with_mask(mask_value):
    scope.arm()
    target.simpleserial_write('p', bytearray([mask_value]))
    scope.capture()
    _ = target.simpleserial_read('r', 1, timeout=100)
    return scope.get_last_trace()

print("capturing 256 traces for training...")
traces = []
masks = []
for mask in trange(256, desc="capturing"):
    trace = capture_trace_with_mask(mask)
    traces.append(trace)
    masks.append(mask)

traces_array = np.array(traces)
masks_array = np.array(masks)

print(f"traces shape: {traces_array.shape}")

trace_variance = np.var(traces_array, axis=0)
threshold = np.mean(trace_variance) + 0.5 * np.std(trace_variance)
high_var_indices = np.where(trace_variance > threshold)[0]

print(f"high variance samples: {len(high_var_indices)}")

if len(high_var_indices) > 500:
    high_var_indices = high_var_indices[::len(high_var_indices)//500]
    print(f"reduced to: {len(high_var_indices)}")

x_features = traces_array[:, high_var_indices]

print("building ml models for each byte position...")
models = []

for byte_idx in range(12):
    print(f"\ntraining model for byte {byte_idx}...")

    y_labels = []
    for mask in masks_array:
        for secret_guess in range(256):
            hw = hamming_weight(mask ^ secret_guess)
            y_labels.append(hw)

    x_repeated = np.repeat(x_features, 256, axis=0)
    y_array = np.array(y_labels)

    x_train, x_test, y_train, y_test = train_test_split(
        x_repeated, y_array, test_size=0.2, random_state=42
    )

    train_start = time.time()
    model = GradientBoostingRegressor(n_estimators=50, max_depth=5, random_state=42)
    model.fit(x_train, y_train)
    train_end = time.time()

    score = model.score(x_test, y_test)
    print(f"byte {byte_idx} - r2 score: {score:.4f}, time: {train_end - train_start:.2f}s")

    models.append(model)

with open('cpa_predictor_models.pkl', 'wb') as f:
    pickle.dump({
        'models': models,
        'high_var_indices': high_var_indices
    }, f)

print("\nsaved models to cpa_predictor_models.pkl")

scope.dis()
target.dis()
