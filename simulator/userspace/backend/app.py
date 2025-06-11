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

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Log buffer'ı oluştur (son 100 log)
log_buffer = deque(maxlen=100)

# Custom log handler
class LogBufferHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_buffer.append(f"[{timestamp}] {msg}")
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
    return os.path.exists('/dev/spi_test')

def check_driver_loaded():
    try:
        result = subprocess.run(['lsmod'], capture_output=True, text=True)
        return 'spi_test_driver' in result.stdout
    except Exception as e:
        log_info(f"Error checking driver status: {e}")
        return False

# Sequence dosyasının yolu
SEQUENCE_FILE = '/tmp/spi_sequences.json'

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

def load_driver(device_name="spi_test", sequences=None):
    try:
        log_info(f"Starting driver load process for device: {device_name}")
        
        # Save sequences if provided
        if sequences:
            if not save_sequences(sequences):
                log_info("Warning: Failed to save sequences, continuing anyway...")
        
        # Unload existing driver if loaded
        try:
            log_info("Checking for existing driver...")
            result = subprocess.run(['sudo', 'rmmod', 'spi_test_driver'], 
                                 capture_output=True, 
                                 text=True)
            if result.returncode == 0:
                log_info("✓ Existing driver unloaded successfully")
            else:
                log_info("✓ No existing driver found (this is normal)")
        except Exception as e:
            log_info(f"Note: {str(e)}")

        # Load driver with device name parameter
        log_info("Loading new driver...")
        driver_path = '/home/ubuntu/Desktop/SPI_Simulator/build/output/spi_test_driver.ko'
        
        if not os.path.exists(driver_path):
            log_info(f"✗ Error: Driver file not found at {driver_path}")
            return False
            
        # Ensure device_name is properly quoted and use the provided name
        cmd = ['sudo', 'insmod', driver_path, f'device_name={device_name}']
        log_info(f"Executing command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True)
                              
        if result.returncode != 0:
            log_info(f"✗ Error loading driver: {result.stderr}")
            return False
            
        log_info(f"✓ Driver loaded successfully with device name: {device_name}")
        
        # Set device permissions
        device_path = f'/dev/{device_name}'
        log_info(f"Setting permissions for {device_path}...")
        
        # Wait a bit for the device to be created
        time.sleep(1)
        
        # Set permissions to 666
        chmod_cmd = ['sudo', 'chmod', '666', device_path]
        log_info(f"Executing command: {' '.join(chmod_cmd)}")
        
        chmod_result = subprocess.run(chmod_cmd,
                                    capture_output=True,
                                    text=True)
                                    
        if chmod_result.returncode == 0:
            log_info(f"✓ Device permissions set successfully")
        else:
            log_info(f"✗ Error setting device permissions: {chmod_result.stderr}")
            
        return True
        
    except Exception as e:
        log_info(f"✗ Unexpected error in load_driver: {str(e)}")
        return False

def unload_driver():
    try:
        log_info("Attempting to unload driver...")
        
        # Check if driver is loaded
        if not check_driver_loaded():
            log_info("✓ Driver is not loaded (this is normal)")
            return True
            
        # Try to unload the driver
        result = subprocess.run(['sudo', 'rmmod', 'spi_test_driver'], 
                              capture_output=True, 
                              text=True)
                              
        if result.returncode == 0:
            log_info("✓ Driver unloaded successfully")
            return True
        else:
            log_info(f"✗ Error unloading driver: {result.stderr}")
            return False
            
    except Exception as e:
        log_info(f"✗ Unexpected error in unload_driver: {str(e)}")
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
        result = subprocess.run(['/usr/local/bin/spi_test_driver', device_path], 
                              input=command.encode(), 
                              capture_output=True, 
                              text=True)
        
        if result.returncode != 0:
            return jsonify({
                'status': 'error',
                'message': f'Command execution failed: {result.stderr}'
            }), 500

        return jsonify({
            'status': 'success',
            'response': result.stdout
        })
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
        log_info("Checking driver status...")
        
        driver_loaded = check_driver_loaded()
        device_exists = check_device_exists()
        
        log_info(f"Driver status: {'loaded' if driver_loaded else 'not loaded'}")
        log_info(f"Device status: {'exists' if device_exists else 'does not exist'}")
        
        return jsonify({
            "status": "success",
            "driver_loaded": driver_loaded,
            "device_exists": device_exists
        })
    except Exception as e:
        log_info(f"Exception in check_driver_status: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/spi/logs', methods=['GET'])
def get_logs():
    return jsonify({
        "status": "success",
        "logs": list(log_buffer)
    })

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
        sequences = data.get('sequences', [])
        
        if load_driver(device_name, sequences):
            return jsonify({
                'status': 'success',
                'message': f'Driver loaded successfully with device name: {device_name}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to load driver'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error loading driver: {str(e)}'
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

if __name__ == '__main__':
    log_info("Starting SPI Simulator Backend...")
    log_info(f"Python version: {sys.version}")
    log_info(f"Current working directory: {os.getcwd()}")
    log_info(f"Driver path: /home/ubuntu/Desktop/SPI_Simulator/simulator/build/output/spi_test_driver.ko")
    log_info(f"Driver exists: {os.path.exists('/home/ubuntu/Desktop/SPI_Simulator/simulator/build/output/spi_test_driver.ko')}")
    log_info(f"Sudo permission: {check_sudo_permission()}")
    log_info(f"Device exists: {check_device_exists()}")
    log_info(f"Driver loaded: {check_driver_loaded()}")
    
    app.run(debug=True, host='0.0.0.0', port=5001) 