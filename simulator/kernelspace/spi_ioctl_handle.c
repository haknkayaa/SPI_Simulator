#include "spi_simulator.h"

long spi_ioctl(struct file *file, unsigned int cmd, unsigned long arg) {
    printk(KERN_INFO "SPI Simulator: IOCTL command received: %u (0x%x)\n", cmd, cmd);

    u32          mode; // Changed to u32 to match IOCTL definition
    void __user *argp = (void __user *) arg;

    switch (cmd) {
        // IOCTL Write SPI Mode
        case SPI_IOC_WR_MODE: {
            printk(KERN_INFO "SPI Simulator: Setting SPI mode\n");
            if (copy_from_user(&mode, argp, sizeof(mode))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy mode from user\n");
                return -EFAULT;
            }
            if (mode > 3) {
                printk(KERN_ERR "SPI Simulator: Invalid mode value: %u\n", mode);
                return -EINVAL;
            }
            spi_mode = mode;
            printk(KERN_INFO "SPI Simulator: Mode successfully set to %u\n", mode);
            return 0;
        }

        // IOCTL Read SPI Mode
        case SPI_IOC_RD_MODE: {
            printk(KERN_INFO "SPI Simulator: Getting SPI mode\n");
            if (copy_to_user(argp, &spi_mode, sizeof(spi_mode))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy mode to user\n");
                return -EFAULT;
            }
            printk(KERN_INFO "SPI Simulator: Mode successfully read as %d\n", spi_mode);
            return 0;
        }

        // IOCTL Write SPI Bits Per Word
        case SPI_IOC_WR_BITS_PER_WORD: {
            u8 bits;
            printk(KERN_INFO "SPI Simulator: Setting SPI bits per word\n");
            if (copy_from_user(&bits, argp, sizeof(bits))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy bits from user\n");
                return -EFAULT;
            }
            if (bits < 1 || bits > 32) {
                printk(KERN_ERR "SPI Simulator: Invalid bits per word value: %u\n", bits);
                return -EINVAL;
            }
            // Here you would typically set the bits per word in your SPI device
            printk(KERN_INFO "SPI Simulator: Bits per word successfully set to %u\n", bits);
            return 0;
        }
        // IOCTL Read SPI Bits Per Word
        case SPI_IOC_RD_BITS_PER_WORD: {
            u8 bits = 8; // Default bits per word
            printk(KERN_INFO "SPI Simulator: Getting SPI bits per word\n");
            if (copy_to_user(argp, &bits, sizeof(bits))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy bits to user\n");
                return -EFAULT;
            }
            printk(KERN_INFO "SPI Simulator: Bits per word successfully read as %u\n", bits);
            return 0;
        }

        // IOCTL Write SPI Max Speed
        case SPI_IOC_WR_MAX_SPEED_HZ: {
            u32 speed;
            printk(KERN_INFO "SPI Simulator: Setting SPI max speed\n");
            if (copy_from_user(&speed, argp, sizeof(speed))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy speed from user\n");
                return -EFAULT;
            }
            if (speed == 0) {
                printk(KERN_ERR "SPI Simulator: Invalid speed value: %u\n", speed);
                return -EINVAL;
            }
            // Here you would typically set the max speed in your SPI device
            printk(KERN_INFO "SPI Simulator: Max speed successfully set to %u Hz\n", speed);
            return 0;
        }
        // IOCTL Read SPI Max Speed
        case SPI_IOC_RD_MAX_SPEED_HZ: {
            u32 speed = 500000; // Default max speed
            printk(KERN_INFO "SPI Simulator: Getting SPI max speed\n");
            if (copy_to_user(argp, &speed, sizeof(speed))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy speed to user\n");
                return -EFAULT;
            }
            printk(KERN_INFO "SPI Simulator: Max speed successfully read as %u Hz\n", speed);
            return 0;
        }
        // IOCTL Write SPI LSB First
        case SPI_IOC_WR_LSB_FIRST: {
            u8 lsb_first;
            printk(KERN_INFO "SPI Simulator: Setting SPI LSB first\n");
            if (copy_from_user(&lsb_first, argp, sizeof(lsb_first))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy LSB first from user\n");
                return -EFAULT;
            }
            // Here you would typically set the LSB first in your SPI device
            printk(KERN_INFO "SPI Simulator: LSB first successfully set to %u\n", lsb_first);
            return 0;
        }
        // IOCTL Read SPI LSB First
        case SPI_IOC_RD_LSB_FIRST: {
            u8 lsb_first = 0; // Default LSB first
            printk(KERN_INFO "SPI Simulator: Getting SPI LSB first\n");
            if (copy_to_user(argp, &lsb_first, sizeof(lsb_first))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy LSB first to user\n");
                return -EFAULT;
            }
            printk(KERN_INFO "SPI Simulator: LSB first successfully read as %u\n", lsb_first);
            return 0;
        }
        // IOCTL Write SPI Mode 32
        case SPI_IOC_WR_MODE32: {
            u32 mode32;
            printk(KERN_INFO "SPI Simulator: Setting SPI mode 32\n");
            if (copy_from_user(&mode32, argp, sizeof(mode32))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy mode 32 from user\n");
                return -EFAULT;
            }
            if (mode32 > 3) {
                printk(KERN_ERR "SPI Simulator: Invalid mode 32 value: %u\n", mode32);
                return -EINVAL;
            }
            spi_mode = mode32;
            printk(KERN_INFO "SPI Simulator: Mode 32 successfully set to %u\n", mode32);
            return 0;
        }
        // IOCTL Read SPI Mode 32
        case SPI_IOC_RD_MODE32: {
            u32 mode32 = spi_mode; // Use current mode
            printk(KERN_INFO "SPI Simulator: Getting SPI mode 32\n");
            if (copy_to_user(argp, &mode32, sizeof(mode32))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy mode 32 to user\n");
                return -EFAULT;
            }
            printk(KERN_INFO "SPI Simulator: Mode 32 successfully read as %u\n", mode32);
            return 0;
        }


        // IOCTL Read/WriteSPI Message
        case SPI_IOC_MESSAGE(1): {
            struct spi_ioc_transfer transfer;
            printk(KERN_INFO "SPI Simulator: Handling SPI message\n");

            if (copy_from_user(&transfer, argp, sizeof(transfer))) {
                printk(KERN_ERR "SPI Simulator: Failed to copy transfer from user\n");
                return -EFAULT;
            }

            printk(KERN_INFO "SPI Simulator: Transfer details - tx_buf: %llx, rx_buf: %llx, len: %u, speed_hz: %u, "
                             "delay_usecs: %u, bits_per_word: %u\n",
                   (unsigned long long) transfer.tx_buf, (unsigned long long) transfer.rx_buf, transfer.len,
                   transfer.speed_hz, transfer.delay_usecs, transfer.bits_per_word);

            // Check if this is a read or write operation based on tx_buf and rx_buf
            if (transfer.tx_buf && !transfer.rx_buf) {
                printk(KERN_INFO "SPI Simulator: Write operation detected\n");

                // Handle write operation
                if (transfer.len > 0 && transfer.tx_buf) {
                    u8 *tx_buf = kmalloc(transfer.len, GFP_KERNEL);
                    if (!tx_buf) {
                        return -ENOMEM;
                    }

                    if (copy_from_user(tx_buf, (const void __user *) transfer.tx_buf, transfer.len)) {
                        kfree(tx_buf);
                        return -EFAULT;
                    }

                    // Process the write data
                    printk(KERN_INFO "SPI Simulator: Writing %d bytes\n", transfer.len);
                    printk(KERN_INFO "SPI Simulator: Data: ");
                    for (unsigned int i = 0; i < transfer.len; i++) {
                        printk(KERN_CONT "0x%02x ", tx_buf[i]);
                    }
                    printk(KERN_CONT "\n");

                    kfree(tx_buf);
                }
            } else if (!transfer.tx_buf && transfer.rx_buf) {
                printk(KERN_INFO "SPI Simulator: Read operation detected\n");
                // Handle read operation
                if (transfer.len > 0 && transfer.rx_buf) {
                    u8 *rx_buf = kmalloc(transfer.len, GFP_KERNEL);
                    if (!rx_buf) {
                        return -ENOMEM;
                    }

                    // Simulate reading data (fill with dummy data)
                    memset(rx_buf, 0xAA, transfer.len);

                    if (copy_to_user((void __user *) transfer.rx_buf, rx_buf, transfer.len)) {
                        kfree(rx_buf);
                        return -EFAULT;
                    }

                    printk(KERN_INFO "SPI Simulator: Reading %d bytes\n", transfer.len);
                    printk(KERN_INFO "SPI Simulator: Data: ");
                    for (unsigned int i = 0; i < transfer.len; i++) {
                        printk(KERN_CONT "0x%02x ", rx_buf[i]);
                    }
                    printk(KERN_CONT "\n");

                    kfree(rx_buf);
                }
            } else if (transfer.tx_buf && transfer.rx_buf) {
                printk(KERN_INFO "SPI Simulator: Full-duplex operation detected\n");

                // Handle full-duplex operation
                if (transfer.len > 0 && transfer.tx_buf) {
                    // Validate transfer length
                    if (transfer.len > 256) {
                        printk(KERN_ERR "SPI Simulator: Transfer length too large: %u\n", transfer.len);
                        return -EINVAL;
                    }

                    // Calculate actual tx buffer size by finding first null byte
                    __u32 actual_len = 0;
                    u8   *temp_buf   = kmalloc(transfer.len, GFP_KERNEL);
                    if (!temp_buf) {
                        return -ENOMEM;
                    }

                    if (copy_from_user(temp_buf, (const void __user *) transfer.tx_buf, transfer.len)) {
                        kfree(temp_buf);
                        return -EFAULT;
                    }

                    // Find actual length by looking for first null byte or non-zero byte
                    while (actual_len < transfer.len && temp_buf[actual_len] != 0) {
                        actual_len++;
                    }
                    kfree(temp_buf);

                    printk(KERN_INFO "SPI Simulator: Transfer length: %u, Actual length: %u\n", transfer.len,
                           actual_len);

                    // Validate actual length
                    if (actual_len == 0) {
                        printk(KERN_ERR "SPI Simulator: No valid data found in transfer\n");
                        return -EINVAL;
                    }

                    // Allocate buffer for actual data
                    u8 *tx_buf = kmalloc(actual_len, GFP_KERNEL);
                    if (!tx_buf) {
                        return -ENOMEM;
                    }

                    if (copy_from_user(tx_buf, (const void __user *) transfer.tx_buf, actual_len)) {
                        kfree(tx_buf);
                        return -EFAULT;
                    }

                    // Convert tx_buf to string for sequence matching
                    char cmd[256] = {0};
                    int  i;
                    for (i = 0; i < actual_len && i < sizeof(cmd) - 1; i++) {
                        snprintf(cmd + (i * 3), 4, "%02X ", tx_buf[i]);
                    }
                    if (i > 0) {
                        cmd[(i * 3) - 1] = '\0'; // Remove trailing space
                    }

                    printk(KERN_INFO "SPI Simulator: Received command: %s\n", cmd);

                    // Search in sequence list
                    struct spi_sequence *seq;
                    bool                 found         = false;
                    char                 response[256] = {0};

                    printk(KERN_INFO "SPI Simulator: Searching for sequence match...\n");
                    printk(KERN_INFO "SPI Simulator: Looking for command: '%s'\n", cmd);

                    mutex_lock(&sequence_mutex);
                    list_for_each_entry(seq, &sequence_list, list) {
                        printk(KERN_INFO "SPI Simulator: Comparing with sequence - Received: '%s', Response: '%s'\n",
                               seq->received, seq->response);

                        // Trim whitespace and convert to uppercase for case-insensitive comparison
                        char trimmed_cmd[256]      = {0};
                        char trimmed_received[256] = {0};
                        int  i, j;

                        // Trim and convert cmd to uppercase
                        for (i = 0, j = 0; cmd[i]; i++) {
                            if (cmd[i] != ' ') {
                                trimmed_cmd[j] = toupper(cmd[i]);
                                j++;
                            }
                        }
                        trimmed_cmd[j] = '\0';

                        // Trim and convert received to uppercase
                        for (i = 0, j = 0; seq->received[i]; i++) {
                            if (seq->received[i] != ' ') {
                                trimmed_received[j] = toupper(seq->received[i]);
                                j++;
                            }
                        }
                        trimmed_received[j] = '\0';

                        printk(KERN_INFO
                               "SPI Simulator: Trimmed and uppercase comparison - Command: '%s', Sequence: '%s'\n",
                               trimmed_cmd, trimmed_received);

                        if (strcmp(trimmed_cmd, trimmed_received) == 0) {
                            strncpy(response, seq->response, sizeof(response) - 1);
                            found = true;
                            printk(KERN_INFO "SPI Simulator: Found matching sequence!\n");
                            break;
                        }
                    }
                    mutex_unlock(&sequence_mutex);

                    if (!found) {
                        // Default response if no sequence matches
                        snprintf(response, sizeof(response), "Unknown command: %s", cmd);
                        printk(KERN_INFO "SPI Simulator: No matching sequence found\n");
                    }

                    // Convert response string to bytes
                    u8 *rx_buf = kmalloc(transfer.len, GFP_KERNEL);
                    if (!rx_buf) {
                        kfree(tx_buf);
                        return -EFAULT;
                    }

                    // Initialize rx_buf with zeros
                    memset(rx_buf, 0, transfer.len);

                    if (found) {
                        // Parse hex string to bytes using kernel functions
                        char *ptr = response;
                        int   idx = 0;

                        printk(KERN_INFO "SPI Simulator: Converting response: '%s'\n", response);

                        while (*ptr && idx < actual_len) {
                            char hex[3] = {0};
                            int  i      = 0;

                            // Skip spaces
                            while (*ptr && *ptr == ' ')
                                ptr++;
                            if (!*ptr)
                                break;

                            // Get next two characters
                            while (*ptr && *ptr != ' ' && i < 2) {
                                hex[i++] = *ptr++;
                            }

                            // Convert hex to byte
                            long val;
                            if (kstrtol(hex, 16, &val) == 0) {
                                rx_buf[idx++] = (u8) val;
                                printk(KERN_INFO "SPI Simulator: Converted hex '%s' to byte 0x%02X\n", hex, (u8) val);
                            }
                        }
                    }

                    // Log the final response buffer
                    printk(KERN_INFO "SPI Simulator: Final response buffer (length %u): ", transfer.len);
                    for (int i = 0; i < transfer.len; i++) {
                        printk(KERN_CONT "0x%02X ", rx_buf[i]);
                    }
                    printk(KERN_CONT "\n");

                    printk(KERN_INFO "SPI Simulator: About to copy %u bytes to user buffer at %llx\n", transfer.len,
                           (unsigned long long) transfer.rx_buf);

                    // Copy response to user buffer
                    if (copy_to_user((void __user *) transfer.rx_buf, rx_buf, transfer.len)) {
                        printk(KERN_ERR "SPI Simulator: Failed to copy response to user buffer\n");
                        kfree(tx_buf);
                        kfree(rx_buf);
                        return -EFAULT;
                    }

                    printk(KERN_INFO "SPI Simulator: Successfully copied response to user buffer\n");

                    kfree(tx_buf);
                    kfree(rx_buf);
                    return actual_len; // Return actual length instead of transfer length
                }
            }

            printk(KERN_INFO "SPI Simulator: SPI transfer completed with length %u\n", transfer.len);
            return 0;
        }

        default:
            printk(KERN_ERR "SPI Simulator: Invalid IOCTL command.\n");
            return -ENOTTY;
    }
}
