obj-m := spi_simulator_driver.o 
spi_simulator_driver-objs := spi_simulator.o spi_core.o spi_ioctl_handle.o spi_sequence_match.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean 