"""
Main application entry point for the SPI Simulator backend.
"""
import sys
import os
from flask import Flask
from flask_cors import CORS

from app.config import API_HOST, API_PORT, CORS_ORIGINS
from app.logger import log_info
from app.utils import check_sudo_permission, check_device_exists
from app.driver import driver_manager
from api.routes import api

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": CORS_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Register blueprints
    app.register_blueprint(api)
    
    return app

def main():
    """Main application entry point."""
    # Log startup information
    log_info("[APP] Starting SPI Simulator Backend...")
    log_info(f"[INFO] Python version: {sys.version}")
    log_info(f"[INFO] Current working directory: {os.getcwd()}")
    log_info(f"[INFO] Driver path: {driver_manager.driver_path}")
    log_info(f"[INFO] Driver exists: {os.path.exists(driver_manager.driver_path)}")
    log_info(f"[INFO] Sudo permission: {check_sudo_permission()}")
    log_info(f"[INFO] Device exists: {check_device_exists('/dev/spi_test')}")
    log_info(f"[INFO] Driver loaded: {driver_manager.is_loaded()}")
    
    # Create and run application
    app = create_app()
    app.run(debug=True, host=API_HOST, port=API_PORT)

if __name__ == '__main__':
    main()
