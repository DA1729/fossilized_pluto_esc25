# Alchemist Infuser - Advanced CPA with Trace Alignment

## Vulnerability Analysis

This challenge demonstrates an advanced **Correlation Power Analysis (CPA)** attack against a block cipher implementation (likely DES or similar). The attack requires sophisticated trace alignment techniques to compensate for timing variations in the target device's execution.

### Attack Strategy

The attack consists of multiple phases:

1. **Trace Collection**: Capture 1000+ power traces with random plaintexts
2. **Peak Detection**: Identify the 16 operation points where round operations occur
3. **Trace Alignment**: For each byte, align traces using Sum of Absolute Differences (SAD)
4. **Phase 1 CPA**: Recover candidate pairs for key bytes 0-7 using Hamming weight correlation
5. **Phase 2 CPA**: For each Phase 1 candidate, recover candidates for bytes 8-15
6. **Brute Force**: Test all 2^16 combinations to find the correct key

### Analysis Output

The `analysis.py` script captures traces and identifies operation peaks:

```
programming target...
Detected known STMF32: STM32F04xxx
Extended erase (0x44), this can take ten seconds or more
Attempting to program 6707 bytes at 0x8000000
STM32F Programming flash...
STM32F Reading flash...
Verified flash OK, 6707 bytes
resetting target...
target is now running.

capturing 1000 traces...
Capturing traces: 100%|███████████████████████████| 1000/1000 [00:14<00:00, 70.88it/s]
capture complete. 0 errors encountered.

saving traces to traces.npy...
traces saved successfully.

analyzing traces from traces.npy (samples 0-3250)...
loaded 1000 traces with 5000 samples each.
calculating standard deviation...
finding peaks with distance=100, height=0.0111...
found 16 peaks within samples 0-3250.
generating combined plot...
plot saved to alchemist_peak_analysis.png

detected peak offsets (sample indices):
[59, 262, 465, 668, 871, 1074, 1277, 1480, 1684, 1888, 2092, 2296, 2500, 2704, 2908, 3112]

success: found exactly 16 peaks!
peak offsets for attack script:
op_offsets = [59, 262, 465, 668, 871, 1074, 1277, 1480, 1684, 1888, 2092, 2296, 2500, 2704, 2908, 3112]

analysis complete.
scope and target disconnected.
```

The analysis generates a visualization (`alchemist_peak_analysis.png`) showing:
- Sample power trace with detected peaks
- Standard deviation across all traces
- Vertical markers at each of the 16 operation points

## Attack Execution

Running `attack.py` performs the complete key recovery:

```
programming target...
Detected known STMF32: STM32F04xxx
Extended erase (0x44), this can take ten seconds or more
Attempting to program 6707 bytes at 0x8000000
STM32F Programming flash...
STM32F Reading flash...
Verified flash OK, 6707 bytes
resetting target...
target is now running.

capturing 5000 traces...
Capturing traces: 100%|███████████████████████████| 5000/5000 [01:09<00:00, 72.24it/s]
capture complete. 0 errors encountered.

starting phase 1 (key bytes 0-7)...
Attacking key bytes 0-7:   0%|                                           | 0/8 [00:00<?, ?it/s]

  Byte 0 - Top 2 Pairs (guess: correlation):
    Pair 1: 0x4e: 0.6800
            0xb1: 0.6800
    Pair 2: 0x31: 0.6558
            0xce: 0.6558
  Margin (Pair 1 - Pair 2): 0.0243

[... similar output for bytes 1-7 ...]

Attacking key bytes 0-7: 100%|████████████████████████████████████████████| 8/8 [00:11<00:00,  1.41s/it]

phase 1 done. candidate pairs: [('0x4e', '0xb1'), ('0x9e', '0x61'), ('0xb5', '0x4a'), ('0x2d', '0xd2'), ('0xaa', '0x55'), ('0x98', '0x67'), ('0xad', '0x52'), ('0x9b', '0x64')]

starting phase 2 & brute-force (2^16 keys)...
Checking 1st-half keys:  43%|██████████████████████████████| 111/256 [35:58<47:27, 19.64s/it]

key found!
key (hex): 4e614a2d556752643270586b38763573
flag: a1c{Wh1teDragonT}
Checking 1st-half keys:  43%|██████████████████████████████| 111/256 [36:15<47:21, 19.60s/it]

analysis complete, disconnecting...
scope and target disconnected.
```

## Flag

**a1c{Wh1teDragonT}**

## Technical Details

### Trace Alignment

Due to timing jitter in the target device, traces must be aligned before CPA can be effective. The attack uses Sum of Absolute Differences (SAD) alignment:

1. For each byte position, identify the expected operation window
2. Extract a reference pattern from the first trace
3. For each trace, search nearby samples for the best match using SAD
4. Shift the trace to align the operation with the reference

### Two-Phase Attack

The attack uses a clever reduction strategy:

**Phase 1**: Attack bytes 0-7 independently
- For each byte, CPA returns the top 2 candidates
- This gives 2^8 = 256 possible first-half keys

**Phase 2**: For each first-half candidate, attack bytes 8-15
- Use the assumed first-half key to transform the data
- Attack the second round operations
- Each byte gives 2 candidates

**Brute Force**: Test 2 × 2 × ... × 2 (16 times) = 2^16 = 65,536 total keys

The key insight is that the second round's input depends on the first round's key, allowing this divide-and-conquer approach.

### Key Recovery Process

1. The block cipher performs 16 XOR operations (2 per byte, 8 bytes total)
2. Each XOR operation's Hamming weight correlates with power consumption
3. By aligning traces to each operation point and applying CPA, we recover key candidates
4. The correct key produces the highest correlation coefficient

### Attack Parameters

- **N_TRACE**: 5000 traces for reliable statistics
- **MAX_SHIFT**: 25 samples search range for alignment
- **OP_WIDTH**: 15 samples window for SAD matching
- **OP_OFFSETS**: 16 pre-computed peak locations

## Mitigation

To defend against advanced CPA attacks:
- **Hardware Countermeasures**: Use masked implementations or dual-rail logic
- **Algorithmic Defenses**: Implement random delays, dummy operations, or shuffling
- **Secure Elements**: Use cryptographic co-processors with built-in DPA resistance
- **Power Filtering**: Add noise or use constant-power designs
- **Software Masking**: Split sensitive variables into random shares
