# Echoes - Timing Side-Channel Attack on Sorting Algorithm

## Vulnerability

Sorting algorithm with comparison operations that exhibit timing differences:
- **SHORT path**: `guess <= secret[pos]` → lower power consumption
- **LONG path**: `guess > secret[pos]` → higher power consumption

Timing oracle enables binary search recovery (16 queries per 16-bit value vs 65,536 for brute force).

## Attack Strategy

**Automated two-stage recovery:**

1. **Parameter Optimization** (per position):
   - Test multiple sample sizes and window configurations
   - Capture 1000 calibration traces
   - Select optimal parameters for SHORT/LONG path separation

2. **Binary Search Recovery**:
   - Use windowed energy analysis to distinguish execution paths
   - Perform 16-iteration binary search for each 16-bit value
   - Repeat for all 15 array positions

3. **Flag Retrieval**: Sort recovered array and send to retrieve flag

**Efficiency**: ~270,000 total traces for 15 values (~18,000 per value)

## Flag

**eoc{th3yreC00ked}**

## Mitigation

- Constant-time/data-oblivious algorithms
- Balanced branches with equal execution time
- Random delays to mask execution paths
- Shuffling and blinding techniques
- Hardware countermeasures (dual-rail logic, randomized clocking)
