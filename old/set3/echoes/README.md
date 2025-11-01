# Echoes - Timing Side-Channel Attack on Sorting Algorithm

## Challenge Overview

This challenge exploits a timing side-channel vulnerability in a sorting algorithm implementation running on an STM32F0 microcontroller. The target uses a comparison-based sorting algorithm where execution time varies depending on whether a comparison returns true or false, creating a detectable power consumption difference.

## Vulnerability

The firmware implements a sorting routine that processes an array of 15 uint16_t values. When queried with a test value at a specific position, the device performs comparisons that exhibit timing differences:

- **SHORT path**: When `guess <= secret[pos]`, execution takes less time (lower power)
- **LONG path**: When `guess > secret[pos]`, execution takes more time (higher power)

This timing oracle can be exploited via binary search to recover each secret value using only 16 queries per byte.

## Setup

- **Target Platform**: STM32F0 series MCU (ChipWhisperer Nano)
- **Firmware**: `chaos-CWNANO.hex`
- **Attack Type**: Timing side-channel analysis via power consumption
- **Communication**: SimpleSerial protocol
- **Secret Array**: 15 uint16_t values (30 bytes total)

## Approach

### 1. Analysis Phase (`analysis.py`)

The analysis script characterizes the timing side-channel:

- Captures power traces for different guess values at a specific position
- Generates visualizations showing power consumption variations
- Identifies windowed energy differences between SHORT and LONG paths
- Demonstrates the existence and measurability of the timing oracle

**Key Outputs:**
- `power_traces_analysis.png` - Power traces for 10 different guess values
- `windowed_energy_vs_guess.png` - Energy consumption vs guess value
- `power_trace_differences.png` - Differential power analysis

### 2. Attack Phase (`attack.py`)

The attack implements a fully automated two-stage recovery process:

**Stage 1: Parameter Optimization (Per Position)**
- Tests multiple scope.adc.samples values: [1500, 2000, 3000, 5000]
- Tests multiple window configurations for best separation
- Captures N_ANALYSIS=1000 traces for calibration
- Selects optimal parameters based on balanced accuracy

**Stage 2: Binary Search Recovery**
- Uses optimized parameters to distinguish SHORT vs LONG paths
- Performs 16-iteration binary search (for 16-bit values)
- Recovers secret value with high confidence
- Repeats for all 15 array positions

**Stage 3: Flag Retrieval**
- Sorts the recovered array
- Constructs the 30-byte payload
- Sends via 'a' command to retrieve flag

## Attack Parameters

- **N_ANALYSIS**: 1000 traces (fixed for consistency)
- **SKIP_TRACES**: 10 (initial traces discarded for stability)
- **Sample sizes tested**: [1500, 2000, 3000, 5000]
- **Window configurations**: Various combinations of window size and step
- **Total queries per byte**: ~2000 for optimization + ~16,000 for recovery = ~18,000 per byte
- **Total queries for full attack**: ~270,000 traces for all 15 bytes

## Results

```
Recovered array:
[27964, 697, 45996, 36080, 58772, 9092, 42349, 6536, 13983, 25986, 64748, 64986, 29600, 49204, 19617]

Sorted array:
[697, 6536, 9092, 13983, 19617, 25986, 27964, 29600, 36080, 42349, 45996, 49204, 58772, 64748, 64986]

Flag: eoc{th3yreC00ked}
```

## Attack Methodology

1. **Calibration**: For each array position, capture traces with extreme guess values (0 and 65535) to establish baseline power signatures
2. **Window Optimization**: Identify time windows in the power trace that maximize separation between SHORT and LONG paths
3. **Threshold Calculation**: Compute threshold as midpoint between mean energy of SHORT and LONG paths
4. **Oracle Direction**: Determine if higher energy indicates LONG path (NORMAL) or SHORT path (INVERTED)
5. **Binary Search**: Use the timing oracle to perform binary search recovery
6. **Verification**: Test boundary conditions to confirm recovered value

## Key Insights

- **Adaptive Optimization**: Per-position parameter tuning significantly improves reliability across different array elements
- **Windowed Analysis**: Focusing on specific time windows reduces noise and improves signal-to-noise ratio
- **Automated Recovery**: Full automation enables practical attack execution without manual parameter tuning
- **Query Efficiency**: Binary search reduces queries from 65536 (brute force) to 16 per value
- **Timing Oracle**: Even subtle timing differences (microseconds) create measurable power variations

## Mitigation Strategies

1. **Constant-Time Algorithms**: Use data-oblivious comparison and sorting algorithms
2. **Balanced Branches**: Ensure equal execution time for all comparison outcomes
3. **Random Delays**: Add random timing variations to mask true execution paths
4. **Shuffling**: Shuffle array positions before sorting to prevent positional leakage
5. **Blinding**: Apply cryptographic blinding to input values
6. **Hardware Countermeasures**: Implement dual-rail logic or randomized clocking

## Usage

### Run Analysis:
```bash
python analysis.py
```
Captures power traces and generates visualization plots for one example position.

### Run Automated Attack:
```bash
python attack.py
```
Fully automated recovery of all 15 bytes and flag retrieval. Expected runtime: 45-60 minutes depending on hardware.

## Performance

- **Per-byte recovery time**: ~3-4 minutes
- **Total attack time**: ~45-60 minutes for complete flag recovery
- **Success rate**: >95% with N_ANALYSIS=1000
- **Queries per byte**: ~18,000 traces

## Dependencies

- ChipWhisperer toolkit (>= 5.7.0)
- NumPy
- Matplotlib
- SciPy (for signal processing)
- tqdm (for progress bars)

## Notes

- The attack script automatically optimizes parameters for each position
- No manual intervention required - fully autonomous recovery
- Original solution used different N_ANALYSIS values per byte (ranging from 500-2000)
- This refined version uses fixed N_ANALYSIS=1000 for consistency and reproducibility
