#include "spi_simulator.h"

int spi_open(struct inode *inode, struct file *file) {
    printk(KERN_INFO "SPI Simulator: Device opened\n");
    return 0;
}

int spi_release(struct inode *inode, struct file *file) {
    printk(KERN_INFO "SPI Simulator: Device closed\n");
    return 0;
}

ssize_t spi_read_file(struct file *file, char __user *buffer, size_t len, loff_t *offset) {
    printk(KERN_INFO "SPI Simulator: Read operation\n");
    return 0;
}

ssize_t spi_write_file(struct file *file, const char __user *buf, size_t count, loff_t *ppos) {
    char                 cmd[256];
    char                 response[256] = {0};
    struct spi_sequence *seq;
    bool                 found = false;

    printk(KERN_INFO "SPI Simulator: Write operation\n");

    if (count >= sizeof(cmd))
        return -EINVAL;

    if (copy_from_user(cmd, buf, count))
        return -EFAULT;

    cmd[count] = '\0';

    // Sequence listesinde ara
    mutex_lock(&sequence_mutex);
    list_for_each_entry(seq, &sequence_list, list) {
        if (strcmp(seq->received, cmd) == 0) {
            strncpy(response, seq->response, sizeof(response) - 1);
            found = true;
            break;
        }
    }
    mutex_unlock(&sequence_mutex);

    if (!found) {
        // Varsayılan yanıt
        snprintf(response, sizeof(response), "Unknown command: %s", cmd);
    }

    // Yanıtı kullanıcıya gönder
    if (copy_to_user((void __user *) buf, response, strlen(response) + 1))
        return -EFAULT;

    return strlen(response) + 1;
}
