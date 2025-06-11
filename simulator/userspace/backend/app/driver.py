"""
Driver management module for the SPI Simulator backend.
"""
import os
import json
from typing import List, Dict, Optional, Tuple

from .config import (
    DRIVER_PATH,
    DRIVER_MODULE_NAME,
    DEFAULT_DEVICE_NAME,
    DEVICE_PERMISSIONS,
    SEQUENCE_FILE,
    MESSAGES
)
from .logger import log_info
from .utils import (
    check_sudo_permission,
    check_device_exists,
    run_command,
    wait_for_device,
    set_device_permissions
)

class DriverManager:
    """Manages the SPI simulator kernel driver."""
    
    def __init__(self):
        self.device_name: Optional[str] = None
        self.driver_path = str(DRIVER_PATH)
        self._ensure_driver_path()
    
    def _ensure_driver_path(self) -> None:
        """Ensure the driver file exists."""
        if not os.path.exists(self.driver_path):
            raise FileNotFoundError(f"Driver file not found at {self.driver_path}")
    
    def is_loaded(self) -> bool:
        """Check if the driver is currently loaded."""
        success, output = run_command(['lsmod'])
        return success and DRIVER_MODULE_NAME in output
    
    def get_device_path(self) -> Optional[str]:
        """Get the current device path."""
        return f"/dev/{self.device_name}" if self.device_name else None
    
    def load(self, device_name: str = DEFAULT_DEVICE_NAME, sequences: Optional[List[Dict]] = None) -> Tuple[bool, str]:
        """
        Load the kernel driver with the specified device name.
        
        Args:
            device_name: Name of the device to create
            sequences: Optional list of SPI sequences
            
        Returns:
            Tuple of (success, message)
        """
        try:
            log_info(f"[PROCESS] Starting driver load process for device: {device_name}")
            self.device_name = device_name
            
            # Save sequences if provided
            if sequences and not self._save_sequences(sequences):
                log_info("[WARNING] Failed to save sequences, continuing anyway...")
            
            # Unload existing driver if loaded
            if self.is_loaded():
                log_info("[PROCESS] Unloading existing driver...")
                self.unload()
            
            # Load new driver
            log_info("[PROCESS] Loading new driver...")
            cmd = ['sudo', 'insmod', self.driver_path, f'device_name={device_name}']
            success, message = run_command(cmd)
            
            if not success:
                return False, f"Error loading driver: {message}"
            
            # Wait for device and set permissions
            device_path = self.get_device_path()
            if not wait_for_device(device_path):
                return False, "Device file not created"
            
            success, message = set_device_permissions(device_path, DEVICE_PERMISSIONS)
            if not success:
                return False, f"Error setting device permissions: {message}"
            
            log_info(f"[SUCCESS] Driver loaded successfully with device name: {device_name}")
            return True, MESSAGES['DRIVER_LOADED']
            
        except Exception as e:
            error_msg = f"Unexpected error in load_driver: {str(e)}"
            log_info(f"[ERROR] {error_msg}")
            return False, error_msg
    
    def unload(self) -> Tuple[bool, str]:
        """
        Unload the kernel driver.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            log_info("[PROCESS] Attempting to unload driver...")
            
            if not self.is_loaded():
                log_info("[INFO] Driver is not loaded")
                self.device_name = None
                return True, MESSAGES['DRIVER_UNLOADED']
            
            success, message = run_command(['sudo', 'rmmod', DRIVER_MODULE_NAME])
            if not success:
                return False, f"Error unloading driver: {message}"
            
            self.device_name = None
            log_info("[SUCCESS] Driver unloaded successfully")
            return True, MESSAGES['DRIVER_UNLOADED']
            
        except Exception as e:
            error_msg = f"Unexpected error in unload_driver: {str(e)}"
            log_info(f"[ERROR] {error_msg}")
            return False, error_msg
    
    def _save_sequences(self, sequences: List[Dict]) -> bool:
        """
        Save SPI sequences to file.
        
        Args:
            sequences: List of SPI sequences
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(SEQUENCE_FILE.parent, exist_ok=True)
            
            with open(SEQUENCE_FILE, 'w') as f:
                json.dump(sequences, f, indent=2)
            
            log_info(f"✓ Saved {len(sequences)} sequences to {SEQUENCE_FILE}")
            return True
            
        except Exception as e:
            log_info(f"✗ Error saving sequences: {str(e)}")
            return False

# Create global driver manager instance
driver_manager = DriverManager()
