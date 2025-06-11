"""
System status and monitoring module for the SPI Simulator backend.
"""
from typing import Dict

from .config import API_PORT, FRONTEND_PORT
from .utils import check_port_status
from .driver import driver_manager

def get_system_status() -> Dict:
    """
    Get the status of all system components.
    
    Returns:
        Dictionary containing status of backend, frontend, and driver
    """
    return {
        'backend': {
            'status': check_port_status(API_PORT),
            'port': API_PORT
        },
        'frontend': {
            'status': check_port_status(FRONTEND_PORT),
            'port': FRONTEND_PORT
        },
        'driver': {
            'status': driver_manager.is_loaded(),
            'device': driver_manager.get_device_path()
        }
    }
