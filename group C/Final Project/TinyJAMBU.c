#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "platform.h"
#include "xil_printf.h"
#include "xparameters.h"
#include "xtmrctr.h"
#include "TinyJAMBU.h"  // Include TinyJAMBU headers

#define TIMER_DEVICE_ID XPAR_TMRCTR_0_DEVICE_ID
#define CLOCK_FREQUENCY 100000000 // 100 MHz in Hz
#define DYNAMIC_POWER_MW 1111     // Dynamic power in milliwatts (example value)
#define TAG_SIZE 16  // Authentication tag size
#define AD_SIZE 16   // Associated data size
#define KEY_SIZE 16  // 128-bit key
#define NONCE_SIZE 16 // 128-bit nonce

XTmrCtr TimerInstance;

void init_timer() {
    int status = XTmrCtr_Initialize(&TimerInstance, TIMER_DEVICE_ID);
    if (status != XST_SUCCESS) {
        xil_printf("Timer Initialization Failed!\n\r");
        while (1);
    }
    XTmrCtr_SetOptions(&TimerInstance, 0, XTC_AUTO_RELOAD_OPTION);
}

void read_choice(char *buffer, size_t size) {
    char c;
    size_t i = 0;
    xil_printf("\n\rEnter your choice: ");
    while (i < size - 1) { // Leave space for the null terminator
        c = inbyte(); // Read a character from UART
        if (c == '\r' || c == '\n') {
            buffer[i] = '\0'; // Null-terminate the string
            xil_printf("\n\r"); // Move to the next line in UART
            break;
        }
        buffer[i++] = c;
        outbyte(c); // Echo the character back to UART
    }
    buffer[i] = '\0'; // Ensure the string is null-terminated
}

void print_metrics(const char *operation, u64 cycles, size_t data_size) {
    u64 time_us = (cycles * 1000000) / CLOCK_FREQUENCY;
    u64 throughput_kbps = (data_size * 1000) / time_us; // Kilobytes/sec
    u64 energy_uj = (DYNAMIC_POWER_MW * time_us) / 1000; // Microjoules

    xil_printf("\n\r=== %s Performance Metrics ===\n\r", operation);
    xil_printf("Clock Cycles: %lu\n\r", cycles);
    xil_printf("Execution Time: %lu microseconds\n\r", time_us);
    xil_printf("Throughput: %lu KB/s\n\r", throughput_kbps);
    xil_printf("Estimated Energy: %lu microjoules\n\r", energy_uj);
}

void print_memory_usage(size_t plaintext_len) {
    size_t total_memory = plaintext_len + AD_SIZE + KEY_SIZE + NONCE_SIZE + TAG_SIZE;
    xil_printf("\n\rMemory Usage Breakdown:\n\r");
    xil_printf("Plaintext: %lu bytes\n\r", plaintext_len);
    xil_printf("Ciphertext: %lu bytes\n\r", plaintext_len + TAG_SIZE);
    xil_printf("Associated Data: %lu bytes\n\r", AD_SIZE);
    xil_printf("Key: %lu bytes\n\r", KEY_SIZE);
    xil_printf("Nonce: %lu bytes\n\r", NONCE_SIZE);
    xil_printf("Total Memory Used: %lu bytes\n\r", total_memory);
}

void print_hex_limited(const char *label, const uint8_t *data, size_t length, size_t limit) {
    xil_printf("%s (First %lu bytes): ", label, limit);
    for (size_t i = 0; i < (length > limit ? limit : length); i++) {
        xil_printf("%02x", data[i]);
    }
    xil_printf("...\n\r");
}

void test_case(const char *test_name, uint8_t *plaintext, size_t plaintext_len, uint8_t *associated_data, size_t ad_len,
               uint8_t *key, uint8_t *nonce, int tamper_ciphertext) {
    uint8_t *ciphertext = (uint8_t *)malloc(plaintext_len + TAG_SIZE);
    uint8_t *decrypted_text = (uint8_t *)malloc(plaintext_len);
    if (!ciphertext || !decrypted_text) {
        xil_printf("Memory allocation failed!\n\r");
        return;
    }

    xil_printf("\n\r=== Running Test Case: %s ===\n\r", test_name);

    // Memory Usage
    print_memory_usage(plaintext_len);

    // Encryption
    xil_printf("\n\rEncrypting...\n\r");
    XTmrCtr_Reset(&TimerInstance, 0);
    XTmrCtr_Start(&TimerInstance, 0);

    size_t ciphertext_len = 0;
    tinyjambu_128_aead_encrypt(ciphertext, &ciphertext_len, plaintext, plaintext_len, associated_data, ad_len, nonce, key);

    XTmrCtr_Stop(&TimerInstance, 0);
    u64 encryption_cycles = XTmrCtr_GetValue(&TimerInstance, 0);
    print_metrics("Encryption", encryption_cycles, plaintext_len);

    print_hex_limited("Ciphertext", ciphertext, ciphertext_len, 64);

    // Optionally tamper with ciphertext for security test
    if (tamper_ciphertext) {
        ciphertext[0] ^= 0xFF; // Modify the first byte
        xil_printf("Tampered Ciphertext for Security Test.\n\r");
    }

    // Decryption
    xil_printf("\n\rDecrypting...\n\r");
    XTmrCtr_Reset(&TimerInstance, 0);
    XTmrCtr_Start(&TimerInstance, 0);

    size_t decrypted_len = 0;
    int result = tinyjambu_128_aead_decrypt(decrypted_text, &decrypted_len, ciphertext, ciphertext_len, associated_data, ad_len, nonce, key);

    XTmrCtr_Stop(&TimerInstance, 0);
    u32 decryption_cycles = XTmrCtr_GetValue(&TimerInstance, 0);
    print_metrics("Decryption", decryption_cycles, plaintext_len);

    if (result == 0) {
        print_hex_limited("Decrypted Text", decrypted_text, decrypted_len, 64);
        if (memcmp(plaintext, decrypted_text, plaintext_len) == 0) {
            xil_printf("Test Case PASSED: Decrypted text matches the original plaintext.\n\r");
        } else {
            xil_printf("Test Case FAILED: Decrypted text does not match the original plaintext.\n\r");
        }
    } else {
        xil_printf("Decryption failed: Authentication error.\n\r");
    }

    free(ciphertext);
    free(decrypted_text);
}

void run_test_case(int choice) {
    uint8_t key[KEY_SIZE] = {0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
                             0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};
    uint8_t nonce[NONCE_SIZE] = {0xCA, 0xFE, 0xBA, 0xBE, 0xDE, 0xAD, 0xBE, 0xEF,
                                 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07};
    uint8_t associated_data[AD_SIZE] = "Metadata12345678";

    switch (choice) {
        case 1: {
            uint8_t plaintext[] = "Hello, world!";
            test_case("Functional Test", plaintext, sizeof(plaintext) - 1, associated_data, sizeof(associated_data), key, nonce, 0);
            break;
        }
        case 2: {
            uint8_t plaintext[] = "";
            test_case("Edge Case: Empty Plaintext", plaintext, sizeof(plaintext) - 1, associated_data, sizeof(associated_data), key, nonce, 0);
            break;
        }
        case 3: {
            size_t large_plaintext_len = 1024; // 1 KB
            uint8_t *large_plaintext = (uint8_t *)malloc(large_plaintext_len);
            if (large_plaintext) {
                memset(large_plaintext, 'A', large_plaintext_len);
                test_case("Performance Test: 1 KB Plaintext", large_plaintext, large_plaintext_len, associated_data, sizeof(associated_data), key, nonce, 0);
                free(large_plaintext);
            }
            break;
        }
        case 4: {
            size_t large_plaintext_len = 1024 * 1024; // 1 MB
            uint8_t *large_plaintext = (uint8_t *)malloc(large_plaintext_len);
            if (large_plaintext) {
                memset(large_plaintext, 'A', large_plaintext_len);
                test_case("Performance Test: 1 MB Plaintext", large_plaintext, large_plaintext_len, associated_data, sizeof(associated_data), key, nonce, 0);
                free(large_plaintext);
            }
            break;
        }
        case 5: {
            uint8_t plaintext[] = "Security Test";
            test_case("Security Test: Modified Ciphertext", plaintext, sizeof(plaintext) - 1, associated_data, sizeof(associated_data), key, nonce, 1);
            break;
        }
        default:
            xil_printf("Invalid choice.\n\r");
            break;
    }
}

int main() {
    init_platform();
    init_timer();

    xil_printf("=== TinyJAMBU AEAD Encryption/Decryption Tests ===\n\r");
    xil_printf("Select Test Case:\n\r");
    xil_printf("1. Functional Test\n\r");
    xil_printf("2. Edge Case Test (Empty Plaintext)\n\r");
    xil_printf("3. Performance Test (1 KB Plaintext)\n\r");
    xil_printf("4. Performance Test (1 MB Plaintext)\n\r");
    xil_printf("5. Security Test (Modified Ciphertext)\n\r");

    while (1) {
        char choice_str[10];
        read_choice(choice_str, sizeof(choice_str)); // Use the updated function
        int choice = atoi(choice_str); // Convert input to an integer

        if (choice == 0) {
            xil_printf("Exiting program. Goodbye!\n\r");
            break;
        }

        run_test_case(choice); // Execute the selected test case
    }

    cleanup_platform();
    return 0;
}
