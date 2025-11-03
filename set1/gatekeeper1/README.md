# Gatekeeper1 - Timing Side-Channel Attack

## Vulnerability

Byte-by-byte password comparison with early termination creates measurable timing differences that reveal correct characters.

## Attack Strategy

1. Test all possible characters at each position and measure response times
2. Collect multiple samples and use median timing to reduce noise
3. The character producing the longest execution time is correct
4. Recover each character sequentially to build the complete password

## Flag

**gk1{l0g1npwn}**

## Mitigation

- Use constant-time comparison functions
- Avoid early termination in security-critical comparisons
- Implement proper password hashing (bcrypt, scrypt, Argon2)
