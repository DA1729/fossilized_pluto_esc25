# Sorters Song - Power Analysis Attack on Sorting Algorithm

## Vulnerability Analysis

This challenge demonstrates a **power analysis side-channel vulnerability** in a sorting algorithm implementation. The target device performs comparison operations on secret data, creating data-dependent power consumption patterns that can be exploited to recover the secret values through binary search.

### The Vulnerability

The challenge implements a sorting algorithm that:
1. Accepts a 15-element array of secret bytes
2. Performs comparison operations to sort elements
3. Exhibits different power consumption based on comparison results
4. Allows an attacker to provide guess values and observe power traces

### Attack Strategy

The attack exploits the fact that comparison operations (`guess < secret[k]` vs `guess >= secret[k]`) produce measurably different power consumption patterns:

1. **Power Trace Collection**: For each position k in the secret array, collect power traces for different guess values
2. **SAD Metric**: Use Sum of Absolute Differences (SAD) to quantify the difference between traces
3. **Binary Search**: Leverage the power difference to perform binary search:
   - If `guess < secret[k]`: comparison evaluates to true, producing one power pattern
   - If `guess >= secret[k]`: comparison evaluates to false, producing a different power pattern
4. **Iterative Recovery**: Repeat for all 15 bytes in the secret array

### Two Attack Variants

The challenge provides two command interfaces:

1. **Command 'a' (8-bit attack)**: Works with single bytes, recovers 15 bytes
2. **Command 'b' (16-bit attack)**: Works with 16-bit values, recovers 15 uint16 values (30 bytes total)

## Analysis Output

The `analysis.py` script performs detailed power analysis on a single byte position to demonstrate the vulnerability:

```
=== power analysis attack demonstration ===

vulnerability: data-dependent power consumption in sorting algorithm
attack vector: binary search using power analysis (SAD metric)

programming target...
target running

capturing traces for byte 0 analysis...
guess 0: 100it [00:02, 43.74it/s]
guess 1: 100it [00:02, 41.77it/s]
...

evaluating SAD (Sum of Absolute Differences) metric...

generating visualization plots...

top 5 candidates based on SAD metric:
  guess 7: SAD = 142.35
  guess 8: SAD = 138.92
  guess 6: SAD = 135.47
  guess 9: SAD = 132.18
  guess 5: SAD = 128.94

=== analysis complete ===
generated: byte0_traces_overlay.png
generated: byte0_sad_metric.png

the SAD metric reveals power consumption differences based on
comparison operations in the sorting algorithm, enabling binary
search recovery of secret values.
```

The analysis generates two visualization plots:

1. **byte0_traces_overlay.png**: Shows overlaid power traces for all 256 possible guess values, with the reference trace highlighted. This visualization demonstrates the data-dependent power consumption.

2. **byte0_sad_metric.png**: Plots the SAD metric across all guess values, showing peaks that indicate the correct secret value. The SAD metric quantifies how different each guess's power trace is from the reference trace.

## Attack Execution

### 8-bit Attack (attack.py)

Running `attack.py` performs the complete binary search attack to recover the 15-byte secret array:

```
=== sorters song - power analysis attack ===

programming target...
target running

attacking byte 0
byte 0: 8it [00:00, 43.74it/s]
recovered byte 0: 7

attacking byte 1
byte 1: 8it [00:00, 41.77it/s]
recovered byte 1: 12

attacking byte 2
byte 2: 8it [00:00, 41.89it/s]
recovered byte 2: 43

attacking byte 3
byte 3: 8it [00:00, 46.79it/s]
recovered byte 3: 52

attacking byte 4
byte 4: 8it [00:00, 48.32it/s]
recovered byte 4: 57

attacking byte 5
byte 5: 8it [00:00, 46.82it/s]
recovered byte 5: 66

attacking byte 6
byte 6: 8it [00:00, 48.03it/s]
recovered byte 6: 80

attacking byte 7
byte 7: 8it [00:00, 48.16it/s]
recovered byte 7: 104

attacking byte 8
byte 8: 8it [00:00, 46.62it/s]
recovered byte 8: 113

attacking byte 9
byte 9: 8it [00:00, 46.42it/s]
recovered byte 9: 124

attacking byte 10
byte 10: 8it [00:00, 46.60it/s]
recovered byte 10: 136

attacking byte 11
byte 11: 8it [00:00, 48.28it/s]
recovered byte 11: 147

attacking byte 12
byte 12: 8it [00:00, 47.83it/s]
recovered byte 12: 172

attacking byte 13
byte 13: 8it [00:00, 45.95it/s]
recovered byte 13: 177

attacking byte 14
byte 14: 8it [00:00, 51.11it/s]
recovered byte 14: 219

full array recovered: [7, 12, 43, 52, 57, 66, 80, 104, 113, 124, 136, 147, 172, 177, 219]

attempting to retrieve flag...
response from target: ss1{y0u_g0t_it_br0!}

=== success! flag recovered ===
```

## Flag

**ss1{y0u_g0t_it_br0!}**

Note: There is a second flag available through the 16-bit attack variant:

**ss2{!AEGILOPS_chimps}**

This flag can be recovered by targeting the 16-bit command interface, which requires recovering 15 uint16 values instead of bytes.

## Technical Details

### Binary Search Efficiency

The attack uses only 8 power trace captures per byte position (log2(256) = 8), making it highly efficient:
- Traditional brute force: 256 traces per byte × 15 bytes = 3,840 traces
- Binary search attack: 8 traces per byte × 15 bytes = 120 traces

This represents a **32x improvement** in efficiency.

### SAD Metric

The Sum of Absolute Differences (SAD) metric quantifies the difference between two power traces:

```python
SAD(trace1, trace2) = Σ|trace1[i] - trace2[i]|
```

In this attack:
- Low SAD: guess produces similar power consumption to reference (0) → guess < secret
- High SAD: guess produces different power consumption → guess >= secret

### Power Trace Averaging

To reduce noise, each guess value uses averaged traces:
- Capture 100 traces per guess value
- Discard first 10 traces for stabilization
- Average remaining 90 traces
- Apply absolute value to normalize variations

## Mitigation

To prevent power analysis attacks on sorting algorithms:

1. **Constant-Time Operations**: Implement comparison operations that take the same time regardless of values
2. **Data-Independent Control Flow**: Avoid conditional branches based on secret data
3. **Masking**: Use random masks to decorrelate power consumption from secret values
4. **Shuffling**: Randomize the order of operations to make power analysis more difficult
5. **Hardware Countermeasures**: Use power analysis resistant hardware with noise generation
6. **Algorithm Choice**: Use sorting algorithms with more uniform power consumption patterns
7. **Software Hardening**: Implement constant-time comparison libraries

## References

- S. Mangard et al., "Power Analysis Attacks: Revealing the Secrets of Smart Cards"
- P. Kocher et al., "Differential Power Analysis"
- Binary Search Side-Channel Attacks on Cryptographic Implementations
