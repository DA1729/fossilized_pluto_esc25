#include <stdint.h>
#include <stdlib.h>

void constant_time_swap(uint16_t* arr, int i, int j) {
    uint16_t mask = -(uint16_t)(arr[i] > arr[j]);
    uint16_t diff = (arr[i] - arr[j]) & mask;
    arr[i] -= diff;
    arr[j] += diff;
}

void shuffle_array(uint16_t* arr, int n) {
    for (int i = n - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        uint16_t temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
}

void secure_bubble_sort(uint16_t* arr, int n) {
    shuffle_array(arr, n);

    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            constant_time_swap(arr, j, j + 1);

            int random_delay = 10 + (rand() % 40);
            for (volatile int k = 0; k < random_delay; k++) {
                __asm__("nop");
            }
        }
    }
}

void blinded_sort(uint16_t* arr, int n) {
    uint16_t mask = rand() & 0xffff;

    for (int i = 0; i < n; i++) {
        arr[i] ^= mask;
    }

    secure_bubble_sort(arr, n);

    for (int i = 0; i < n; i++) {
        arr[i] ^= mask;
    }
}

void process_sort_request(uint16_t* secret_array, int n) {
    blinded_sort(secret_array, n);
    send_response(secret_array, n);
}
