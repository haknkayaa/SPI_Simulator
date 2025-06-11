"""
API routes for the SPI Simulator backend.
"""
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from app.driver import driver_manager
from app.spi import send_quick_command
from app.system import get_system_status
from app.logger import get_logs, clear_logs
from api.schemas import (
    SPICommand,
    SPIResponse,
    DriverConfig,
    SystemStatus,
    LogResponse
)

# Create blueprint
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/spi/command', methods=['POST'])
def send_command() -> Dict[str, Any]:
    """Send a command to the SPI device."""
    try:
        data = request.json
        command = data.get('command')
        device_path = data.get('device_path', '/dev/spi_test')
        
        if not driver_manager.is_loaded():
            return jsonify({
                'status': 'error',
                'message': 'Driver not loaded'
            }), 400
        
        success, message, response = send_quick_command(command, device_path)
        return jsonify({
            'status': 'success' if success else 'error',
            'message': message,
            'response': response
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing command: {str(e)}'
        }), 500

@api.route('/spi/config', methods=['POST'])
def update_config() -> Dict[str, Any]:
    """Update driver configuration."""
    try:
        config = request.json
        device_name = config.get('device_name', 'spi_test')
        sequences = config.get('sequences')
        
        success, message = driver_manager.load(device_name, sequences)
        return jsonify({
            'status': 'success' if success else 'error',
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error updating configuration: {str(e)}'
        }), 500

@api.route('/spi/status', methods=['GET'])
def check_driver_status() -> Dict[str, Any]:
    """Check driver status."""
    try:
        return jsonify({
            "status": "success",
            "driver_loaded": driver_manager.is_loaded(),
            "device_exists": bool(driver_manager.get_device_path())
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api.route('/spi/logs', methods=['GET'])
def get_logs_endpoint() -> Dict[str, Any]:
    """Get system logs."""
    return jsonify({
        "status": "success",
        "logs": get_logs()
    })

@api.route('/spi/clear-logs', methods=['POST'])
def clear_logs_endpoint() -> Dict[str, Any]:
    """Clear system logs."""
    try:
        clear_logs()
        return jsonify({
            "status": "success",
            "message": "Logs cleared successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error clearing logs: {str(e)}"
        }), 500

@api.route('/spi/unload-driver', methods=['POST'])
def unload_driver_endpoint() -> Dict[str, Any]:
    """Unload the driver."""
    try:
        success, message = driver_manager.unload()
        return jsonify({
            'status': 'success' if success else 'error',
            'message': message
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error unloading driver: {str(e)}'
        }), 500

@api.route('/spi/load-driver', methods=['POST'])
def load_driver_endpoint() -> Dict[str, Any]:
    """Load the driver."""
    try:
        data = request.json or {}
        device_name = data.get('device_name', 'spi_test')
        sequences = data.get('sequences', [])
        
        success, message = driver_manager.load(device_name, sequences)
        return jsonify({
            'status': 'success' if success else 'error',
            'message': message
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error loading driver: {str(e)}'
        }), 500

@api.route('/spi/sequences', methods=['POST'])
def update_sequences() -> Dict[str, Any]:
    """Update SPI sequences."""
    try:
        sequences = request.json
        success = driver_manager._save_sequences(sequences)
        return jsonify({
            'status': 'success' if success else 'error',
            'message': 'Sequences updated successfully' if success else 'Failed to update sequences'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error updating sequences: {str(e)}'
        }), 500

@api.route('/system/status', methods=['GET'])
def get_status() -> Dict[str, Any]:
    """Get system status."""
    return jsonify({
        'status': 'success',
        'data': get_system_status()
    })
