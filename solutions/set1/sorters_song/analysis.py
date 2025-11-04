import chipwhisperer as cw
import numpy as np
import matplotlib.pyplot as plt
from tqdm import trange
import time

SCOPETYPE = 'CWNANO'
PLATFORM = 'CWNANO'
FIRMWARE = '../../../challenges/set1/sortersSong-CWNANO.hex'
N_TRACES = 100
SAMPLE_SIZE = 700

def setup():
    try:
        scope = cw.scope()
        if not scope.connectStatus:
            scope.con()
    except Exception:
        scope = cw.scope()

    target_type = cw.targets.SimpleSerial
    try:
        target = cw.target(scope, target_type)
    except Exception:
        scope = cw.scope()
        target = cw.target(scope, target_type)

    return scope, target

def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)

def program_target(scope):
    prog = cw.programmers.STM32FProgrammer
    scope.default_setup()
    cw.program_target(scope, prog, FIRMWARE)
    reset_target(scope)

def capture_traces_for_byte_analysis(scope, target, byte_position=0):
    all_traces = []

    print(f'\ncapturing traces for byte {byte_position} analysis...')

    for guess in range(256):
        avg_trace = np.zeros(SAMPLE_SIZE)
        payload = bytearray([1, guess, 0, byte_position])

        for _ in trange(N_TRACES, desc=f'guess {guess}', leave=False):
            target.simpleserial_write('p', payload)
            target.simpleserial_read('r', 2)

            scope.arm()
            target.simpleserial_write('c', b'')
            ret = scope.capture()

            if ret:
                continue

            target.simpleserial_read('r', 1)
            trace = scope.get_last_trace()

            # Skip first 10 traces for stabilization
            if _ >= 10:
                avg_trace = np.add(avg_trace, trace)

        avg_trace /= (N_TRACES - 10)
        all_traces.append(np.abs(avg_trace))

    return all_traces

def analyze_with_sad_metric(all_traces):
    sad_values = []
    ref_trace = all_traces[0]

    print('evaluating SAD (Sum of Absolute Differences) metric...')

    for trace in all_traces:
        sad = np.sum(np.abs(trace - ref_trace))
        sad_values.append(sad)

    return sad_values

def visualize_analysis(all_traces, sad_values, byte_position=0):
    # Plot trace overlay
    plt.figure(figsize=(12, 6))
    for trace in all_traces:
        plt.plot(trace, alpha=0.05, color='blue')
    plt.plot(all_traces[0], alpha=0.9, color='red', label='Reference trace')
    plt.title(f'Power Trace Overlay - Byte {byte_position}')
    plt.xlabel('Sample Point')
    plt.ylabel('Power')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'byte{byte_position}_traces_overlay.png')
    plt.close()

    # Plot SAD metric
    plt.figure(figsize=(12, 6))
    plt.plot(range(256), sad_values)
    plt.title(f'SAD Metric vs Guess Value - Byte {byte_position}')
    plt.xlabel('Guess Value')
    plt.ylabel('SAD')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'byte{byte_position}_sad_metric.png')
    plt.close()

    # Find peaks in SAD metric
    peaks_idx = np.argsort(sad_values)[-5:][::-1]
    print(f'\ntop 5 candidates based on SAD metric:')
    for idx in peaks_idx:
        print(f'  guess {idx}: SAD = {sad_values[idx]:.2f}')

def main():
    print('=== power analysis attack demonstration ===')
    print('\nvulnerability: data-dependent power consumption in sorting algorithm')
    print('attack vector: binary search using power analysis (SAD metric)\n')

    scope, target = setup()
    scope.adc.samples = SAMPLE_SIZE

    print('programming target...')
    program_target(scope)
    print('target running\n')

    # Initialize target
    target.simpleserial_write('x', b'')
    target.simpleserial_read('r', 1)

    # Analyze first byte as demonstration
    byte_pos = 0
    all_traces = capture_traces_for_byte_analysis(scope, target, byte_pos)
    sad_values = analyze_with_sad_metric(all_traces)

    print('\ngenerating visualization plots...')
    visualize_analysis(all_traces, sad_values, byte_pos)

    print('\n=== analysis complete ===')
    print(f'generated: byte{byte_pos}_traces_overlay.png')
    print(f'generated: byte{byte_pos}_sad_metric.png')
    print('\nthe SAD metric reveals power consumption differences based on')
    print('comparison operations in the sorting algorithm, enabling binary')
    print('search recovery of secret values.')

    scope.dis()
    target.dis()

if __name__ == '__main__':
    main()
