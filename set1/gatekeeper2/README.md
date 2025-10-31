# Gatekeeper2 - Extended Timing Side-Channel Attack

## Vulnerability Analysis

This challenge extends the timing side-channel vulnerability from Gatekeeper1 with a longer password and different command interface. The same fundamental vulnerability exists: byte-by-byte comparison with early termination creates measurable timing differences.

### Attack Strategy

1. **Extended Password Length**: This challenge uses a 17-character password instead of 13
2. **Different Command**: Uses 'b' command instead of 'a' for password verification
3. **Increased Sample Size**: Uses 15 samples per character instead of 10 for better accuracy with the longer password
4. **Same Principle**: Timing differences still reveal the correct character at each position

### Analysis Output

The `analysis.py` script performs timing analysis on the first few positions:

```
=== timing side-channel analysis (gatekeeper2) ===

vulnerability: byte-by-byte password comparison with longer password
attack vector: timing differences reveal correct characters
difference from gatekeeper1: different command ('b' vs 'a') and longer password

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

The analysis generates timing distribution plots demonstrating the measurable timing differences between correct and incorrect character guesses.

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
position 13: guessed 'w'
position 14: guessed 'l'
position 15: guessed 'b'
position 16: guessed '4'
guessed password: gk1{l0g1npwn}wlb4
```

## Flag

**gk1{l0g1npwn}wlb4**

Note: The automated attack may occasionally produce incorrect results due to timing noise. The correct flag is shown above. Increasing the SAMPLES parameter and adding delays can improve accuracy.

## Mitigation

To prevent timing side-channel attacks:
- Use constant-time comparison functions
- Avoid early termination in security-critical comparisons
- Implement proper password hashing (bcrypt, scrypt, Argon2)
- Use HMAC-based verification instead of direct comparison
