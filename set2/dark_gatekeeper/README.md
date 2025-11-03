# Dark Gatekeeper - Differential Power Analysis Password Bypass

## Vulnerability

Byte-by-byte password comparison with different execution paths for correct vs incorrect bytes creates distinct power signatures.

## Attack Strategy

1. Test each password position with all 256 possible values
2. Capture power trace for each guess
3. Correct byte produces outlier power signature (different execution path)
4. Use statistical methods (Difference from Mean, Sum of Absolute Differences) to identify outlier
5. Recover all 12 bytes sequentially

**Attack Complexity**: 256 attempts × 12 bytes = 3,072 queries (vs 256^12 ≈ 2^96 for brute force)

## Flag

**ESC{J0lt_Th3_G473}**

## Mitigation

- Constant-time comparison functions
- Masking to randomize intermediate values
- Noise injection
- Hardware countermeasures (secure elements)
- Cryptographic authentication (HMAC) instead of direct comparison
