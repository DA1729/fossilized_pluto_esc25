import numpy as np
from scipy.signal import find_peaks
import anthropic
import os
from api_templates import api_usage_guide

def analyze_trace_statistics(traces):
    if len(traces.shape) == 1:
        traces = traces.reshape(1, -1)

    stats = {
        'n_traces': traces.shape[0],
        'n_samples': traces.shape[1],
        'mean': np.mean(traces, axis=0),
        'std': np.std(traces, axis=0),
        'variance': np.var(traces, axis=0),
        'min': np.min(traces, axis=0),
        'max': np.max(traces, axis=0)
    }

    return stats

def find_high_variance_regions(traces, threshold_percentile=90):
    stats = analyze_trace_statistics(traces)
    variance = stats['variance']

    threshold = np.percentile(variance, threshold_percentile)
    high_var_indices = np.where(variance > threshold)[0]

    if len(high_var_indices) == 0:
        return []

    regions = []
    start = high_var_indices[0]
    prev = high_var_indices[0]

    for idx in high_var_indices[1:]:
        if idx - prev > 100:
            regions.append((int(start), int(prev)))
            start = idx
        prev = idx

    regions.append((int(start), int(prev)))

    return regions[:10]

def detect_variance_peaks(traces, prominence=0.5):
    stats = analyze_trace_statistics(traces)
    variance = stats['variance']

    normalized_var = (variance - np.min(variance)) / (np.max(variance) - np.min(variance) + 1e-10)

    peaks, properties = find_peaks(normalized_var, prominence=prominence, distance=50)

    peak_info = []
    for i, peak in enumerate(peaks[:20]):
        peak_info.append({
            'index': int(peak),
            'value': float(variance[peak]),
            'prominence': float(properties['prominences'][i])
        })

    return peak_info

def analyze_trace_correlation(traces):
    if traces.shape[0] < 2:
        return {}

    sample_indices = np.linspace(0, traces.shape[1]-1, min(10, traces.shape[1]), dtype=int)

    corr_info = {}
    for idx in sample_indices:
        sample_values = traces[:, idx]
        if np.std(sample_values) > 0:
            corr_info[int(idx)] = {
                'mean': float(np.mean(sample_values)),
                'std': float(np.std(sample_values)),
                'range': float(np.max(sample_values) - np.min(sample_values))
            }

    return corr_info

def compute_sad_matrix(traces, reference_idx=0):
    if traces.shape[0] < 2:
        return None

    reference = traces[reference_idx]
    sad_values = []

    sample_size = min(100, traces.shape[0])
    for i in range(1, sample_size):
        sad = np.sum(np.abs(traces[i] - reference))
        sad_values.append(float(sad))

    if len(sad_values) == 0:
        return None

    return {
        'mean_sad': float(np.mean(sad_values)),
        'std_sad': float(np.std(sad_values)),
        'min_sad': float(np.min(sad_values)),
        'max_sad': float(np.max(sad_values))
    }

def format_analysis_for_llm(traces, challenge_name="unknown"):
    stats = analyze_trace_statistics(traces)
    variance_regions = find_high_variance_regions(traces)
    peaks = detect_variance_peaks(traces)
    sad_info = compute_sad_matrix(traces)

    summary = f"""trace analysis for {challenge_name}:

basic statistics:
- number of traces: {stats['n_traces']}
- samples per trace: {stats['n_samples']}
- overall mean power: {np.mean(stats['mean']):.2f}
- overall std deviation: {np.mean(stats['std']):.2f}

high variance regions (potential leakage points):
"""

    for i, (start, end) in enumerate(variance_regions[:5]):
        summary += f"  region {i+1}: samples {start}-{end} (width: {end-start})\n"

    summary += f"\nvariance peaks (top operations):\n"
    for i, peak in enumerate(peaks[:5]):
        summary += f"  peak {i+1}: sample {peak['index']}, prominence {peak['prominence']:.3f}\n"

    if sad_info:
        summary += f"\nsum of absolute differences analysis:\n"
        summary += f"  mean sad: {sad_info['mean_sad']:.1f}\n"
        summary += f"  std sad: {sad_info['std_sad']:.1f}\n"
        summary += f"  range: {sad_info['min_sad']:.1f} to {sad_info['max_sad']:.1f}\n"

    return summary

def query_llm_for_attack(trace_summary, challenge_name, api_key=None):
    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        return "error: anthropic_api_key not found in environment"

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""{trace_summary}

challenge type: {challenge_name}

based on the power trace analysis above, identify the most likely side-channel vulnerability and suggest a specific attack approach.

consider:
1. timing side-channels (if execution time varies with data)
2. differential power analysis (if power consumption reveals data-dependent operations)
3. correlation power analysis (if operations correlate with intermediate cryptographic values)
4. simple power analysis (if distinct operations are visible)

provide:
- vulnerability type
- attack methodology
- key indicators from the trace analysis
- recommended attack parameters

keep response concise and technical."""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"llm query failed: {str(e)}"

def analyze_and_suggest(traces, challenge_name="unknown", api_key=None):
    print(f"\nanalyzing traces for {challenge_name}...")

    trace_summary = format_analysis_for_llm(traces, challenge_name)
    print(trace_summary)

    print("\nquerying llm for attack suggestions...")
    llm_response = query_llm_for_attack(trace_summary, challenge_name, api_key)

    print("\nllm analysis:")
    print("-" * 60)
    print(llm_response)
    print("-" * 60)

    return {
        'trace_summary': trace_summary,
        'llm_response': llm_response
    }
