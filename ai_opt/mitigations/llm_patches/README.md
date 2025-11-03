# LLM-Generated Security Mitigations

AI/ML-assisted security patches for all ESC 2025 Finals challenges developed through iterative consultation with LLMs.

## Challenge Coverage

### Set 1
- **Gatekeeper**: Constant-time comparison + random delays
- **Sorters Song**: Constant-time swap + shuffling + blinding
- **Critical Calculation**: TMR + canary values + timing bounds

### Set 2
- **Hyperspace**: Boolean masking + operation shuffling
- **Dark Gatekeeper**: First-order masking + random delays
- **Ghost Blood**: Masked ARX operations + threshold randomization

### Set 3
- **Echoes**: Constant-time operations + array shuffling
- **Alchemist**: Second-order masking + clock jitter

## Mitigation Techniques

1. **Constant-Time Operations**: Eliminates data-dependent branches
2. **Boolean Masking**: Splits sensitive variables into random shares (first/second-order)
3. **Operation Shuffling**: Randomizes execution order
4. **Random Delays**: Adds temporal noise (10-100 CPU cycles)
5. **Triple Modular Redundancy**: Executes computation three times with majority voting
6. **XOR Blinding**: Random masking to decouple power consumption from values
7. **Clock Jitter**: Hardware-level timing variation

## Implementation Requirements

- Hardware RNG for quality randomness
- Volatile qualifiers to prevent compiler optimization
- Memory clearing of sensitive data after use
- Timing validation for constant-time property

## Notes

- All mitigations tested against original attack scripts
- Requires security review before production deployment
- Each challenge has paired `.md` (analysis) and `.c` (patch) files
