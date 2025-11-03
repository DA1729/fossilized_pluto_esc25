timing_attack_template = """
import chipwhisperer as cw
import time
import statistics

charset = 'abcdefghijklmnopqrstuvwxyz0123456789{}'
pwd_len = 13
samples = 10
firmware = 'path/to/firmware.hex'

def setup():
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    time.sleep(0.05)
    scope.default_setup()
    prog = cw.programmers.STM32FProgrammer
    cw.program_target(scope, prog, firmware)
    time.sleep(0.2)
    return scope, target

def measure_time(target, password):
    password_bytes = password.encode('ascii')
    start = time.perf_counter()
    target.simpleserial_write('a', password_bytes)
    response = target.simpleserial_read('r', 1)
    end = time.perf_counter()
    return end - start

def guess_character(target, current_password, position):
    timings = {}
    for char in charset:
        pwd_try = (current_password + char).ljust(pwd_len, 'a')
        char_samples = []
        for _ in range(samples):
            t = measure_time(target, pwd_try)
            char_samples.append(t)
            time.sleep(0.01)
        median_time = statistics.median(char_samples)
        timings[char] = median_time
    best_char = max(timings, key=timings.get)
    return best_char
"""

power_analysis_template = """
import chipwhisperer as cw
import numpy as np
import time

firmware = 'path/to/firmware.hex'
sample_size = 700

def setup():
    scope = cw.scope()
    if not scope.connectStatus:
        scope.con()
    prog = cw.programmers.STM32FProgrammer
    scope.default_setup()
    target = cw.target(scope, cw.targets.SimpleSerial)
    cw.program_target(scope, prog, firmware)
    time.sleep(0.2)
    return scope, target

def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)

def capture_trace(target, scope, payload):
    target.simpleserial_write('p', payload)
    target.simpleserial_read('r', 2)
    scope.arm()
    target.simpleserial_write('c', b'')
    target.simpleserial_read('r', 1)
    if scope.capture():
        return None
    return scope.get_last_trace()

def analyze_sad(trace_ref, trace_test):
    return int(np.sum(np.abs(trace_test - trace_ref)))
"""

glitch_attack_template = """
import chipwhisperer as cw
import time

firmware = 'path/to/firmware.hex'

def setup():
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    scope.default_setup()
    prog = cw.programmers.STM32FProgrammer
    cw.program_target(scope, prog, firmware)

    scope.glitch.clk_src = 'clkgen'
    scope.glitch.output = 'glitch_only'
    scope.glitch.trigger_src = 'ext_single'

    scope.io.glitch_lp = True
    scope.io.glitch_hp = True

    time.sleep(0.2)
    return scope, target

def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.1)

def glitch_attempt(scope, target, repeat, ext_offset):
    scope.glitch.repeat = repeat
    scope.glitch.ext_offset = ext_offset

    reset_target(scope)

    scope.arm()
    target.simpleserial_write('a', b'')

    response = target.simpleserial_read('r', 100, timeout=1)

    return response
"""

cpa_attack_template = """
import chipwhisperer as cw
import numpy as np
import time

firmware = 'path/to/firmware.hex'
n_traces = 256

def setup():
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    scope.default_setup()
    prog = cw.programmers.STM32FProgrammer
    cw.program_target(scope, prog, firmware)

    scope.adc.samples = 5000
    scope.adc.offset = 0
    scope.adc.basic_mode = "rising_edge"
    scope.clock.clkgen_freq = 7370000
    scope.clock.adc_src = "clkgen_x4"
    scope.trigger.triggers = "tio4"
    scope.io.tio1 = "serial_rx"
    scope.io.tio2 = "serial_tx"
    scope.io.hs2 = "glitch"

    time.sleep(0.2)
    return scope, target

def capture_traces(scope, target, n):
    traces = []
    plaintexts = []

    for i in range(n):
        plaintext = i & 0xff
        plaintexts.append(plaintext)

        scope.arm()
        target.simpleserial_write('p', bytearray([plaintext]))

        if not scope.capture():
            trace = scope.get_last_trace()
            traces.append(trace)

        time.sleep(0.01)

    return np.array(traces), np.array(plaintexts)

def hamming_weight(n):
    return bin(n).count('1')

def cpa_attack(traces, plaintexts, byte_position):
    n_samples = traces.shape[1]
    correlations = np.zeros(256)

    for guess in range(256):
        hypothetical_hw = np.array([hamming_weight(p ^ guess) for p in plaintexts])

        best_corr = 0
        for sample_idx in range(n_samples):
            sample_values = traces[:, sample_idx]
            corr = np.corrcoef(hypothetical_hw, sample_values)[0, 1]
            if abs(corr) > abs(best_corr):
                best_corr = corr

        correlations[guess] = abs(best_corr)

    return np.argmax(correlations), np.max(correlations)
"""

api_usage_guide = """
chipwhisperer nano api reference for llm code generation:

setup and connection:
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    scope.default_setup()
    prog = cw.programmers.STM32FProgrammer
    cw.program_target(scope, prog, firmware_path)

simpleserial communication:
    target.simpleserial_write(command, data)
    response = target.simpleserial_read(command, length, timeout=1)

trace capture:
    scope.arm()
    scope.capture()
    trace = scope.get_last_trace()

glitch configuration:
    scope.glitch.clk_src = 'clkgen'
    scope.glitch.output = 'glitch_only'
    scope.glitch.trigger_src = 'ext_single'
    scope.glitch.repeat = value
    scope.glitch.ext_offset = value
    scope.io.glitch_lp = True
    scope.io.glitch_hp = True

adc configuration:
    scope.adc.samples = 5000
    scope.adc.offset = 0
    scope.adc.basic_mode = "rising_edge"

target reset:
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)

cleanup:
    scope.dis()
    target.dis()
"""
