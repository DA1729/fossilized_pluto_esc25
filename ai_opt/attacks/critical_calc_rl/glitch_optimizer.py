import chipwhisperer as cw
import numpy as np
import time
from collections import deque
import random

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

def reboot_flush():
    scope.io.nrst = False
    time.sleep(0.02)
    scope.io.nrst = "high_z"
    time.sleep(0.02)
    target.flush()

fw_path = "../../challenges/set1/criticalCalculation-CWNANO.hex"
cw.program_target(scope, prog, fw_path)
scope.io.clkout = 7.5e6

class glitch_env:
    def __init__(self):
        self.repeat_min = 1
        self.repeat_max = 20
        self.offset_min = 50
        self.offset_max = 200
        self.success_params = []
        self.history = deque(maxlen=100)

    def test_params(self, repeat, offset):
        scope.glitch.repeat = repeat
        scope.glitch.ext_offset = offset
        reboot_flush()
        target.flush()
        scope.arm()
        target.simpleserial_write("d", bytearray([]))
        ret = scope.capture()
        if ret:
            return 'reset', None
        val = target.simpleserial_read_witherrors('r', 26, glitch_timeout=10)
        if val['valid'] is False:
            reboot_flush()
            return 'reset', None
        response_str = val['payload'].decode('ascii', errors='ignore')
        if "DIAGNOSTIC_OK" not in response_str:
            return 'success', response_str
        return 'normal', None

    def get_reward(self, result):
        if result == 'success':
            return 100.0
        elif result == 'normal':
            return -1.0
        else:
            return -5.0

    def get_neighbors(self, repeat, offset, radius=2):
        neighbors = []
        for dr in range(-radius, radius + 1):
            for do in range(-radius, radius + 1):
                new_repeat = max(self.repeat_min, min(self.repeat_max, repeat + dr))
                new_offset = max(self.offset_min, min(self.offset_max, offset + do))
                neighbors.append((new_repeat, new_offset))
        return neighbors

class q_learner:
    def __init__(self):
        self.q_table = {}
        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 0.3
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.05

    def get_q_value(self, state):
        return self.q_table.get(state, 0.0)

    def update(self, state, reward, next_state):
        current_q = self.get_q_value(state)
        max_next_q = self.get_q_value(next_state)
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state] = new_q

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

print("starting reinforcement learning glitch optimization...")
env = glitch_env()
agent = q_learner()

n_episodes = 200
best_params = None
best_flag = None


for episode in range(n_episodes):
    if episode % 20 == 0:
        print(f"episode {episode}/{n_episodes}, epsilon: {agent.epsilon:.3f}")

    if random.random() < agent.epsilon:
        repeat = random.randint(env.repeat_min, env.repeat_max)
        offset = random.randint(env.offset_min, env.offset_max)
    else:
        if len(agent.q_table) > 0:
            state = max(agent.q_table.items(), key=lambda x: x[1])[0]
            repeat, offset = state
        else:
            repeat = random.randint(env.repeat_min, env.repeat_max)
            offset = random.randint(env.offset_min, env.offset_max)

    state = (repeat, offset)
    result, flag = env.test_params(repeat, offset)
    reward = env.get_reward(result)

    if result == 'success':
        print(f"\nflag found at episode {episode}")
        print(f"params: repeat={repeat}, offset={offset}")
        print(f"flag: {flag}")
        best_params = (repeat, offset)
        best_flag = flag
        break

    neighbors = env.get_neighbors(repeat, offset)
    next_state = random.choice(neighbors)
    agent.update(state, reward, next_state)
    agent.decay_epsilon()


print(f"\nrl optimization complete")
print(f"episodes: {episode + 1}")

if best_params:
    print(f"best params: repeat={best_params[0]}, offset={best_params[1]}")
    print(f"flag: {best_flag}")
else:
    print("no successful glitch found")
    top_states = sorted(agent.q_table.items(), key=lambda x: x[1], reverse=True)[:5]
    print("top 5 q-values:")
    for state, q_val in top_states:
        print(f"  repeat={state[0]}, offset={state[1]}, q={q_val:.2f}")
