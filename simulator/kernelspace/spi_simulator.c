#include "spi_simulator.h"
#include <linux/module.h>
#include <linux/init.h>

// Global variables
LIST_HEAD(sequence_list);
DEFINE_MUTEX(sequence_mutex);

int            major_number;
struct class  *spi_class  = NULL;
struct device *spi_device = NULL;
int            spi_mode   = 0; // Current SPI mode

// Module parameters
static char *device_name = "spi_test";
module_param(device_name, charp, S_IRUGO | S_IWUSR);
MODULE_PARM_DESC(device_name, "SPI device name");

static int bus_num = 0;
module_param(bus_num, int, S_IRUGO);
MODULE_PARM_DESC(bus_num, "SPI bus number");

static int cs_num = 0;
module_param(cs_num, int, S_IRUGO);
MODULE_PARM_DESC(cs_num, "SPI chip select number");


static struct file_operations fops = {
        .open           = spi_open, // Open the device
        .read           = spi_read_file, // Read from the device
        .write          = spi_write_file, // Write to the device
        .release        = spi_release, // Release the device
        .unlocked_ioctl = spi_ioctl, // Handle IOCTL commands
        .owner          = THIS_MODULE,
};


static int __init spi_init(void) {
    int ret;

    printk(KERN_INFO "SPI Simulator:-----------------------------------------------------------------\n");
    printk(KERN_INFO "SPI Simulator: Initializing the SPI Test Driver\n");

    // Register the major number
    major_number = register_chrdev(0, device_name, &fops);
    if (major_number < 0) {
        printk(KERN_ALERT "SPI Simulator: Failed to register major number\n");
        return major_number;
    }

    // Register the device class
    spi_class = class_create(device_name);
    if (IS_ERR(spi_class)) {
        unregister_chrdev(major_number, device_name);
        printk(KERN_ALERT "SPI Simulator: Failed to register device class\n");
        return PTR_ERR(spi_class);
    }

    // Register the device driver
    spi_device = device_create(spi_class, NULL, MKDEV(major_number, 0), NULL, device_name);
    if (IS_ERR(spi_device)) {
        class_destroy(spi_class);
        unregister_chrdev(major_number, device_name);
        printk(KERN_ALERT "SPI Simulator: Failed to create the device\n");
        return PTR_ERR(spi_device);
    }

    // Sequence dosyasını oku
    ret = read_sequence_file();
    if (ret) {
        printk(KERN_WARNING "SPI Simulator: Failed to read sequence file: %d\n", ret);
    }

    printk(KERN_INFO "SPI Simulator: Device initialized with major number %d and name %s\n", major_number, device_name);
    return 0;
}

static void __exit spi_exit(void) {
    // Sequence listesini temizle
    clear_sequences();

    device_destroy(spi_class, MKDEV(major_number, 0));
    class_destroy(spi_class);
    unregister_chrdev(major_number, device_name);
    printk(KERN_INFO "SPI Simulator: Device unloaded!\n");
    printk(KERN_INFO "SPI Simulator:-----------------------------------------------------------------\n");
}

module_init(spi_init);
module_exit(spi_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Hakan Kaya");
MODULE_DESCRIPTION("SPI Simulator Driver");
MODULE_VERSION("0.1");