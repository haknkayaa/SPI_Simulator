"""
Configuration settings for the SPI Simulator backend.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DRIVER_PATH = Path('/home/ubuntu/Desktop/SPI_Simulator/build/output/spi_simulator_driver.ko')
SEQUENCE_FILE = Path('/tmp/spi_sequences.json')

# API Configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 5001))
FRONTEND_PORT = int(os.getenv('FRONTEND_PORT', 5173))
CORS_ORIGINS = [f"http://localhost:{FRONTEND_PORT}"]

# Driver Configuration
DEFAULT_DEVICE_NAME = 'spidev0.0'
DRIVER_MODULE_NAME = 'spi_simulator_driver'
DEVICE_PERMISSIONS = '666'

# Logging Configuration
LOG_BUFFER_SIZE = 100
LOG_FORMAT = '%(message)s'

# SPI Configuration
SPI_TIMEOUT = 1.0  # seconds
SPI_READ_CHUNK_SIZE = 1  # bytes

# System Configuration
SUDO_CHECK_TIMEOUT = 5  # seconds
DEVICE_CHECK_TIMEOUT = 1  # seconds

# API Response Messages
MESSAGES = {
    'DRIVER_LOADED': 'Driver loaded successfully',
    'DRIVER_UNLOADED': 'Driver unloaded successfully',
    'DRIVER_NOT_LOADED': 'Driver not loaded',
    'DEVICE_NOT_FOUND': 'SPI device does not exist',
    'PERMISSION_DENIED': 'Permission denied. Try running with sudo.',
    'NO_COMMAND': 'No command provided',
    'TIMEOUT': 'No response received within timeout period',
    'SEQUENCES_UPDATED': 'Sequences updated successfully',
    'LOGS_CLEARED': 'Logs cleared successfully'
}
