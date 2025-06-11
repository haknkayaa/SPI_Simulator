#include "linux_spi.h"
#include <fcntl.h>
#include <string.h>


//---------------------------------------------------------------------------
// Open/Close Functions
//---------------------------------------------------------------------------

/// @brief Initialize the SPI device
/// @param device SPI device path
/// @return If the operation is successful, return 0. Otherwise, return -1
int spi_init(spi_config_t *self) {
    self->spidev_fd = open(self->device, O_RDWR);
    if (self->spidev_fd < 0) {
        printf("    Error! Can't open device! (fn: %s)\n", __func__);
        return -1;
    }

    if (spi_set_mode(self, self->mode) < 0) {
        printf("    Error! Can't set mode! (fn: %s)\n", __func__);
        return -1;
    }

    if (spi_set_bits_per_word(self, self->bits) < 0) {
        printf("    Error! Can't set bits per word! (fn: %s)\n", __func__);
        return -1;
    }

    if (spi_set_speed(self, self->speed) < 0) {
        printf("    Error! Can't set max speed! (fn: %s)\n", __func__);
        return -1;
    }

    if (spi_set_lsb(self, self->lsb) < 0) {
        printf("    Error! Can't set 'LSB first'! (fn: %s)\n", __func__);
        return -1;
    }

    printf("\n");
    printf("    Debug information : (fn: %s)\n", __func__);
    printf("    SPI device   : %s\n", self->device);
    printf("    SPI Mode     : %d\n", self->mode);
    printf("    Bits per word: %d\n", self->bits);
    printf("    Max Speed    : %d Hz (%d KHz) (%d Mhz)\n", self->speed, self->speed / 1000, self->speed / 1000000);
    printf("    Done! SPI device and communication okay. (fn: %s)\n", __func__);

    return 0;
}

/// @brief Deinitialize the SPI device
/// @return If the operation is successful, return 0. Otherwise, return -1
int spi_deinit(spi_config_t *self) {
    if (self->spidev_fd < 0) {
        printf("    Error! SPI device is not initialized. (fn: %s)\n", __func__);
        return -1;
    }

    close(self->spidev_fd);
    return 0;
}

//---------------------------------------------------------------------------
// Config Functions
//---------------------------------------------------------------------------

/// @brief Set the SPI mode
/// @param mode SPI mode
/// @return If the operation is successful, return 0. Otherwise, return -1
int spi_set_mode(spi_config_t *self, uint8_t mode) {
    if (self->spidev_fd < 0) {
        printf("    Error! SPI device is not initialized. (fn: %s)\n", __func__);
        return -1;
    }

    if (ioctl(self->spidev_fd, SPI_IOC_WR_MODE, &mode) < 0) {
        printf("    Error! Can't set SPI mode. (fn: %s)\n", __func__);
        return -1;
    }

    return 0;
}

/// @brief Set the bits per word
/// @param bits Bits per word
/// @return If the operation is successful, return 0. Otherwise, return -1
int spi_set_bits_per_word(spi_config_t *self, uint8_t bits) {
    if (self->spidev_fd < 0) {
        printf("    Error! SPI device is not initialized. (fn: %s)\n", __func__);
        return -1;
    }

    if (ioctl(self->spidev_fd, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0) {
        printf("    Error! Can't set bits per word. (fn: %s)\n", __func__);
        return -1;
    }

    return 0;
}

/// @brief Set the SPI speed
/// @param speed SPI speed
/// @return If the operation is successful, return 0. Otherwise, return -1
int spi_set_speed(spi_config_t *self, uint32_t speed) {
    if (self->spidev_fd < 0) {
        printf("    Error! SPI device is not initialized. (fn: %s)\n", __func__);
        return -1;
    }

    if (ioctl(self->spidev_fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed) < 0) {
        printf("    Error! Can't set max speed. (fn: %s)\n", __func__);
        return -1;
    }

    return 0;
}

/// @brief Set the SPI LSB
/// @param lsb LSB
/// @return If the operation is successful, return 0. Otherwise, return -1
int spi_set_lsb(spi_config_t *self, uint32_t lsb) {
    if (self->spidev_fd < 0) {
        printf("    Error! SPI device is not initialized. (fn: %s)\n", __func__);
        return -1;
    }

    if (ioctl(self->spidev_fd, SPI_IOC_WR_LSB_FIRST, &lsb) < 0) {
        printf("    Error! Can't set 'LSB first'. (fn: %s)\n", __func__);
        return -1;
    }

    return 0;
}

//---------------------------------------------------------------------------
// Read/Write functions
//---------------------------------------------------------------------------

/// @brief Write data to the SPI device
/// @param data Data to be written
/// @param size Data size
/// @return If the operation is successful, return 0. Otherwise, return -1
int spi_write(spi_config_t *self, uint8_t *buffer, uint16_t length) {
    if (self->spidev_fd < 0) {
        printf("    Error! SPI device is not initialized. (fn: %s)\n", __func__);
        return -1;
    }

    struct spi_ioc_transfer xfer = {
            .tx_buf           = (unsigned long) buffer,
            .rx_buf           = 0,
            .len              = length,
            .delay_usecs      = 0, // Set 1us for tCPH (> 100ns requirement)
            .cs_change        = 0, // Keep CS asserted
            .word_delay_usecs = 0, // No word delay needed as we meet tDS and tDH
            .speed_hz         = self->speed, // Max 40MHz (tCYC = 25ns) -> Using 20MHz for safety
            .bits_per_word    = self->bits,
    };

    if (ioctl(self->spidev_fd, SPI_IOC_MESSAGE(1), &xfer) < 0) {
        printf("    Error! SPI_IOC_MESSAGE failed. (fn: %s)\n", __func__);
        return -1;
    }

    return 0;
}

/// @brief Read data from the SPI device
/// @param data Data to be read
/// @param size Data size
/// @return If the operation is successful, return 0. Otherwise, return -1
int spi_read(spi_config_t *self, uint8_t *buffer, uint16_t length) {
    if (self->spidev_fd < 0) {
        printf("    Error! SPI device is not initialized. (fn: %s)\n", __func__);
        return -1;
    }

    struct spi_ioc_transfer xfer = {
            .tx_buf           = 0,
            .rx_buf           = (unsigned long) buffer,
            .len              = length,
            .delay_usecs      = 0, // Set 1us for tCPH (> 100ns requirement)
            .cs_change        = 0, // Enable CS control for proper tCES and tCEH timing
            .word_delay_usecs = 0, // No word delay needed as we meet tDS and tDH
            .speed_hz         = self->speed, // Max 40MHz (tCYC = 25ns) -> Using 20MHz for safety
            .bits_per_word    = self->bits,
    };

    if (ioctl(self->spidev_fd, SPI_IOC_MESSAGE(1), &xfer) < 0) {
        printf("    Error! SPI_IOC_MESSAGE failed. (fn: %s)\n", __func__);
        return -1;
    }

    return 0;
}

/// @brief Transfer data to the SPI device
/// @param tx_data Data to be written (can be NULL if only reading)
/// @param rx_data Data to be read (can be NULL if only writing)
/// @param txLength Data size to be written
/// @param rxLength Data size to be read
/// @return If the operation is successful, return 0. Otherwise, return -1
int spi_transfer(spi_config_t *self, const uint8_t *tx_buffer, uint16_t tx_length, uint8_t *rx_buffer,
                 uint16_t rx_length) {
    if (self->spidev_fd < 0) {
        printf("    Error! SPI device is not initialized. (fn: %s)\n", __func__);
        return -1;
    }

    // Tek bir transfer içinde hem write hem read yapıyoruz
    uint16_t total_length   = tx_length + rx_length;
    uint8_t *full_tx_buffer = calloc(total_length, sizeof(uint8_t));
    uint8_t *full_rx_buffer = calloc(total_length, sizeof(uint8_t));

    if (!full_tx_buffer || !full_rx_buffer) {
        printf("    Error! Memory allocation failed. (fn: %s)\n", __func__);
        free(full_tx_buffer);
        free(full_rx_buffer);
        return -1;
    }

    // TX buffer'ı kopyala, geri kalanı 0 (dummy bytes)
    memcpy(full_tx_buffer, tx_buffer, tx_length);

    struct spi_ioc_transfer xfer = {.tx_buf        = (unsigned long) full_tx_buffer,
                                    .rx_buf        = (unsigned long) full_rx_buffer,
                                    .len           = total_length,
                                    .delay_usecs   = 0,
                                    .cs_change     = 0, // Tek CS cycle'da tamamla
                                    .speed_hz      = self->speed,
                                    .bits_per_word = self->bits};

    if (ioctl(self->spidev_fd, SPI_IOC_MESSAGE(1), &xfer) < 0) {
        printf("    Error! SPI_IOC_MESSAGE failed. (fn: %s)\n", __func__);
        free(full_tx_buffer);
        free(full_rx_buffer);
        return -1;
    }

    // RX data'yı kopyala (ilk rx_length byte'ı al)
    memcpy(rx_buffer, full_rx_buffer, rx_length);

    free(full_tx_buffer);
    free(full_rx_buffer);
    return 0;
}
