# Alchemist Infuser - Advanced CPA with Trace Alignment

## Vulnerability

Block cipher implementation with power leakage during XOR operations. Requires trace alignment to compensate for timing jitter.

## Attack Strategy

**Multi-phase divide-and-conquer approach:**

1. **Trace Collection**: Capture 5000 power traces with random plaintexts
2. **Peak Detection**: Identify 16 operation points where round operations occur
3. **Trace Alignment**: Align traces using Sum of Absolute Differences (SAD) to compensate for timing jitter
4. **Phase 1 CPA**: Recover top 2 candidates for key bytes 0-7 (2^8 = 256 first-half keys)
5. **Phase 2 CPA**: For each Phase 1 candidate, recover candidates for bytes 8-15
6. **Brute Force**: Test 2^16 = 65,536 total key combinations

## Flag

**a1c{Wh1teDragonT}**

## Mitigation

- Masked implementations or dual-rail logic
- Random delays, dummy operations, shuffling
- Cryptographic co-processors with DPA resistance
- Power filtering and noise injection
- Software masking (split sensitive variables into random shares)
