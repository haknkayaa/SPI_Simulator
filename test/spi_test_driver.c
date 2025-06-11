#include "linux_spi.h"
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

static volatile int g_app_running = 1; // Global variable to control the application loop

void sigint_handler(int sig_num) {
    printf("\n[APP] SIGINT received, shutting down...\n");
    g_app_running = 0;
}

void print_usage(const char *program_name) {
    printf("Usage: %s [device_name]\n", program_name);
    printf("  device_name: Path to SPI device (default: /dev/spi_test)\n");
}

int main(int argc, char **argv) {
    printf("-----------------------------------------------------------------\n");
    printf("SPI Test Driver Simulator\n");
    printf("-----------------------------------------------------------------\n");
    printf("This is a simple test program for the SPI Test Driver.\n");
    printf("It simulates the basic operations of opening, reading, writing, and closing the SPI device.\n");

    signal(SIGINT, sigint_handler); // Ignore SIGINT to prevent termination

    // Default device path
    const char *device_path = "/dev/spi_test";

    // Parse command line arguments
    if (argc > 1) {
        if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        }
        device_path = argv[1];
    }

    printf("[APP] Opening the SPI device: %s\n", device_path);
    spi_config_t spi_config;
    spi_config.device    = (char *) device_path; // Use the provided device path
    spi_config.mode      = SPI_MODE_0; // Set SPI mode
    spi_config.bits      = 8; // Set bits per word
    spi_config.speed     = 500000; // Set SPI speed (500 kHz)
    spi_config.delay     = 0; // No delay
    spi_config.lsb       = 0; // Not using LSB first
    spi_config.spidev_fd = -1; // Initialize file descriptor

    if (spi_init(&spi_config) < 0) {
        printf("    Error! Failed to initialize SPI device.\n");
        return -1;
    }

    printf("[APP] SPI device opened successfully.\n");

    while (g_app_running) {
        // -----------------------------------------------------------------------------------
        // RAW WRITE
        // -----------------------------------------------------------------------------------
        // printf("[+] Writing data from SPI device...\n");
        // uint8_t write_buffer[0x10] = {0x01, 0x02, 0x03, 0x04, 0x05,
        //                               0x06, 0x07, 0x08, 0x09, 0x0A}; // Example data to write
        // if (spi_write(&spi_config, write_buffer, 10) < 0) {
        //     printf("Failed to write data to SPI device.\n");
        //     spi_deinit(&spi_config);
        //     return -1;
        // }
        // printf("    Data written successfully.\n");

        // -----------------------------------------------------------------------------------
        // RAW READ
        // -----------------------------------------------------------------------------------
        // printf("[+] Reading data from SPI device...\n");
        // uint8_t read_buffer[10]; // Buffer to hold read data
        // if (spi_read(&spi_config, read_buffer, 10) < 0) {
        //     printf("    Error! Failed to read data from SPI device.\n");
        //     spi_deinit(&spi_config);
        //     return -1;
        // }
        // printf("    Data read successfully.\n");

        // printf("    Received data: ");
        // for (size_t i = 0; i < 10; i++) {
        //     printf("0x%02X ", read_buffer[i]);
        // }
        // printf("\n");


        // ------------------------------------------------------------------------------------
        // TRANSFER
        // ------------------------------------------------------------------------------------
        printf("[+] Performing SPI transfer...\n");
        uint8_t transfer_tx_buffer[2] = {0xAA, 0xAA}; // Example data to transfer
        uint8_t transfer_rx_buffer[2] = {0}; // Buffer to hold received data
        if (spi_transfer(&spi_config, transfer_tx_buffer, 2, transfer_rx_buffer, 2) < 0) {
            printf("    Error! Failed to perform SPI transfer.\n");
            spi_deinit(&spi_config);
            return -1;
        }
        printf("    SPI transfer completed successfully.\n");
        printf("    Received data: ");
        for (size_t i = 0; i < 2; i++) {
            printf("0x%02X ", transfer_rx_buffer[i]);
        }
        printf("\n");
        // ------------------------------------------------------------------------------------

        // Sequence tests
        printf("[+] Running sequence tests...\n");


        usleep(1000000); // Sleep for 1 second to simulate periodic operations

        printf("\n\n\n");
    }


    printf("[APP] Closing the SPI device...\n");
    if (spi_deinit(&spi_config) < 0) {
        printf("    Error! Failed to close SPI device.\n");
        return -1;
    }
    printf("[APP] SPI device closed successfully.\n");
    printf("[APP] SPI Test Driver Simulator finished.\n");

    return 0;
}