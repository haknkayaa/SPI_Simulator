from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import sys
import logging
from datetime import datetime
from collections import deque
import time
import json
import socket
import psutil
import fcntl
import struct
import select

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Global variables
driver_name = None
log_buffer = deque(maxlen=100)
last_log_message = None  # Son log mesajını takip etmek için

# Sequence dosyasının yolu
SEQUENCE_FILE = '/tmp/spi_sequences.json'

# Custom log handler
class LogBufferHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            global last_log_message
            
            # Aynı mesajı tekrar ekleme
            if msg != last_log_message:
                timestamp = datetime.now().strftime('%H:%M:%S')
                log_buffer.append(f"[{timestamp}] {msg}")
                last_log_message = msg
        except Exception:
            self.handleError(record)

# Logger'ı yapılandır
logger = logging.getLogger('spi_simulator')
logger.setLevel(logging.INFO)
handler = LogBufferHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_info(message):
    logger.info(message)
    print(message)  # Konsola da yazdır

def check_sudo_permission():
    try:
        result = subprocess.run(['sudo', '-n', 'true'], capture_output=True)
        return result.returncode == 0
    except Exception as e:
        log_info(f"Error checking sudo permission: {e}")
        return False

def check_device_exists():
    device_path = '/dev/spi_test'
    log_info(f"[PROCESS] Checking if device exists: {device_path}")
    exists = os.path.exists(device_path)
    log_info(f"[INFO] Device exists: {exists}")
    return exists

def check_driver_loaded():
    try:
        result = subprocess.run(['lsmod'], capture_output=True, text=True)
        return 'spi_simulator_driver' in result.stdout
    except Exception as e:
        log_info(f"Error checking driver status: {e}")
        return False

def save_sequences(sequences):
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(SEQUENCE_FILE), exist_ok=True)
        
        # Check if file exists
        file_exists = os.path.exists(SEQUENCE_FILE)
        
        # Save sequences to file
        with open(SEQUENCE_FILE, 'w') as f:
            json.dump(sequences, f, indent=2)
            
        if file_exists:
            log_info(f"✓ Updated existing sequences file at {SEQUENCE_FILE}")
        else:
            log_info(f"✓ Created new sequences file at {SEQUENCE_FILE}")
            
        # Log sequence details
        log_info(f"Total sequences saved: {len(sequences)}")
        for i, seq in enumerate(sequences, 1):
            log_info(f"Sequence {i}: Received='{seq.get('received', '')}', Response='{seq.get('response', '')}'")
            
        return True
    except Exception as e:
        log_info(f"✗ Error saving sequences: {str(e)}")
        return False

def load_driver(device_name="spidev0.0", sequences=None):
    global driver_name
    try:
        log_info(f"[PROCESS] Starting driver load process for device: {device_name}")
        driver_name = device_name  # Set the global driver_name
        log_info(f"[PROCESS] Using device name: {driver_name}")
        # Save sequences if provided
        if sequences:
            if not save_sequences(sequences):
                log_info("[WARNING] Failed to save sequences, continuing anyway...")
        
        # Unload existing driver if loaded
        try:
            log_info("[PROCESS] Checking for existing driver...")
            result = subprocess.run(['sudo', 'rmmod', 'spi_simulator_driver'], 
                                 capture_output=True, 
                                 text=True)
            if result.returncode == 0:
                log_info("[INFO] Existing driver unloaded successfully")
            else:
                log_info("[INFO] No existing driver found (this is normal)")
        except Exception as e:
            log_info(f"[INFO] {str(e)}")

        # Load driver with device name parameter
        log_info("[PROCESS] Loading new driver...")
        driver_path = '/home/ubuntu/Desktop/SPI_Simulator/build/output/spi_simulator_driver.ko'
        
        if not os.path.exists(driver_path):
            error_msg = f"[ERROR] Driver file not found at {driver_path}"
            log_info(error_msg)
            return False, error_msg
            
        # Ensure device_name is properly quoted and use the provided name
        cmd = ['sudo', 'insmod', driver_path, f'device_name={device_name}']
        log_info(f"[PROCESS] Executing command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True)
                              
        if result.returncode != 0:
            error_msg = f"[ERROR] Error loading driver: {result.stderr}"
            log_info(error_msg)
            return False, error_msg
            
        log_info(f"[SUCCESS] Driver loaded successfully with device name: {device_name}")
        
        # Set device permissions
        device_path = f'/dev/{device_name}'
        log_info(f"[PROCESS] Setting permissions for {device_path}...")
        
        # Wait a bit for the device to be created
        time.sleep(1)
        
        # Set permissions to 666
        chmod_cmd = ['sudo', 'chmod', '666', device_path]
        log_info(f"[PROCESS] Executing command: {' '.join(chmod_cmd)}")
        
        chmod_result = subprocess.run(chmod_cmd,
                                    capture_output=True,
                                    text=True)
                                    
        if chmod_result.returncode == 0:
            log_info("[SUCCESS] Device permissions set successfully")
        else:
            error_msg = f"[ERROR] Error setting device permissions: {chmod_result.stderr}"
            log_info(error_msg)
            return False, error_msg
            
        return True, "Driver loaded successfully"
        
    except Exception as e:
        error_msg = f"[ERROR] Unexpected error in load_driver: {str(e)}"
        log_info(error_msg)
        return False, error_msg

def unload_driver():
    global driver_name
    try:
        log_info("[PROCESS] Attempting to unload driver...")
        
        # Check if driver is loaded
        if not check_driver_loaded():
            log_info("[INFO] Driver is not loaded (this is normal)")
            driver_name = None  # Reset driver_name when driver is not loaded
            return True
            
        # Try to unload the driver
        result = subprocess.run(['sudo', 'rmmod', 'spi_simulator_driver'], 
                              capture_output=True, 
                              text=True)
                              
        if result.returncode == 0:
            log_info("[SUCCESS] Driver unloaded successfully")
            driver_name = None  # Reset driver_name when driver is unloaded
            return True
        else:
            log_info(f"[ERROR] Error unloading driver: {result.stderr}")
            return False
            
    except Exception as e:
        log_info(f"[ERROR] Unexpected error in unload_driver: {str(e)}")
        return False

@app.route('/api/spi/command', methods=['POST'])
def send_command():
    try:
        command = request.json.get('command')
        device_path = request.json.get('device_path', '/dev/spi_test')
        
        # Check if driver is loaded
        if not check_driver_loaded():
            return jsonify({'status': 'error', 'message': 'Driver not loaded'}), 400

        # Execute the command using the test program
        try:
            process = subprocess.Popen(['/usr/local/bin/spi_test_driver', device_path], 
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            
            # Send command and close stdin immediately
            process.stdin.write(command.encode())
            process.stdin.close()
            
            # Return success immediately
            return jsonify({
                'status': 'success',
                'message': 'Command sent successfully'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Command execution failed: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing command: {str(e)}'
        }), 500

@app.route('/api/spi/config', methods=['POST'])
def update_config():
    try:
        config = request.json
        log_info(f"Received config data: {config}")
        
        device_name = config.get('device_name', 'spi_test')
        log_info(f"Extracted device name: {device_name}")
        
        # Unload existing driver
        if not unload_driver():
            log_info("Note: Could not unload existing driver, continuing anyway...")
        
        # Load driver with new device name
        if not load_driver(device_name):
            log_info("Failed to load driver with new configuration")
            return jsonify({
                'status': 'error',
                'message': 'Failed to load driver with new configuration'
            }), 500
            
        log_info(f"Successfully reconfigured driver with device name: {device_name}")
        return jsonify({
            'status': 'success',
            'message': f'Driver reconfigured with device name: {device_name}'
        })
    except Exception as e:
        log_info(f"Error updating configuration: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error updating configuration: {str(e)}'
        }), 500

@app.route('/api/spi/status', methods=['GET'])
def check_driver_status():
    try:
        log_info("[PROCESS] Checking driver status...")
        
        driver_loaded = check_driver_loaded()
        device_exists = check_device_exists()
        
        log_info(f"[INFO] Driver status: {'loaded' if driver_loaded else 'not loaded'}")
        log_info(f"[INFO] Device status: {'exists' if device_exists else 'does not exist'}")
        
        return jsonify({
            "status": "success",
            "driver_loaded": driver_loaded,
            "device_exists": device_exists
        })
    except Exception as e:
        log_info(f"[ERROR] Exception in check_driver_status: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/spi/logs', methods=['GET'])
def get_logs():
    return jsonify({
        "status": "success",
        "logs": list(log_buffer)
    })

@app.route('/api/spi/clear-logs', methods=['POST'])
def clear_logs():
    try:
        log_buffer.clear()
        global last_log_message
        last_log_message = None  # Son log mesajını sıfırla
        return jsonify({
            "status": "success",
            "message": "Logs cleared successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error clearing logs: {str(e)}"
        }), 500

@app.route('/api/spi/unload-driver', methods=['POST', 'OPTIONS'])
def unload_driver_endpoint():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if unload_driver():
            return jsonify({
                'status': 'success',
                'message': 'Driver unloaded successfully' 
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to unload driver' 
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error unloading driver: {str(e)}'
        }), 500

@app.route('/api/spi/load-driver', methods=['POST', 'OPTIONS'])
def load_driver_endpoint():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Get device name and sequences from request
        data = request.json or {}
        device_name = data.get('device_name', 'spi_test')
        driver_name = f'/dev/{device_name}'
        sequences = data.get('sequences', [])
        
        success, message = load_driver(device_name, sequences)
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 500
    except Exception as e:
        error_msg = f"Error loading driver: {str(e)}"
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 500

@app.route('/api/spi/sequences', methods=['POST', 'OPTIONS'])
def update_sequences():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        sequences = request.json
        if save_sequences(sequences):
            return jsonify({
                'status': 'success',
                'message': 'Sequences updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update sequences'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error updating sequences: {str(e)}'
        }), 500

def check_port_status(port):
    """Check if a port is in use."""
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            return True
    return False

def get_system_status():
    """Get the status of all system components."""
    return {
        'backend': {
            'status': check_port_status(5001),
            'port': 5001
        },
        'frontend': {
            'status': check_port_status(5173),
            'port': 5173
        },
        'driver': {
            'status': check_driver_loaded(),
            'device': f"/dev/{driver_name}" if driver_name else None
        }
    }

@app.route('/api/system/status', methods=['GET'])
def get_status():
    """Get the status of all system components."""
    return jsonify({
        'status': 'success',
        'data': get_system_status()
    })

@app.route('/api/spi/quick-command', methods=['POST'])
def quick_spi_command():
    fd = None
    try:
        data = request.get_json()
        command = data.get('command')
        device_path = data.get('device_path', '/dev/spi_test')  # Get device path from request
        
        if not command:
            log_info('[quick_spi_command] No command provided')
            return jsonify({'status': 'error', 'message': 'No command provided'}), 400

        # Check if driver is loaded
        if not check_driver_loaded():
            log_info('[quick_spi_command] SPI driver is not loaded')
            return jsonify({'status': 'error', 'message': 'SPI driver is not loaded'}), 400

        # Check if device exists
        if not os.path.exists(device_path):
            log_info(f'[quick_spi_command] SPI device does not exist: {device_path}')
            return jsonify({'status': 'error', 'message': f'SPI device does not exist: {device_path}'}), 400

        try:
            log_info(f'[quick_spi_command] Attempting to open SPI device {device_path}')
            fd = os.open(device_path, os.O_RDWR)  # Removed O_NONBLOCK
            
            # Convert command to bytes
            command_bytes = bytes([int(x, 16) for x in command.split()])
            log_info(f'[quick_spi_command] Sending command bytes: {command_bytes}')
            
            # Write command
            bytes_written = os.write(fd, command_bytes)
            if bytes_written != len(command_bytes):
                log_info(f'[quick_spi_command] Warning: Only wrote {bytes_written} of {len(command_bytes)} bytes')
            
            # Read response with timeout
            start_time = time.time()
            response = bytearray()
            
            while time.time() - start_time < 1.0:  # 1 second timeout
                try:
                    # Try to read a single byte
                    chunk = os.read(fd, 1)
                    if not chunk:  # No more data
                        break
                    response.extend(chunk)
                except BlockingIOError:
                    # No data available, wait a bit
                    time.sleep(0.01)
                    continue
                except Exception as e:
                    log_info(f'[quick_spi_command] Read error: {str(e)}')
                    break
            
            log_info(f'[quick_spi_command] Received response: {list(response)}')
            
            if not response:
                return jsonify({
                    'status': 'timeout',
                    'message': 'No response received within 1 second'
                })

            return jsonify({
                'status': 'success',
                'response': ' '.join([f'{x:02x}' for x in response])
            })
            
        except PermissionError:
            log_info('[quick_spi_command] Permission denied while opening SPI device')
            return jsonify({'status': 'error', 'message': 'Permission denied. Try running with sudo.'}), 403
        except Exception as e:
            log_info(f'[quick_spi_command] SPI communication error: {str(e)}')
            return jsonify({'status': 'error', 'message': f'SPI communication error: {str(e)}'}), 500
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except Exception as e:
                    log_info(f'[quick_spi_command] Error closing file descriptor: {str(e)}')

    except Exception as e:
        log_info(f'[quick_spi_command] General error: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    log_info("[APP] Starting SPI Simulator Backend...")
    log_info(f"[INFO] Python version: {sys.version}")
    log_info(f"[INFO] Current working directory: {os.getcwd()}")
    log_info(f"[INFO] Driver path: /home/ubuntu/Desktop/SPI_Simulator/simulator/build/output/spi_simulator_driver.ko")
    log_info(f"[INFO] Driver exists: {os.path.exists('/home/ubuntu/Desktop/SPI_Simulator/simulator/build/output/spi_simulator_driver.ko')}")
    log_info(f"[INFO] Sudo permission: {check_sudo_permission()}")
    log_info(f"[INFO] Device exists: {check_device_exists()}")
    log_info(f"[INFO] Driver loaded: {check_driver_loaded()}")
    
    app.run(debug=True, host='0.0.0.0', port=5001) 