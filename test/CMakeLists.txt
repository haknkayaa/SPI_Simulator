cmake_minimum_required(VERSION 3.0)

project(spi_test_driver)

add_executable(spi_test_driver 
    spi_test_driver.c
    linux_spi.c
    linux_spi.h
)