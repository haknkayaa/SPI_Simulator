#ifndef LINUX_SPI_H
#define LINUX_SPI_H

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>


// SPI Variables
typedef struct {
    int      spidev_fd;
    uint8_t  mode;
    uint8_t  bits;
    uint32_t speed;
    uint16_t delay;
    uint32_t lsb;
    char     *device;
} spi_config_t;

//---------------------------------------------------------------------------
// Open/Close Functions
//---------------------------------------------------------------------------
int spi_init(spi_config_t *self);
int spi_deinit(spi_config_t *self);

//---------------------------------------------------------------------------
// Config Functions
//---------------------------------------------------------------------------
int spi_set_mode(spi_config_t *self, uint8_t mode);
int spi_set_bits_per_word(spi_config_t *self, uint8_t bits);
int spi_set_speed(spi_config_t *self, uint32_t speed);
int spi_set_lsb(spi_config_t *self, uint32_t lsb);

//---------------------------------------------------------------------------
// Read/Write functions
//---------------------------------------------------------------------------
int spi_write(spi_config_t *self, uint8_t *buffer, uint16_t length);
int spi_read(spi_config_t *self, uint8_t *buffer, uint16_t length);
int spi_transfer(spi_config_t *self, const uint8_t *tx_buffer, uint16_t tx_length, uint8_t *rx_buffer, uint16_t rx_length);

#endif //LINUX_SPI_H