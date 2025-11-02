import chipwhisperer as cw
import numpy as np
import time
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
from tqdm import trange

scopetype = 'CWNANO'
platform = 'CWNANO'

n_normal_samples = 500
n_attack_samples = 500

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
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)

fw_path = "../../challenges/set1/gatekeeper-CWNANO.hex"
cw.program_target(scope, prog, fw_path)
reset_target(scope)

print("collecting normal operation traces...")
normal_features = []

for i in trange(n_normal_samples, desc="normal ops"):
    password = bytearray([ord('a')] * 13)
    start = time.perf_counter()
    target.simpleserial_write('a', password)
    response = target.simpleserial_read('r', 1)
    end = time.perf_counter()

    timing = end - start

    features = [
        timing,
        len(password),
        password[0],
        1 if response else 0
    ]
    normal_features.append(features)

    time.sleep(0.01)

print("simulating attack pattern traces...")
attack_features = []

for i in trange(n_attack_samples, desc="attack patterns"):
    for pos in range(13):
        for char_idx in range(10):
            password = bytearray([ord('a')] * 13)
            password[pos] = ord('a') + char_idx

            start = time.perf_counter()
            target.simpleserial_write('a', password)
            response = target.simpleserial_read('r', 1)
            end = time.perf_counter()

            timing = end - start

            features = [
                timing,
                len(password),
                password[pos],
                pos
            ]
            attack_features.append(features)

            if len(attack_features) >= n_attack_samples:
                break
        if len(attack_features) >= n_attack_samples:
            break

normal_features = np.array(normal_features)
attack_features = np.array(attack_features)

print(f"normal features shape: {normal_features.shape}")
print(f"attack features shape: {attack_features.shape}")

x = np.vstack([normal_features, attack_features])
y = np.hstack([np.zeros(len(normal_features)), np.ones(len(attack_features))])

scaler = StandardScaler()
x_scaled = scaler.fit_transform(x)

print("training isolation forest...")
train_start = time.time()
detector = IsolationForest(
    contamination=0.1,
    random_state=42,
    n_estimators=100
)
detector.fit(x_scaled[y == 0])
train_end = time.time()

print(f"training time: {train_end - train_start:.2f}s")

predictions = detector.predict(x_scaled)
predictions = (predictions == -1).astype(int)

normal_pred = predictions[y == 0]
attack_pred = predictions[y == 1]

true_negatives = np.sum(normal_pred == 0)
false_positives = np.sum(normal_pred == 1)
true_positives = np.sum(attack_pred == 1)
false_negatives = np.sum(attack_pred == 0)

print(f"\nperformance metrics:")
print(f"true negatives (normal correctly identified): {true_negatives}/{len(normal_pred)}")
print(f"false positives (normal flagged as attack): {false_positives}/{len(normal_pred)}")
print(f"true positives (attack correctly detected): {true_positives}/{len(attack_pred)}")
print(f"false negatives (attack missed): {false_negatives}/{len(attack_pred)}")

detection_rate = true_positives / len(attack_pred) * 100
false_alarm_rate = false_positives / len(normal_pred) * 100

print(f"\ndetection rate: {detection_rate:.2f}%")
print(f"false alarm rate: {false_alarm_rate:.2f}%")

with open('anomaly_detector.pkl', 'wb') as f:
    pickle.dump({
        'detector': detector,
        'scaler': scaler
    }, f)

print("\nsaved model to anomaly_detector.pkl")

scope.dis()
target.dis()
