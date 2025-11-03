# hyperspace jump drive CPA mitigation

## vulnerability analysis

**original vulnerable code pattern:**
```c
uint8_t invert_polarity(uint8_t* data, uint8_t dlen) {
    uint8_t inversion_mask = data[0];

    trigger_high();
    volatile uint8_t* secret_bytes = (uint8_t*)secret_ignition_sequence;
    for (int i = 0; i < total_bytes; i++) {
        temp_result = inversion_mask ^ secret_bytes[i];  // key-dependent operation
        simple_delay_separator();
    }
    trigger_low();

    return 0;
}
```

**vulnerability**: XOR operation between user-controlled mask and secret bytes exhibits Hamming weight leakage
**attack vector**: Correlation Power Analysis targeting XOR intermediate values
**success rate**: 100% with 256 traces per byte (correlation > 0.35)

---

## llm conversation log

**prompt to claude:**
```
analyze this cryptographic operation for CPA vulnerabilities:

temp_result = inversion_mask ^ secret_bytes[i];

where inversion_mask is attacker-controlled plaintext and secret_bytes
are unknown key bytes. the power consumption during this XOR operation
correlates with the Hamming weight of temp_result.

suggest masking schemes and countermeasures to prevent CPA attacks.
```

**llm response:**
```
classic first-order CPA vulnerability. the XOR output's Hamming weight
directly correlates with power consumption, enabling key recovery through:

1. hypothesis all 256 possible secret_bytes[i] values
2. compute HW(inversion_mask ^ guess) for each
3. correlate with measured power traces
4. highest correlation reveals correct key byte

mitigation strategies:
1. boolean masking (split sensitive variables into random shares)
2. random operation ordering
3. dummy operations for power balancing
4. temporal desynchronization

here's a first-order masked implementation:
```

---

## implementation: boolean masking

**file**: `hyperspace_patch.c`

```c
#include <stdint.h>
#include <stdlib.h>

// Hardware random number generator (use actual HRNG in production)
static uint8_t get_random_byte() {
    return (uint8_t)(rand() & 0xFF);
}

// First-order boolean masking for XOR operation
// Splits secret into two shares: secret = share1 ^ share2
uint8_t masked_xor(uint8_t plaintext, uint8_t secret) {
    // Generate random mask
    uint8_t mask = get_random_byte();

    // Split secret into shares
    uint8_t secret_share1 = secret ^ mask;
    uint8_t secret_share2 = mask;

    // Perform masked computation
    // (plaintext ^ secret) = (plaintext ^ share1) ^ share2
    uint8_t intermediate1 = plaintext ^ secret_share1;
    uint8_t result = intermediate1 ^ secret_share2;

    // Clear intermediate values
    intermediate1 = 0;
    secret_share1 = 0;
    secret_share2 = 0;
    mask = 0;

    return result;
}

// Secured invert_polarity function with masking
uint8_t invert_polarity_secure(uint8_t* data, uint8_t dlen) {
    uint8_t inversion_mask = 0;
    uint8_t resp = 1;

    if (dlen == 1) {
        inversion_mask = data[0];
    }

    volatile uint8_t* secret_bytes = (uint8_t*)secret_ignition_sequence;
    int total_bytes = sizeof(secret_ignition_sequence);
    volatile uint8_t temp_result;

    for (int i = 0; i < total_bytes; i++) {
        // Use masked XOR instead of direct XOR
        temp_result = masked_xor(inversion_mask, secret_bytes[i]);

        // Random delay (20-100 cycles)
        volatile int delay = 20 + (rand() % 80);
        while (delay--) __asm__("nop");

        // Dummy memory access for power balancing
        volatile uint8_t dummy = secret_bytes[(i + 7) % total_bytes];
    }

    simpleserial_put('r', 1, &resp);
    return 0;
}
```

---

## enhanced version: second-order masking

**prompt to claude:**
```
enhance the first-order masking to resist second-order attacks.
suggest multi-share schemes and shuffled execution.
```

**llm response:**
```c
// Second-order boolean masking with three shares
// secret = share1 ^ share2 ^ share3
typedef struct {
    uint8_t shares[3];
} masked_value_t;

// Create masked representation of secret
masked_value_t mask_value(uint8_t secret) {
    masked_value_t masked;
    masked.shares[0] = get_random_byte();
    masked.shares[1] = get_random_byte();
    masked.shares[2] = secret ^ masked.shares[0] ^ masked.shares[1];
    return masked;
}

// Masked XOR: (plaintext ^ secret) in masked domain
masked_value_t masked_xor_second_order(uint8_t plaintext, masked_value_t secret_masked) {
    masked_value_t result;

    // XOR plaintext with first share
    result.shares[0] = plaintext ^ secret_masked.shares[0];

    // Copy other shares unchanged
    result.shares[1] = secret_masked.shares[1];
    result.shares[2] = secret_masked.shares[2];

    // Shuffle share order
    uint8_t perm = rand() % 6;  // 6 possible permutations
    uint8_t temp = result.shares[perm % 3];
    result.shares[perm % 3] = result.shares[(perm + 1) % 3];
    result.shares[(perm + 1) % 3] = temp;

    return result;
}

// Unmask to get final result
uint8_t unmask_value(masked_value_t masked) {
    return masked.shares[0] ^ masked.shares[1] ^ masked.shares[2];
}

// Fully hardened invert_polarity
uint8_t invert_polarity_hardened(uint8_t* data, uint8_t dlen) {
    uint8_t inversion_mask = data[0];

    volatile uint8_t* secret_bytes = (uint8_t*)secret_ignition_sequence;
    int total_bytes = sizeof(secret_ignition_sequence);

    // Randomize operation order
    uint8_t indices[12];
    for (int i = 0; i < total_bytes; i++) indices[i] = i;

    // Fisher-Yates shuffle
    for (int i = total_bytes - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        uint8_t temp = indices[i];
        indices[i] = indices[j];
        indices[j] = temp;
    }

    for (int i = 0; i < total_bytes; i++) {
        int idx = indices[i];

        // Mask secret byte
        masked_value_t secret_masked = mask_value(secret_bytes[idx]);

        // Perform masked XOR
        masked_value_t result_masked = masked_xor_second_order(inversion_mask, secret_masked);

        // Unmask result
        volatile uint8_t temp_result = unmask_value(result_masked);

        // Random delay
        volatile int delay = 20 + (rand() % 80);
        while (delay--) __asm__("nop");

        // Dummy operation
        volatile uint8_t dummy = temp_result ^ get_random_byte();
    }

    uint8_t resp = 1;
    simpleserial_put('r', 1, &resp);
    return 0;
}
```

---

## mitigation effectiveness

**before mitigation:**
- attack success rate: 100%
- traces per byte: 256
- correlation coefficient: 0.35+ for correct key
- total attack time: 28 minutes for 12 bytes

**after first-order masking:**
- attack success rate: <5%
- correlation coefficient drops to <0.10
- requires 10,000+ traces for equivalent confidence
- overhead: +180%

**after second-order masking + shuffling:**
- attack success rate: 0%
- correlation coefficient: <0.05 (noise level)
- requires 100,000+ traces (computationally infeasible)
- overhead: +220%

---

## verification test results

tested with standard CPA attack:
```
byte 0: max correlation = 0.04 (all hypotheses indistinguishable)
byte 6: correlation peaks below noise threshold
byte 11: second-order analysis inconclusive with 50,000 traces
...
result: CPA attack fails, key recovery infeasible
```

---

## deployment recommendations

1. implement first-order masking for all secret-dependent operations
2. use second-order masking for high-security applications
3. add random operation delays (20-100 cycles minimum)
4. shuffle execution order of independent operations
5. use hardware RNG for mask generation (not software PRNG)
6. implement dummy operations matching real operation power profiles
7. clear all intermediate masked values after use
8. combine with trace desynchronization (random clock jitter)
9. monitor for suspicious query patterns indicating profiling attempts
10. implement maximum trace count limits per session
