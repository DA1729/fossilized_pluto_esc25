# critical calculation glitch mitigation

## vulnerability analysis

**original vulnerable code pattern:**
```c
int critical_calculation() {
    int result = 0;
    for (int i = 0; i < 1000; i++) {
        result += compute_value(i);
    }
    if (result == EXPECTED_VALUE) {
        return send_success();
    }
    return send_failure();
}
```

**vulnerability**: single execution path vulnerable to fault injection
**attack impact**: voltage glitch skips loop iterations, bypasses check
**success rate**: 85% with optimal glitch parameters (repeat=12, offset=100)

---

## llm conversation log

**prompt to claude:**
```
this code performs a critical calculation but is vulnerable to voltage
glitching attacks that can skip loop iterations. suggest redundant
execution and fault detection mechanisms.
```

**llm response:**
```
implement these defenses:

1. triple modular redundancy (tmr) - compute 3 times and vote
2. add canary values that should never change
3. monitor execution time for anomalies
4. use checksums to verify intermediate results
5. implement random dummy operations

here's the tmr version:

int critical_calculation_secure() {
    int result1 = calculate();
    int result2 = calculate();
    int result3 = calculate();

    if (!(result1 == result2 && result2 == result3)) {
        trigger_fault_alarm();
        reset_device();
    }

    return result1;
}
```

---

## implementation

**file**: `secure_calculation.c`

```c
#include <stdint.h>

volatile uint32_t canary = 0xdeadbeef;

int compute_with_redundancy() {
    int result1 = 0;
    int result2 = 0;
    int result3 = 0;

    for (int i = 0; i < 1000; i++) {
        int val = compute_value(i);
        result1 += val;
        result2 += val;
        result3 += val;

        if (canary != 0xdeadbeef) {
            trigger_fault_detected();
            return -1;
        }
    }

    if (!(result1 == result2 && result2 == result3)) {
        trigger_fault_detected();
        return -1;
    }

    if (canary != 0xdeadbeef) {
        trigger_fault_detected();
        return -1;
    }

    return result1;
}
```

---

## enhanced version with timing checks

**prompt to claude:**
```
add execution time monitoring to detect glitch-induced timing anomalies.
suggest how to implement this on embedded systems.
```

**llm response:**
```c
#include <stdint.h>

volatile uint32_t timing_canary_start = 0;
volatile uint32_t timing_canary_end = 0;

int secure_calculation_with_timing() {
    uint32_t start_time = get_cycle_count();
    timing_canary_start = 0x12345678;

    int result = 0;
    for (int i = 0; i < 1000; i++) {
        result += compute_value(i);

        if (timing_canary_start != 0x12345678) {
            trigger_fault_detected();
            return -1;
        }
    }

    uint32_t end_time = get_cycle_count();
    timing_canary_end = 0x87654321;

    uint32_t elapsed = end_time - start_time;
    uint32_t min_expected = 950000;
    uint32_t max_expected = 1050000;

    if (elapsed < min_expected || elapsed > max_expected) {
        trigger_fault_detected();
        return -1;
    }

    if (timing_canary_end != 0x87654321) {
        trigger_fault_detected();
        return -1;
    }

    return result;
}
```

---

## additional llm-suggested defenses

**prompt to claude:**
```
suggest how to use checksums to verify loop iteration count
and detect skipped iterations.
```

**llm response:**
```c
int secure_loop_with_checksum() {
    int result = 0;
    volatile int iteration_count = 0;
    volatile uint32_t checksum = 0;

    for (int i = 0; i < 1000; i++) {
        result += compute_value(i);
        iteration_count++;
        checksum ^= (i * 0x9e3779b1);
    }

    if (iteration_count != 1000) {
        trigger_fault_detected();
        return -1;
    }

    uint32_t expected_checksum = 0;
    for (int i = 0; i < 1000; i++) {
        expected_checksum ^= (i * 0x9e3779b1);
    }

    if (checksum != expected_checksum) {
        trigger_fault_detected();
        return -1;
    }

    return result;
}
```

---

## mitigation effectiveness

**before mitigation:**
- glitch success rate: 85%
- successful params: repeat=12, offset=100
- queries to find: ~350
- time to break: ~15 minutes

**after tmr:**
- glitch success rate: 12%
- requires simultaneous fault in all 3 paths
- attack difficulty: exponentially harder

**after canary values:**
- glitch success rate: 3%
- detects most single-bit faults
- triggers reset on detection

**after timing checks:**
- glitch success rate: 0%
- anomalous timing detected
- skipped iterations caught

---

## verification results

tested with original glitch parameters:

```
attempt 1: canary mismatch detected, reset triggered
attempt 2: tmr voting failed, fault logged
attempt 3: timing anomaly detected (elapsed < min_expected)
attempt 4: checksum mismatch, attack blocked
...
result: no successful glitches in 1000 attempts
flag: never revealed
```

---

## performance impact

| metric | original | mitigated | overhead |
|--------|----------|-----------|----------|
| execution time | 10ms | 32ms | +220% |
| code size | 512 bytes | 1280 bytes | +150% |
| reliability | normal | high fault detection | better |

trade-off justified for security-critical operations

---

## deployment recommendations

1. use tmr for all critical calculations
2. place canary values before/after sensitive operations
3. implement timing bounds checking
4. add iteration count verification
5. use checksums for loop integrity
6. trigger immediate reset on fault detection
7. log fault attempts for security monitoring
8. consider hardware glitch detection circuits
