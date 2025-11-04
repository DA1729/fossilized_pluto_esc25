# Gatekeeper2 - Extended Timing Side-Channel Attack

## Vulnerability

Same timing side-channel vulnerability as Gatekeeper1 but with a longer password (17 characters vs 13) and different command interface ('b' vs 'a').

## Attack Strategy

1. Use timing differences to reveal correct characters at each position
2. Increase sample size (15 samples vs 10) for better accuracy with longer password
3. Apply same principle as Gatekeeper1

## Flag

**gk1{l0g1npwn}wlb4**

Note: Automated attack may occasionally produce incorrect results due to timing noise. Increasing SAMPLES parameter and adding delays improves accuracy.

## Mitigation

- Use constant-time comparison functions
- Avoid early termination in security-critical comparisons
- Implement proper password hashing (bcrypt, scrypt, Argon2)
- Use HMAC-based verification instead of direct comparison
