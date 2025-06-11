#include <errno.h>
#include <fcntl.h>
#include <linux/spi/spidev.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#define BUFFER_SIZE 1024

void print_usage(const char *program_name) {
    printf("Usage: %s <device> <WRITE> <write_size> <RESPONSE> <response_size>\n", program_name);
    printf("Example: %s /dev/spidev0.0 WRITE 2 RESPONSE 2\n", program_name);
}

int main(int argc, char *argv[]) {
    if (argc != 6) {
        print_usage(argv[0]);
        return 1;
    }

    const char *device_path   = argv[1];
    const char *write_cmd     = argv[2];
    int         write_size    = atoi(argv[3]);
    const char *response_cmd  = argv[4];
    int         response_size = atoi(argv[5]);

    // Validate arguments
    if (strcmp(write_cmd, "WRITE") != 0 || strcmp(response_cmd, "RESPONSE") != 0) {
        printf("Error: Invalid command format. Use WRITE and RESPONSE\n");
        return 1;
    }

    if (write_size <= 0 || response_size <= 0) {
        printf("Error: Size must be positive\n");
        return 1;
    }

    // Open device
    int fd = open(device_path, O_RDWR);
    if (fd < 0) {
        printf("Error: Cannot open device %s: %s\n", device_path, strerror(errno));
        return 1;
    }

    // SPI mode
    uint8_t mode = SPI_MODE_0;
    if (ioctl(fd, SPI_IOC_WR_MODE, &mode) < 0) {
        printf("Error: Cannot set SPI mode: %s\n", strerror(errno));
        close(fd);
        return 1;
    }

    // Bits per word
    uint8_t bits = 8;
    if (ioctl(fd, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0) {
        printf("Error: Cannot set bits per word: %s\n", strerror(errno));
        close(fd);
        return 1;
    }

    // Max speed
    uint32_t speed = 500000; // 500 KHz
    if (ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed) < 0) {
        printf("Error: Cannot set max speed: %s\n", strerror(errno));
        close(fd);
        return 1;
    }

    // Prepare transfer buffers
    uint8_t *tx_buffer = malloc(write_size);
    uint8_t *rx_buffer = malloc(response_size);

    if (!tx_buffer || !rx_buffer) {
        printf("Error: Memory allocation failed\n");
        if (tx_buffer)
            free(tx_buffer);
        if (rx_buffer)
            free(rx_buffer);
        close(fd);
        return 1;
    }

    // Fill tx buffer with test pattern (0xAA)
    for (int i = 0; i < write_size; i++) {
        tx_buffer[i] = 0xAA;
    }

    // Prepare transfer structure
    struct spi_ioc_transfer tr = {
            .tx_buf        = (unsigned long) tx_buffer,
            .rx_buf        = (unsigned long) rx_buffer,
            .len           = write_size,
            .speed_hz      = speed,
            .delay_usecs   = 0,
            .bits_per_word = bits,
    };

    // Perform transfer
    if (ioctl(fd, SPI_IOC_MESSAGE(1), &tr) < 0) {
        printf("Error: SPI transfer failed: %s\n", strerror(errno));
        free(tx_buffer);
        free(rx_buffer);
        close(fd);
        return 1;
    }

    // Print response in hex format
    printf("Response: ");
    for (int i = 0; i < response_size; i++) {
        printf("%02X ", rx_buffer[i]);
    }
    printf("\n");

    // Cleanup
    free(tx_buffer);
    free(rx_buffer);
    close(fd);

    return 0;
}