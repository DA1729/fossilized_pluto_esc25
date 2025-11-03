#!/usr/bin/env python3

import numpy as np
import os
from trace_analyzer import analyze_and_suggest
from attack_generator import generate_complete_attack

def simulate_timing_traces():
    n_traces = 50
    n_samples = 1000

    base_trace = np.random.normal(0.5, 0.05, n_samples)

    traces = []
    for i in range(n_traces):
        trace = base_trace.copy()

        if i < 25:
            trace[400:450] += np.random.normal(0.2, 0.02, 50)
        else:
            trace[400:450] += np.random.normal(0.1, 0.02, 50)

        trace[300:320] += np.random.normal(0.15, 0.03, 20)
        trace[600:650] += np.random.normal(0.12, 0.02, 50)

        traces.append(trace)

    return np.array(traces)

def simulate_power_analysis_traces():
    n_traces = 100
    n_samples = 5000

    base_trace = np.random.normal(0.3, 0.02, n_samples)

    traces = []
    for i in range(n_traces):
        trace = base_trace.copy()

        secret_byte = 0x42
        input_byte = i % 256
        hw = bin(secret_byte ^ input_byte).count('1')

        trace[1000:1020] += hw * 0.05 + np.random.normal(0, 0.01, 20)
        trace[2000:2030] += hw * 0.04 + np.random.normal(0, 0.01, 30)
        trace[3500:3550] += hw * 0.06 + np.random.normal(0, 0.01, 50)

        traces.append(trace)

    return np.array(traces)

def demo_timing_attack():
    print("\n" + "=" * 60)
    print("demo: timing side-channel detection")
    print("=" * 60)

    traces = simulate_timing_traces()
    print(f"\ngenerated {traces.shape[0]} simulated timing traces")

    result = analyze_and_suggest(
        traces,
        challenge_name="timing_password_check",
        api_key=os.environ.get('ANTHROPIC_API_KEY')
    )

    return result

def demo_power_analysis():
    print("\n" + "=" * 60)
    print("demo: power analysis detection")
    print("=" * 60)

    traces = simulate_power_analysis_traces()
    print(f"\ngenerated {traces.shape[0]} simulated power traces")

    result = analyze_and_suggest(
        traces,
        challenge_name="aes_encryption",
        api_key=os.environ.get('ANTHROPIC_API_KEY')
    )

    return result

def demo_code_generation():
    print("\n" + "=" * 60)
    print("demo: attack code generation")
    print("=" * 60)

    traces = simulate_timing_traces()

    result = analyze_and_suggest(
        traces,
        challenge_name="password_timing",
        api_key=os.environ.get('ANTHROPIC_API_KEY')
    )

    if result and 'llm_response' in result:
        code = generate_complete_attack(
            result['trace_summary'],
            result['llm_response'],
            "password_timing",
            "firmware/password-CWNANO.hex",
            api_key=os.environ.get('ANTHROPIC_API_KEY')
        )

        print("\ngenerated attack code (first 500 chars):")
        print(code[:500] + "...")

def main():
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("error: ANTHROPIC_API_KEY not set")
        print("export ANTHROPIC_API_KEY='your-key-here'")
        return

    print("llm attack assistant - interactive demo")

    demo_timing_attack()

    print("\n" + "=" * 60)
    input("press enter to continue to power analysis demo...")

    demo_power_analysis()

    print("\n" + "=" * 60)
    input("press enter to continue to code generation demo...")

    demo_code_generation()

    print("\n" + "=" * 60)
    print("demo complete")

if __name__ == '__main__':
    main()
