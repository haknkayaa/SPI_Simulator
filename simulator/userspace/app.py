from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import json
import requests

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {
    'device_path': '/dev/spi_test',
    'bus_num': 0,
    'cs_num': 0,
    'speed': 1000000,
    'mode': 0,
    'bits_per_word': 8
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Routes
@app.route('/api/spi/config', methods=['GET'])
def get_config():
    return jsonify(load_config())

@app.route('/api/spi/config', methods=['POST'])
def update_config():
    config = request.json
    response = requests.post('http://localhost:5001/api/spi/config', json=config)
    return response.json()

@app.route('/api/spi/command', methods=['POST'])
def send_command():
    command = request.json.get('command')
    device_path = request.json.get('device_path', '/dev/spi_test')
    
    # Forward the command to the backend
    response = requests.post('http://localhost:5001/api/spi/command', 
                           json={'command': command, 'device_path': device_path})
    return response.json()

@app.route('/api/spi/status', methods=['GET'])
def get_status():
    response = requests.get('http://localhost:5001/api/spi/status')
    return response.json()

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True) 