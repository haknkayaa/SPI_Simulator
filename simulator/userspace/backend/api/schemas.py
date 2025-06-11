"""
API request and response schemas for the SPI Simulator backend.
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class SPICommand(BaseModel):
    """SPI command request model."""
    command: str = Field(..., description="Space-separated hex string command")
    device_path: Optional[str] = Field(None, description="Path to SPI device")

class SPIResponse(BaseModel):
    """SPI command response model."""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    response: Optional[str] = Field(None, description="SPI response data")

class DriverConfig(BaseModel):
    """Driver configuration request model."""
    device_name: str = Field(..., description="Name of the SPI device")
    sequences: Optional[List[Dict]] = Field(None, description="List of SPI sequences")

class SystemStatus(BaseModel):
    """System status response model."""
    status: str = Field(..., description="Response status")
    data: Dict = Field(..., description="System status data")

class LogResponse(BaseModel):
    """Log response model."""
    status: str = Field(..., description="Response status")
    logs: List[str] = Field(..., description="List of log messages")
