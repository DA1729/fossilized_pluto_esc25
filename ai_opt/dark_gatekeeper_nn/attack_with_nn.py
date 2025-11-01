import chipwhisperer as cw
import numpy as np
import time
import pickle
import tensorflow as tf
from tensorflow import keras

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

fw_path = "../../challenges/set2/darkGatekeeper-CWNANO.hex"
cw.program_target(scope, prog, fw_path)

key_length = 12
response_length = 18

print("loading neural network model...")
model = keras.models.load_model('byte_predictor_model.h5')
with open('scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

print("model loaded")

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

def predict_byte_nn(known_bytes, position, n_predictions=5):
    password = list(known_bytes) + [0] * (key_length - len(known_bytes))
    predictions = []
    for _ in range(n_predictions):
        trace, _ = capture_trace(password)
        trace_scaled = scaler.transform([trace])
        pred_probs = model.predict(trace_scaled, verbose=0)[0]
        predictions.append(pred_probs)
    avg_probs = np.mean(predictions, axis=0)
    top_candidates = np.argsort(avg_probs)[::-1][:5]
    return top_candidates

attack_start = time.time()
recovered_password = []

for byte_pos in range(key_length):
    candidates = predict_byte_nn(recovered_password, byte_pos, n_predictions=5)
    best_byte = candidates[0]
    recovered_password.append(best_byte)
    print(f"position {byte_pos}: {best_byte} (candidates: {candidates[:3]})")

print(f"password: {recovered_password}")
print(f"hex: {' '.join([f'{b:02x}' for b in recovered_password])}")

_, response = capture_trace(recovered_password)

if response:
    result_str = response.decode('utf-8', errors='replace').strip()
    if "access denied" not in result_str.lower():
        print(f"flag: {result_str}")

attack_end = time.time()
total_time = attack_end - attack_start
print(f"time: {total_time:.2f}s")
total_queries = key_length * 5
print(f"queries: {total_queries}")

scope.dis()
target.dis()
