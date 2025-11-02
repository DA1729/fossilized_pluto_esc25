#include <stdint.h>

volatile uint32_t canary = 0xdeadbeef;
volatile uint32_t timing_canary_start = 0;
volatile uint32_t timing_canary_end = 0;

void trigger_fault_detected() {
    __asm__("nop");
    while(1);
}

uint32_t get_cycle_count() {
    return 0;
}

int compute_value(int i) {
    return i * 2;
}

int secure_calculation() {
    uint32_t start_time = get_cycle_count();
    timing_canary_start = 0x12345678;

    int result1 = 0;
    int result2 = 0;
    int result3 = 0;
    volatile int iteration_count = 0;
    volatile uint32_t checksum = 0;

    for (int i = 0; i < 1000; i++) {
        if (canary != 0xdeadbeef || timing_canary_start != 0x12345678) {
            trigger_fault_detected();
            return -1;
        }

        int val = compute_value(i);
        result1 += val;
        result2 += val;
        result3 += val;
        iteration_count++;
        checksum ^= (i * 0x9e3779b1);
    }

    uint32_t end_time = get_cycle_count();
    timing_canary_end = 0x87654321;

    if (!(result1 == result2 && result2 == result3)) {
        trigger_fault_detected();
        return -1;
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

    uint32_t elapsed = end_time - start_time;
    if (elapsed < 950000 || elapsed > 1050000) {
        trigger_fault_detected();
        return -1;
    }

    if (canary != 0xdeadbeef || timing_canary_end != 0x87654321) {
        trigger_fault_detected();
        return -1;
    }

    return result1;
}
