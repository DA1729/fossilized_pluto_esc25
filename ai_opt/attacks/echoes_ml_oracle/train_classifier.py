import chipwhisperer as cw
import numpy as np
import time
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
from tqdm import trange

scopetype = 'CWNANO'
platform = 'CWNANO'

n_samples_per_class = 500
position_to_train = 0

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

print(f"collecting training data for position {position_to_train}")

traces_short = []
traces_long = []

print("capturing short path traces (guess <= secret)...")
for i in trange(n_samples_per_class, desc="short path"):
    target.simpleserial_write('x', b'')
    target.simpleserial_read('r', 1)
    scope.arm()
    payload = bytearray([3, 0, 0, position_to_train])
    target.simpleserial_write('p', payload)
    target.simpleserial_read('r', 1)
    if ret := scope.capture():
        continue
    trace = scope.get_last_trace()
    traces_short.append(trace)

print("capturing long path traces (guess > secret)...")
for i in trange(n_samples_per_class, desc="long path"):
    target.simpleserial_write('x', b'')
    target.simpleserial_read('r', 1)
    scope.arm()
    payload = bytearray([3, 255, 255, position_to_train])
    target.simpleserial_write('p', payload)
    target.simpleserial_read('r', 1)
    if ret := scope.capture():
        continue
    trace = scope.get_last_trace()
    traces_long.append(trace)

traces_short = np.array(traces_short)
traces_long = np.array(traces_long)

print(f"collected {len(traces_short)} short path traces")
print(f"collected {len(traces_long)} long path traces")

x_short = traces_short
y_short = np.zeros(len(traces_short))
x_long = traces_long
y_long = np.ones(len(traces_long))

x = np.vstack([x_short, x_long])
y = np.hstack([y_short, y_long])

print(f"dataset shape: {x.shape}")
print(f"labels shape: {y.shape}")

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42, stratify=y)

print(f"training set: {x_train.shape}")
print(f"test set: {x_test.shape}")

print("training random forest classifier...")
clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
clf.fit(x_train, y_train)


y_pred = clf.predict(x_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"test accuracy: {accuracy*100:.2f}%")
print("\nclassification report:")
print(classification_report(y_test, y_pred, target_names=['short path', 'long path']))

with open('oracle_classifier.pkl', 'wb') as f:
    pickle.dump(clf, f)

print("saved model to oracle_classifier.pkl")

scope.dis()
target.dis()
