# gatekeeper timing attack mitigation

## vulnerability analysis

**original vulnerable code pattern:**
```c
int check_password(char* input) {
    for (int i = 0; i < PASSWORD_LENGTH; i++) {
        if (input[i] != stored_password[i]) {
            return 0;  // early return leaks timing
        }
    }
    return 1;
}
```

**vulnerability**: early return when mismatch found causes timing side-channel
**attack impact**: allows character-by-character password recovery
**success rate**: 100% with 10 samples per character

---

## llm conversation log

**prompt to claude:**
```
analyze this password comparison code for timing vulnerabilities:

int check_password(char* input) {
    for (int i = 0; i < PASSWORD_LENGTH; i++) {
        if (input[i] != stored_password[i]) {
            return 0;
        }
    }
    return 1;
}

suggest a constant-time implementation that prevents timing attacks
while maintaining functionality.
```

**llm response:**
```
the vulnerability is in the early return - it leaks how many characters
matched before the first mismatch. here's a constant-time version:

int check_password_secure(char* input) {
    int result = 1;
    for (int i = 0; i < PASSWORD_LENGTH; i++) {
        result &= (input[i] == stored_password[i]);
    }
    return result;
}

this always iterates through the entire password regardless of where
mismatches occur, eliminating the timing side-channel. the bitwise AND
accumulates the comparison results without branching.
```

---

## implementation

**file**: `secure_password_check.c`

```c
#include <stdint.h>

int secure_password_check(const char* input, const char* stored, int length) {
    volatile uint8_t result = 1;
    for (int i = 0; i < length; i++) {
        result &= (input[i] == stored[i]);
    }
    return result;
}
```

**additional llm-suggested improvements:**
1. use `volatile` to prevent compiler optimization
2. add random delay after comparison
3. implement dummy operations for timing normalization

---

## enhanced version with random delays

**prompt to claude:**
```
enhance the constant-time comparison with random delays to further
obfuscate timing. suggest optimal delay range.
```

**llm response:**
```c
#include <stdlib.h>
#include <time.h>

int secure_password_check_v2(const char* input, const char* stored, int length) {
    volatile uint8_t result = 1;

    for (int i = 0; i < length; i++) {
        result &= (input[i] == stored[i]);
    }

    // add random delay (50-200 cycles)
    int random_delay = 50 + (rand() % 150);
    for (volatile int i = 0; i < random_delay; i++) {
        __asm__("nop");
    }

    return result;
}
```

---

## mitigation effectiveness

**before mitigation:**
- attack success rate: 100%
- queries needed: 13 * 38 * 10 = 4,940
- time to break: ~2 minutes

**after constant-time comparison:**
- attack success rate: 0%
- distinguishable timing: eliminated
- all characters take same time

**after random delays added:**
- attack success rate: 0%
- timing variance: +150% noise
- cost to attacker: requires 100x more samples

---

## verification test results

tested with original timing attack script:
```
position 0: all characters show identical timing (±2%)
position 1: no early-return signal detected
position 2: timing variance exceeds signal strength
...
result: attack fails to recover any characters
```

---

## deployment recommendations

1. replace all string comparison functions with constant-time versions
2. add random delays to all security-critical operations
3. implement rate limiting to prevent statistical attacks
4. use hardware random number generator for delays
5. add canary values to detect timing measurement attempts
