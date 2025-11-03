# Sorters Song - Power Analysis Attack on Sorting Algorithm

## Vulnerability

Data-dependent power consumption in sorting algorithm comparison operations (`guess < secret[k]` vs `guess >= secret[k]`) enables binary search recovery of secret values.

## Attack Strategy

1. Collect power traces for different guess values at each position
2. Use Sum of Absolute Differences (SAD) metric to quantify trace differences
3. Perform binary search leveraging power differences (only 8 traces per byte vs 256 for brute force)
4. Repeat for all 15 bytes in the secret array

## Attack Variants

- **Command 'a' (8-bit)**: Recovers 15 bytes → **ss1{y0u_g0t_it_br0!}**
- **Command 'b' (16-bit)**: Recovers 15 uint16 values → **ss2{!AEGILOPS_chimps}**

## Flags

**ss1{y0u_g0t_it_br0!}**

**ss2{!AEGILOPS_chimps}**

## Mitigation

- Constant-time comparison operations
- Data-independent control flow
- Masking with random values
- Hardware countermeasures (noise generation)
- Constant-time comparison libraries
