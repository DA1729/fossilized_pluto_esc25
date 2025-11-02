#include <stdint.h>
#include <stdlib.h>

void shuffle_indices(int* indices, int length) {
    for (int i = length - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        int temp = indices[i];
        indices[i] = indices[j];
        indices[j] = temp;
    }
}

void dummy_operation() {
    volatile uint8_t dummy = 0;
    for (int i = 0; i < (rand() % 20); i++) {
        dummy ^= rand() & 0xff;
    }
}

void process_byte(uint8_t value) {
    volatile uint8_t temp = value;
}

void process_password_secure(uint8_t* password, uint8_t* secret_key, int length) {
    int indices[12];
    for (int i = 0; i < length; i++) {
        indices[i] = i;
    }
    shuffle_indices(indices, length);

    for (int idx = 0; idx < length; idx++) {
        int i = indices[idx];

        uint8_t mask1 = rand() & 0xff;
        uint8_t mask2 = rand() & 0xff;

        uint8_t masked_pw = password[i] ^ mask1;
        uint8_t masked_key = secret_key[i] ^ mask2;

        uint8_t intermediate = (masked_pw ^ mask1) ^ (masked_key ^ mask2);

        int random_delay = 5 + (rand() % 20);
        for (volatile int j = 0; j < random_delay; j++) {
            __asm__("nop");
        }

        process_byte(intermediate);

        if (rand() % 2) {
            dummy_operation();
        }
    }
}

void second_order_masking(uint8_t* password, uint8_t* secret_key, int length) {
    for (int i = 0; i < length; i++) {
        uint8_t mask1 = rand() & 0xff;
        uint8_t mask2 = rand() & 0xff;

        uint8_t share1_pw = password[i] ^ mask1;
        uint8_t share2_pw = mask1;

        uint8_t share1_key = secret_key[i] ^ mask2;
        uint8_t share2_key = mask2;

        uint8_t result_share1 = share1_pw ^ share1_key;
        uint8_t result_share2 = share2_pw ^ share2_key;

        uint8_t final_result = result_share1 ^ result_share2;

        process_byte(final_result);
    }
}
