# Dark Gatekeeper - Differential Power Analysis Password Bypass

## Vulnerability Analysis

This challenge demonstrates a **Differential Power Analysis (DPA)** attack against password verification. Unlike timing attacks, this exploit uses power consumption differences to distinguish correct from incorrect password bytes. When the correct byte is processed, the device's execution path differs, creating a measurable power signature.

### Attack Strategy

1. **Byte-by-Byte Attack**: Test each password position independently with all 256 possible values
2. **Power Trace Collection**: Capture power consumption for each guess
3. **Differential Analysis**: The correct byte produces a distinct power signature (outlier)
4. **Statistical Methods**:
   - **Difference from Mean**: Correct byte execution path differs from typical incorrect guesses
   - **Sum of Absolute Differences (SAD)**: Measure how different each trace is from all others
   - **Combined Scoring**: Normalize and combine both metrics

### Analysis Output

The `analysis.py` script demonstrates the vulnerability:

```
================================================================================
dark gatekeeper - differential power analysis
================================================================================

vulnerability: byte-by-byte comparison with power leakage
attack vector: differential power analysis reveals correct bytes

analyzing byte position 0...
  capturing traces for sample values...
    captured trace for value 0
    captured trace for value 50
    captured trace for value 100
    captured trace for value 150
    captured trace for value 200
    captured trace for value 250

visualizing power differences...

performing differential analysis on byte 0...
  capturing full set of 256 traces...
    progress: 64/256
    progress: 128/256
    progress: 192/256
    progress: 256/256

  analyzing trace differences...

  top 5 candidates for byte 0:
    1. value:  55 (0x37, '7')  score: 2.0000
    2. value: 214 (0xd6, '?')  score: 0.1302
    3. value: 216 (0xd8, '?')  score: 0.1298
    4. value: 215 (0xd7, '?')  score: 0.1247
    5. value: 227 (0xe3, '?')  score: 0.1203

================================================================================
analysis complete
================================================================================

key findings:
  - correct byte produces distinct power signature (outlier)
  - byte 0 most likely value: 0x37 ('7')
  - differential score: 2.0000
  - attack can recover all 12 bytes iteratively
```

The analysis generates two plots:
- `dark_gatekeeper_traces.png`: Comparison of power traces for different guesses
- `dark_gatekeeper_byte0_scores.png`: Differential scores for all 256 byte values

## Attack Execution

Running `attack.py` performs the complete password recovery:

```
================================================================================
Password Bypass - Correlation Power Analysis (CPA)
================================================================================

Starting byte-by-byte CPA attack...
--------------------------------------------------------------------------------

Attacking byte position 0...
  Capturing traces for all 256 values...
    Progress: 64/256
    Progress: 128/256
    Progress: 192/256
    Progress: 256/256

  Top 5 candidates:
    1. Value:  55 (0x37, '7')  Score: 2.0000
    2. Value: 214 (0xd6, '?')  Score: 0.1302
    [...]

  Recovered so far: [55]
  As string: 7
  As hex: 37

[... repeating for all 12 bytes ...]

Attacking byte position 11...
  [...]
  Top 5 candidates:
    1. Value:  33 (0x21, '!')  Score: 2.0000
    [...]

  Recovered so far: [55, 78, 52, 62, 113, 112, 49, 52, 99, 55, 48, 33]
  As string: 7N4>qp14c70!
  As hex: 37 4e 34 3e 71 70 31 34 63 37 30 21

================================================================================
Verifying recovered password...
--------------------------------------------------------------------------------

Recovered password: [55, 78, 52, 62, 113, 112, 49, 52, 99, 55, 48, 33]
As string: 7N4>qp14c70!
As hex: 37 4e 34 3e 71 70 31 34 63 37 30 21

Server response: ESC{J0lt_Th3_G473}

================================================================================
SUCCESS! FLAG: ESC{J0lt_Th3_G473}
================================================================================

Total password attempts: 3072

Attack complete!
```

## Flag

**ESC{J0lt_Th3_G473}**

## Technical Details

### Why This Works

The vulnerability exists because when the correct byte is guessed:
1. The comparison `if (input[i] != secret[i])` evaluates to FALSE (bytes match)
2. The error-setting code inside the if-block is NOT executed
3. Execution continues to the next byte

When an incorrect byte is guessed:
1. The comparison evaluates to TRUE (bytes don't match)
2. The error-setting code IS executed
3. Different CPU instructions are executed

These different execution paths produce measurably different power consumption patterns.

### Attack Complexity

- **Queries**: 256 attempts per byte × 12 bytes = 3,072 total queries
- **Advantage**: Much faster than brute force (256^12 ≈ 2^96 combinations)
- **Success Rate**: Near 100% when correct byte is a clear outlier

## Mitigation

To prevent differential power analysis attacks:
- **Constant-Time Comparison**: Use comparison functions that always execute the same operations
- **Masking**: Randomize intermediate values during computation
- **Noise Injection**: Add random operations to obscure power patterns
- **Hardware Countermeasures**: Use secure elements with DPA-resistant designs
- **Proper Authentication**: Use cryptographic authentication (HMAC) instead of direct comparison
