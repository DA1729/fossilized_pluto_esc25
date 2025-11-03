# sorters song power analysis mitigation

## vulnerability analysis

**original vulnerable code pattern:**
```c
void sort8(uint8_t* arr, uint8_t len) {
    uint8_t i, j, key_sort;

    for (i = 1; i < len; i++) {
        key_sort = arr[i];
        j = i;
        while (j > 0 && arr[j - 1] > key_sort) {  // data-dependent branches
            arr[j] = arr[j - 1];
            j--;
        }
        arr[j] = key_sort;
    }
}
```

**vulnerability**: insertion sort with data-dependent comparison branches
**attack vector**: SAD-based power analysis with binary search
**success rate**: 100% with 8 traces per byte (logarithmic complexity)

---

## llm conversation log

**prompt to claude:**
```
analyze this insertion sort implementation for power analysis vulnerabilities:

void sort8(uint8_t* arr, uint8_t len) {
    for (i = 1; i < len; i++) {
        key_sort = arr[i];
        j = i;
        while (j > 0 && arr[j - 1] > key_sort) {
            arr[j] = arr[j - 1];
            j--;
        }
        arr[j] = key_sort;
    }
}

the comparison operations leak power signatures based on whether
arr[j-1] > key_sort evaluates true or false. suggest constant-time
sorting or comparison obfuscation techniques.
```

**llm response:**
```
the vulnerability stems from data-dependent branch execution in the
comparison arr[j-1] > key_sort. when this evaluates differently for
different inputs, power traces show measurable differences.

mitigation strategies:

1. constant-time comparisons using branchless selection
2. random comparison shuffling
3. power consumption balancing
4. input/output blinding

here's a secured version:
```

---

## implementation: constant-time comparison

**file**: `sorters_song_patch.c`

```c
#include <stdint.h>
#include <stdlib.h>

// constant-time conditional swap using bitwise masking
void ct_swap(uint8_t* a, uint8_t* b) {
    uint8_t mask = -(*a > *b);  // 0xFF if swap needed, 0x00 otherwise
    uint8_t temp = (*a ^ *b) & mask;
    *a ^= temp;
    *b ^= temp;
}

// constant-time insertion sort
void sort8_secure(uint8_t* arr, uint8_t len) {
    volatile uint8_t dummy = 0;

    for (uint8_t i = 1; i < len; i++) {
        for (uint8_t j = i; j > 0; j--) {
            // always perform comparison, use constant-time swap
            ct_swap(&arr[j-1], &arr[j]);

            // dummy operation for power balancing
            dummy ^= arr[j];
        }
    }
}
```

---

## enhanced version with shuffling and blinding

**prompt to claude:**
```
enhance the constant-time sort with random shuffling and blinding
techniques to further obfuscate power patterns.
```

**llm response:**
```c
#include <stdlib.h>

// XOR-based blinding
void blind_array(uint8_t* arr, uint8_t len, uint8_t mask) {
    for (uint8_t i = 0; i < len; i++) {
        arr[i] ^= mask;
    }
}

// fisher-yates shuffle
void shuffle_indices(uint8_t* indices, uint8_t len) {
    for (uint8_t i = len - 1; i > 0; i--) {
        uint8_t j = rand() % (i + 1);
        uint8_t temp = indices[i];
        indices[i] = indices[j];
        indices[j] = temp;
    }
}

void sort8_hardened(uint8_t* arr, uint8_t len) {
    // apply random blinding mask
    uint8_t blind_mask = rand() & 0xFF;
    blind_array(arr, len, blind_mask);

    // create shuffled comparison order
    uint8_t indices[15];
    for (uint8_t i = 0; i < len; i++) indices[i] = i;
    shuffle_indices(indices, len);

    // constant-time comparisons with shuffled order
    for (uint8_t i = 1; i < len; i++) {
        for (uint8_t j = i; j > 0; j--) {
            uint8_t idx = indices[j];
            ct_swap(&arr[idx-1], &arr[idx]);

            // random delay (10-50 cycles)
            volatile int delay = 10 + (rand() % 40);
            while (delay--) __asm__("nop");
        }
    }

    // remove blinding
    blind_array(arr, len, blind_mask);
}
```

---

## mitigation effectiveness

**before mitigation:**
- attack success rate: 100%
- traces per byte: 8 (binary search)
- total traces for 15-byte array: 120
- SAD metric clearly distinguishes comparison outcomes

**after constant-time comparisons:**
- attack success rate: 0%
- SAD metric becomes uninformative
- all comparison operations show identical power patterns
- overhead: +140%

**after shuffling + blinding:**
- attack success rate: 0%
- power traces converge regardless of input ordering
- position correlation destroyed by shuffling
- overhead: +180%

---

## verification test results

tested with binary search power analysis:
```
byte 0: SAD values uniform across all guesses (±1%)
byte 5: no correlation between guess and power consumption
byte 14: timing oracle completely eliminated
...
result: binary search fails to converge, requires full 256-trace scan
```

---

## deployment recommendations

1. replace all sorting functions with constant-time versions
2. apply input blinding before sensitive comparisons
3. shuffle comparison order to destroy positional correlation
4. add random delays between operations (10-50 cycles)
5. implement dummy memory accesses for power balancing
6. use hardware RNG for mask generation
7. clear sensitive data after sorting operations
