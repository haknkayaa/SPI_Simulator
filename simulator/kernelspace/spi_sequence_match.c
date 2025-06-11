#include "spi_simulator.h"

int read_sequence_file(void) {
    struct file *fp;
    char        *buf;
    loff_t       pos = 0;
    int          ret = 0;

    // Dosyayı aç
    fp = filp_open("/tmp/spi_sequences.json", O_RDONLY, 0);
    if (IS_ERR(fp)) {
        printk(KERN_ERR "Failed to open sequence file\n");
        return PTR_ERR(fp);
    }

    // Dosya boyutunu al
    struct kstat stat;
    ret = vfs_getattr(&fp->f_path, &stat, STATX_SIZE, AT_STATX_SYNC_AS_STAT);
    if (ret) {
        printk(KERN_ERR "Failed to get file size\n");
        filp_close(fp, NULL);
        return ret;
    }

    // Buffer al
    buf = kzalloc(stat.size + 1, GFP_KERNEL);
    if (!buf) {
        printk(KERN_ERR "Failed to allocate buffer\n");
        filp_close(fp, NULL);
        return -ENOMEM;
    }

    // Dosyayı oku
    ret = kernel_read(fp, buf, stat.size, &pos);
    if (ret < 0) {
        printk(KERN_ERR "Failed to read sequence file\n");
        kfree(buf);
        filp_close(fp, NULL);
        return ret;
    }

    // JSON'ı parse et
    char *ptr = buf;
    while (*ptr) {
        if (strncmp(ptr, "\"received\":", 11) == 0) {
            struct spi_sequence *seq = kzalloc(sizeof(*seq), GFP_KERNEL);
            if (!seq) {
                printk(KERN_ERR "Failed to allocate sequence\n");
                break;
            }

            // Received değerini al
            ptr += 11;
            while (*ptr && *ptr != '"')
                ptr++;
            if (*ptr == '"')
                ptr++;
            int i = 0;
            while (*ptr && *ptr != '"' && i < 255) {
                seq->received[i++] = *ptr++;
            }
            seq->received[i] = '\0';

            // Response değerini al
            while (*ptr && strncmp(ptr, "\"response\":", 11) != 0)
                ptr++;
            if (*ptr) {
                ptr += 11;
                while (*ptr && *ptr != '"')
                    ptr++;
                if (*ptr == '"')
                    ptr++;
                i = 0;
                while (*ptr && *ptr != '"' && i < 255) {
                    seq->response[i++] = *ptr++;
                }
                seq->response[i] = '\0';

                // Sequence'i listeye ekle
                mutex_lock(&sequence_mutex);
                list_add_tail(&seq->list, &sequence_list);
                mutex_unlock(&sequence_mutex);

                printk(KERN_INFO "SPI Simulator: Added sequence: received=%s, response=%s\n", seq->received,
                       seq->response);
            } else {
                kfree(seq);
            }
        }
        ptr++;
    }

    kfree(buf);
    filp_close(fp, NULL);
    return 0;
}

void clear_sequences(void) {
    struct spi_sequence *seq, *tmp;

    mutex_lock(&sequence_mutex);
    list_for_each_entry_safe(seq, tmp, &sequence_list, list) {
        list_del(&seq->list);
        kfree(seq);
    }
    mutex_unlock(&sequence_mutex);
}
