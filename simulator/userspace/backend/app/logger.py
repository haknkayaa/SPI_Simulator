"""
Logging configuration for the SPI Simulator backend.
"""
import logging
from datetime import datetime
from collections import deque
from typing import Optional, List

from .config import LOG_BUFFER_SIZE, LOG_FORMAT

class LogBufferHandler(logging.Handler):
    """Custom log handler that maintains a circular buffer of log messages."""
    
    def __init__(self, buffer_size: int = LOG_BUFFER_SIZE):
        super().__init__()
        self.buffer = deque(maxlen=buffer_size)
        self.last_message: Optional[str] = None
        
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the buffer."""
        try:
            msg = self.format(record)
            
            # Avoid duplicate consecutive messages
            if msg != self.last_message:
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.buffer.append(f"[{timestamp}] {msg}")
                self.last_message = msg
                
        except Exception:
            self.handleError(record)
    
    def get_logs(self) -> List[str]:
        """Get all logs from the buffer."""
        return list(self.buffer)
    
    def clear(self) -> None:
        """Clear the log buffer."""
        self.buffer.clear()
        self.last_message = None

# Create and configure logger
logger = logging.getLogger('spi_simulator')
logger.setLevel(logging.INFO)

# Add custom handler
handler = LogBufferHandler()
formatter = logging.Formatter(LOG_FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_info(message: str) -> None:
    """Log an info message and print to console."""
    logger.info(message)
    print(message)  # Also print to console for immediate feedback

def get_logs() -> List[str]:
    """Get all logs from the buffer."""
    return handler.get_logs()

def clear_logs() -> None:
    """Clear all logs from the buffer."""
    handler.clear()
