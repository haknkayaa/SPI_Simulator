#ifndef SPI_SIMULATOR_DRIVER_H
#define SPI_SIMULATOR_DRIVER_H

#include <linux/cdev.h>
#include <linux/delay.h>
#include <linux/device.h>
#include <linux/fs.h>
#include <linux/gpio.h>
#include <linux/hrtimer.h>
#include <linux/init.h>
#include <linux/interrupt.h>
#include <linux/ioctl.h>
#include <linux/kernel.h>
#include <linux/ktime.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/of_gpio.h>
#include <linux/poll.h>
#include <linux/proc_fs.h>
#include <linux/rtc.h>
#include <linux/sched.h>
#include <linux/seq_file.h>
#include <linux/slab.h>
#include <linux/spi/spi.h>
#include <linux/spi/spidev.h>
#include <linux/string.h>
#include <linux/time.h>
#include <linux/timer.h>
#include <linux/uaccess.h>
#include <linux/version.h>
#include <linux/wait.h>
#include <linux/workqueue.h>


extern struct list_head sequence_list;
extern struct mutex     sequence_mutex;

// Global variables
extern int            major_number;
extern struct class  *spi_class;
extern struct device *spi_device;
extern int            spi_mode;

struct spi_sequence {
    char             received[256];
    char             response[256];
    struct list_head list;
};

// SPI Core Function Prototypes
int     spi_open(struct inode *inode, struct file *file);
int     spi_release(struct inode *inode, struct file *file);
ssize_t spi_read_file(struct file *file, char __user *buffer, size_t len, loff_t *offset);
ssize_t spi_write_file(struct file *file, const char __user *buf, size_t count, loff_t *ppos);

// SPI IOCTL Function Prototypes
long spi_ioctl(struct file *file, unsigned int cmd, unsigned long arg);

// SPI Sequence Management Function Prototypes
int  read_sequence_file(void);
void clear_sequences(void);

#endif // SPI_SIMULATOR_DRIVER_H