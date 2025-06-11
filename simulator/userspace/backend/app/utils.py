"""
Utility functions for the SPI Simulator backend.
"""
import subprocess
import os
import time
import psutil
from typing import Tuple, Optional

from .config import SUDO_CHECK_TIMEOUT, DEVICE_CHECK_TIMEOUT
from .logger import log_info

def check_sudo_permission() -> bool:
    """Check if the application has sudo permissions."""
    try:
        result = subprocess.run(
            ['sudo', '-n', 'true'],
            capture_output=True,
            timeout=SUDO_CHECK_TIMEOUT
        )
        return result.returncode == 0
    except Exception as e:
        log_info(f"Error checking sudo permission: {e}")
        return False

def check_device_exists(device_path: str) -> bool:
    """Check if a device file exists."""
    log_info(f"[PROCESS] Checking if device exists: {device_path}")
    exists = os.path.exists(device_path)
    log_info(f"[INFO] Device exists: {exists}")
    return exists

def check_port_status(port: int) -> bool:
    """Check if a port is in use."""
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            return True
    return False

def run_command(cmd: list, timeout: Optional[float] = None) -> Tuple[bool, str]:
    """
    Run a shell command and return its result.
    
    Args:
        cmd: List of command and arguments
        timeout: Optional timeout in seconds
        
    Returns:
        Tuple of (success, message)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stderr if result.returncode != 0 else result.stdout
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def wait_for_device(device_path: str, timeout: float = DEVICE_CHECK_TIMEOUT) -> bool:
    """
    Wait for a device file to appear.
    
    Args:
        device_path: Path to the device file
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if device appeared, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(device_path):
            return True
        time.sleep(0.1)
    return False

def set_device_permissions(device_path: str, permissions: str) -> Tuple[bool, str]:
    """
    Set permissions for a device file.
    
    Args:
        device_path: Path to the device file
        permissions: Permission string (e.g., '666')
        
    Returns:
        Tuple of (success, message)
    """
    log_info(f"[PROCESS] Setting permissions for {device_path}...")
    return run_command(['sudo', 'chmod', permissions, device_path])
