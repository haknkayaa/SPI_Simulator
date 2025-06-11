cmake_minimum_required(VERSION 3.10)
project(spi_simulator_driver)

# Get kernel version and build directory
execute_process(
    COMMAND uname -r
    OUTPUT_VARIABLE KERNEL_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Set kernel build directory
set(KERNEL_BUILD_DIR "/lib/modules/${KERNEL_VERSION}/build")

# Set build directories
set(BUILD_DIR ${CMAKE_BINARY_DIR}/kernel_build)
set(OUTPUT_DIR ${CMAKE_BINARY_DIR}/output)

# Add kernel module clean target
add_custom_target(kernel_cleanup
    COMMAND ${CMAKE_COMMAND} -E make_directory ${BUILD_DIR}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUTPUT_DIR}
    # Bu satırı kaldırıyoruz:
    # COMMAND make -C ${KERNEL_BUILD_DIR} M=${BUILD_DIR} clean
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${OUTPUT_DIR}
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${BUILD_DIR}
)


# Add kernel module build target
add_custom_target(kernel_module ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory ${BUILD_DIR}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OUTPUT_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy 
        ${CMAKE_CURRENT_SOURCE_DIR}/Makefile
        ${CMAKE_CURRENT_SOURCE_DIR}/spi_simulator.c
        ${CMAKE_CURRENT_SOURCE_DIR}/spi_simulator.h
        ${CMAKE_CURRENT_SOURCE_DIR}/spi_core.c
        ${CMAKE_CURRENT_SOURCE_DIR}/spi_ioctl_handle.c
        ${CMAKE_CURRENT_SOURCE_DIR}/spi_sequence_match.c
        ${BUILD_DIR}/
    COMMAND make -C ${KERNEL_BUILD_DIR} M=${BUILD_DIR} modules
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${BUILD_DIR}/spi_simulator_driver.ko
        ${OUTPUT_DIR}/
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    DEPENDS kernel_cleanup
)