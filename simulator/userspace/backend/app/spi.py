"""
SPI communication module for the SPI Simulator backend.
"""
import os
import time
from typing import List, Optional, Tuple

from .config import SPI_TIMEOUT, SPI_READ_CHUNK_SIZE, MESSAGES
from .logger import log_info
from .utils import check_device_exists

class SPIDevice:
    """Handles SPI device communication."""
    
    def __init__(self, device_path: str):
        self.device_path = device_path
        self._fd: Optional[int] = None
    
    def __enter__(self):
        """Open the device file when entering context."""
        if not check_device_exists(self.device_path):
            raise FileNotFoundError(f"SPI device does not exist: {self.device_path}")
        
        try:
            self._fd = os.open(self.device_path, os.O_RDWR)
            return self
        except PermissionError:
            raise PermissionError(MESSAGES['PERMISSION_DENIED'])
        except Exception as e:
            raise Exception(f"Error opening SPI device: {str(e)}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the device file when exiting context."""
        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception as e:
                log_info(f"Error closing file descriptor: {str(e)}")
    
    def _hex_to_bytes(self, hex_str: str) -> bytes:
        """Convert space-separated hex string to bytes."""
        return bytes([int(x, 16) for x in hex_str.split()])
    
    def _bytes_to_hex(self, data: bytes) -> str:
        """Convert bytes to space-separated hex string."""
        return ' '.join([f'{x:02x}' for x in data])
    
    def send_command(self, command: str) -> Tuple[bool, str, Optional[str]]:
        """
        Send a command to the SPI device and read response.
        
        Args:
            command: Space-separated hex string command
            
        Returns:
            Tuple of (success, message, response)
        """
        if not command:
            return False, MESSAGES['NO_COMMAND'], None
        
        try:
            # Convert command to bytes
            command_bytes = self._hex_to_bytes(command)
            log_info(f'[SPI] Sending command bytes: {command_bytes}')
            
            # Write command
            bytes_written = os.write(self._fd, command_bytes)
            if bytes_written != len(command_bytes):
                log_info(f'[SPI] Warning: Only wrote {bytes_written} of {len(command_bytes)} bytes')
            
            # Read response with timeout
            start_time = time.time()
            response = bytearray()
            
            while time.time() - start_time < SPI_TIMEOUT:
                try:
                    chunk = os.read(self._fd, SPI_READ_CHUNK_SIZE)
                    if not chunk:  # No more data
                        break
                    response.extend(chunk)
                except BlockingIOError:
                    time.sleep(0.01)
                    continue
                except Exception as e:
                    log_info(f'[SPI] Read error: {str(e)}')
                    break
            
            log_info(f'[SPI] Received response: {list(response)}')
            
            if not response:
                return False, MESSAGES['TIMEOUT'], None
            
            return True, "Command sent successfully", self._bytes_to_hex(response)
            
        except Exception as e:
            error_msg = f'SPI communication error: {str(e)}'
            log_info(f'[SPI] {error_msg}')
            return False, error_msg, None

def send_quick_command(command: str, device_path: str) -> Tuple[bool, str, Optional[str]]:
    """
    Quick command function that handles device opening/closing.
    
    Args:
        command: Space-separated hex string command
        device_path: Path to the SPI device
        
    Returns:
        Tuple of (success, message, response)
    """
    try:
        with SPIDevice(device_path) as spi:
            return spi.send_command(command)
    except FileNotFoundError as e:
        return False, str(e), None
    except PermissionError as e:
        return False, str(e), None
    except Exception as e:
        return False, f"Error: {str(e)}", None
