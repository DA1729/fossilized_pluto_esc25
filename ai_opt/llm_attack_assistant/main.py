#!/usr/bin/env python3

import sys
import os
import numpy as np
import argparse
from trace_analyzer import analyze_and_suggest
from attack_generator import generate_complete_attack, save_attack_script
from iterative_refiner import refine_iteratively

def load_traces(trace_file):
    try:
        if trace_file.endswith('.npy'):
            traces = np.load(trace_file)
        elif trace_file.endswith('.npz'):
            data = np.load(trace_file)
            traces = data['traces'] if 'traces' in data else data[data.files[0]]
        else:
            traces = np.loadtxt(trace_file)

        return traces

    except Exception as e:
        print(f"failed to load traces: {str(e)}")
        return None

def run_full_pipeline(trace_file, challenge_name, firmware_path, output_script, refine=True):
    print("=" * 60)
    print("llm-powered attack discovery assistant")
    print("=" * 60)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("\nerror: ANTHROPIC_API_KEY environment variable not set")
        print("export ANTHROPIC_API_KEY='your-key-here'")
        return False

    print(f"\nloading traces from {trace_file}...")
    traces = load_traces(trace_file)

    if traces is None:
        return False

    print(f"loaded {traces.shape[0]} traces with {traces.shape[1]} samples each")

    analysis_result = analyze_and_suggest(traces, challenge_name, api_key)

    trace_summary = analysis_result['trace_summary']
    llm_response = analysis_result['llm_response']

    attack_code = generate_complete_attack(
        trace_summary,
        llm_response,
        challenge_name,
        firmware_path,
        api_key
    )

    if "failed" in attack_code.lower() or "error" in attack_code.lower():
        print(f"\ncode generation failed: {attack_code}")
        return False

    save_attack_script(attack_code, output_script)

    if refine:
        print("\n" + "=" * 60)
        print("attempting iterative refinement")
        print("=" * 60)

        final_code, success, result = refine_iteratively(
            attack_code,
            output_script,
            max_iterations=3,
            api_key=api_key
        )

        if success:
            save_attack_script(final_code, output_script)
            print(f"\nfinal attack script saved to {output_script}")
            return True
        else:
            print("\nrefinement did not achieve success")
            print("manual intervention may be required")
            return False
    else:
        print(f"\nattack script generated (refinement skipped)")
        print(f"run manually: python {output_script}")
        return True

def main():
    parser = argparse.ArgumentParser(
        description='llm-powered attack discovery and generation'
    )

    parser.add_argument(
        'trace_file',
        help='path to power traces (.npy, .npz, or .txt)'
    )

    parser.add_argument(
        'challenge_name',
        help='name of the challenge'
    )

    parser.add_argument(
        'firmware_path',
        help='path to target firmware (.hex)'
    )

    parser.add_argument(
        '-o', '--output',
        default='generated_attack.py',
        help='output script filename (default: generated_attack.py)'
    )

    parser.add_argument(
        '--no-refine',
        action='store_true',
        help='skip iterative refinement'
    )

    args = parser.parse_args()

    success = run_full_pipeline(
        args.trace_file,
        args.challenge_name,
        args.firmware_path,
        args.output,
        refine=not args.no_refine
    )

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
