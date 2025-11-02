#include <stdint.h>
#include <stdlib.h>

volatile uint8_t secure_password_check(const char* input, const char* stored, int length) {
    volatile uint8_t result = 1;

    for (int i = 0; i < length; i++) {
        result &= (input[i] == stored[i]);
    }

    int random_delay = 50 + (rand() % 150);
    for (volatile int i = 0; i < random_delay; i++) {
        __asm__("nop");
    }

    return result;
}

void process_password_attempt(const char* input, int length) {
    const char* stored_password = "secretpass123";

    uint8_t is_valid = secure_password_check(input, stored_password, length);

    if (is_valid) {
        send_success_response();
    } else {
        send_failure_response();
    }
}
