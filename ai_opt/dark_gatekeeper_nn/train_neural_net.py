import chipwhisperer as cw
import numpy as np
import time
from tqdm import trange
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
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

fw_path = "../../challenges/set2/darkGatekeeper-CWNANO.hex"
cw.program_target(scope, prog, fw_path)

key_length = 12
response_length = 18
byte_position = 0
n_samples_per_value = 3

print(f"collecting training data for byte position {byte_position}")

traces = []
labels = []

password = [0] * key_length

for guess in trange(256, desc="capturing traces"):
    password[byte_position] = guess
    for _ in range(n_samples_per_value):
        scope.arm()
        target.simpleserial_write('a', bytearray(password))
        ret = scope.capture()
        trace = scope.get_last_trace()
        try:
            resp = target.simpleserial_read('r', response_length, timeout=100)
        except:
            resp = None
        traces.append(trace)
        labels.append(guess)

traces = np.array(traces)
labels = np.array(labels)

print(f"dataset shape: {traces.shape}")
print(f"labels shape: {labels.shape}")

x_train, x_test, y_train, y_test = train_test_split(traces, labels, test_size=0.2, random_state=42)

scaler = StandardScaler()
x_train = scaler.fit_transform(x_train)
x_test = scaler.transform(x_test)

print(f"training set: {x_train.shape}")
print(f"test set: {x_test.shape}")

print("building neural network...")
model = keras.Sequential([
    keras.layers.Dense(128, activation='relu', input_shape=(traces.shape[1],)),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(64, activation='relu'),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dense(256, activation='softmax')
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

print("training neural network...")
train_start = time.time()
history = model.fit(x_train, y_train,
                    epochs=50,
                    batch_size=32,
                    validation_split=0.2,
                    verbose=0)
train_end = time.time()

print(f"training time: {train_end - train_start:.2f}s")

test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
print(f"test accuracy: {test_acc*100:.2f}%")

model.save('byte_predictor_model.h5')
with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("saved model to byte_predictor_model.h5")
print("saved scaler to scaler.pkl")

y_pred = np.argmax(model.predict(x_test, verbose=0), axis=1)
correct_predictions = np.sum(y_pred == y_test)
print(f"correct predictions: {correct_predictions}/{len(y_test)}")

top_5_acc = tf.keras.metrics.sparse_top_k_categorical_accuracy(
    y_test, model.predict(x_test, verbose=0), k=5
)
print(f"top-5 accuracy: {np.mean(top_5_acc)*100:.2f}%")

scope.dis()
target.dis()
