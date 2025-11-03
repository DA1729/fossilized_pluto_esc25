# Hyperspace Jump Drive - Correlation Power Analysis

## Vulnerability

AES key leakage through power consumption. Power consumption correlates with Hamming weight of intermediate values (`mask ⊕ secret_byte`).

## Attack Strategy

1. Capture power traces while device processes different input masks
2. For each secret byte guess, calculate predicted Hamming weights
3. Compute correlation between predicted Hamming weight and actual power consumption
4. Focus on high-variance samples (Region of Interest) where crypto operations occur
5. Highest correlation reveals correct secret byte

## Flag

**ESC{21hYP35TrEEt}**

## Mitigation

- Constant-time cryptographic implementations
- Power analysis countermeasures (masking, shuffling)
- Noise injection
- Secure hardware modules (HSM, secure enclaves)
- Masked AES implementations
