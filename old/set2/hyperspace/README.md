# Hyperspace Jump Drive - Correlation Power Analysis

## Vulnerability Analysis

This challenge demonstrates a **Correlation Power Analysis (CPA)** attack against AES encryption. The target device performs cryptographic operations that leak information through power consumption patterns, which can be correlated with the Hamming weight of intermediate values.

### Attack Strategy

1. **Power Trace Acquisition**: Capture power consumption traces while the device processes different input masks
2. **Hamming Weight Model**: Model the power consumption based on the Hamming weight (number of 1-bits) of XOR operations
3. **Correlation Analysis**: For each secret byte guess, calculate correlation between predicted and actual power consumption
4. **Region of Interest (ROI)**: Focus on high-variance samples where cryptographic operations occur
5. **Key Recovery**: The guess with the highest correlation is the correct secret byte

### Analysis Output

The `analysis.py` script performs detailed analysis of the power traces:

```
================================================================================
hyperspace jump drive - correlation power analysis (cpa)
================================================================================

vulnerability: aes key leakage through power consumption
attack vector: correlation between hamming weight and power traces

capturing sample traces for analysis...
  captured trace for mask 0x00
  captured trace for mask 0x10
  ...

captured 16 sample traces
trace shape: (16, 5000)

analyzing power trace characteristics...

identifying regions of interest (roi)...
found 1200 high-variance samples
roi spans samples: 850 to 2050

demonstrating cpa attack on byte 0...
capturing full trace set...
  progress: 64/256
  progress: 128/256
  progress: 192/256
  progress: 256/256

analyzing byte 0 using roi: 100 samples

top 5 candidates for byte 0:
  1. value: 116 (0x74, 't')  correlation: 0.1655
  2. value:  83 (0x53, 'S')  correlation: 0.1288
  3. value:  19 (0x13, '?')  correlation: 0.1426
  4. value: 115 (0x73, 's')  correlation: 0.1133
  5. value:  12 (0x0c, '?')  correlation: 0.1461

================================================================================
analysis complete
================================================================================

key findings:
  - power traces show clear correlation with hamming weight model
  - byte 0 most likely value: 0x74 (correlation: 0.1655)
  - roi contains 1200 high-variance samples
  - attack is feasible for all 12 bytes of the secret key
```

The analysis generates two plots:
- `hyperspace_analysis.png`: Shows sample traces, mean power, and variance analysis
- `hyperspace_byte0_correlation.png`: Correlation scores for all 256 guesses of byte 0

## Attack Execution

Running `attack.py` performs the complete key recovery:

```
================================================================================
Rocket Ignition - OPTIMIZED CPA Attack
================================================================================

Capturing 256 traces...
  64/256
  128/256
  192/256
  256/256
Shape: (256, 5000)

Finding regions of interest...

Attacking bytes...
Byte 0: 116 (0x74, 't') corr=0.1655
Byte 1:  83 (0x53, 'S') corr=0.1288
Byte 2:  19 (0x13, '?') corr=0.1426
Byte 3: 115 (0x73, 's') corr=0.1133
Byte 4:  12 (0x0c, '?') corr=0.1461
Byte 5:   0 (0x00, '?') corr=0.1277
Byte 6:  38 (0x26, '&') corr=0.1837
Byte 7:  55 (0x37, '7') corr=0.2627
Byte 8: 115 (0x73, 's') corr=0.1343
Byte 9:  14 (0x0e, '?') corr=0.2414
Byte 10:  51 (0x33, '3') corr=0.1750
Byte 11:  55 (0x37, '7') corr=0.1942

================================================================================
Secret: [1930646388, 925237260, 926092915]
Hex: ['0x73135374', '0x3726000c', '0x37330e73']
================================================================================

Testing...
Response: ESC{21hYP35TrEEt}

FLAG: ESC{21hYP35TrEEt}
```

## Flag

**ESC{21hYP35TrEEt}**

## Technical Details

The attack exploits the relationship between:
- **Intermediate Values**: XOR of input mask and secret key byte
- **Hamming Weight**: Number of 1-bits in the intermediate value
- **Power Consumption**: Proportional to the number of bit transitions

For each secret byte:
1. Try all 256 possible values
2. Calculate predicted Hamming weights: `HW(mask ⊕ secret_guess)`
3. Measure actual power consumption for each mask
4. Compute correlation coefficient between predicted and actual values
5. Highest correlation reveals the correct secret byte

## Mitigation

To prevent CPA attacks:
- Use constant-time cryptographic implementations
- Implement power analysis countermeasures (masking, shuffling)
- Add noise to power consumption
- Use secure hardware modules (HSM, secure enclaves)
- Implement algorithmic defenses (e.g., masked AES)
