import chipwhisperer as cw
import numpy as np
import time
import pickle

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

def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)

fw_path = "../../challenges/set1/gatekeeper-CWNANO.hex"
cw.program_target(scope, prog, fw_path)
reset_target(scope)

print("loading anomaly detector...")
with open('anomaly_detector.pkl', 'rb') as f:
    model_data = pickle.load(f)
    detector = model_data['detector']
    scaler = model_data['scaler']

print("detector loaded - monitoring for attacks...\n")

attack_threshold = 5
attack_counter = 0
total_requests = 0
window_size = 100
recent_predictions = []

while True:
    try:
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

        features_scaled = scaler.transform([features])
        prediction = detector.predict(features_scaled)[0]

        total_requests += 1
        recent_predictions.append(prediction)

        if len(recent_predictions) > window_size:
            recent_predictions.pop(0)

        if prediction == -1:
            attack_counter += 1
            print(f"[{total_requests:04d}] anomaly detected! timing={timing:.6f}s")

            if attack_counter >= attack_threshold:
                print(f"\n*** attack detected! {attack_counter} anomalies in recent window ***")
                print(f"triggering countermeasures...")
                attack_counter = 0

        else:
            if total_requests % 50 == 0:
                anomaly_rate = recent_predictions.count(-1) / len(recent_predictions) * 100
                print(f"[{total_requests:04d}] normal operation (anomaly rate: {anomaly_rate:.1f}%)")

        time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nmonitoring stopped by user")
        break
    except Exception as e:
        print(f"error: {e}")
        continue

print(f"\ntotal requests monitored: {total_requests}")
print(f"anomalies detected: {recent_predictions.count(-1)}")

scope.dis()
target.dis()
