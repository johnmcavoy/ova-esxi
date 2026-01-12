"""
Configuration file for OVA ESXi Deployment Application
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))

# Upload Configuration
UPLOAD_FOLDER = BASE_DIR / 'uploads'
MAX_CONTENT_LENGTH = 10 * 1024 * 1024 * 1024  # 10GB max file size
ALLOWED_EXTENSIONS = {'ova', 'ovf'}

# ESXi Configuration (can be overridden via environment variables or web form)
ESXI_HOST = os.environ.get('ESXI_HOST', '')
ESXI_USERNAME = os.environ.get('ESXI_USERNAME', 'root')
ESXI_PASSWORD = os.environ.get('ESXI_PASSWORD', '')
ESXI_DATASTORE = os.environ.get('ESXI_DATASTORE', 'datastore1')
ESXI_NETWORK = os.environ.get('ESXI_NETWORK', 'VM Network')

# OVFTool Configuration
# Default to local ovftool directory, fall back to system ovftool
LOCAL_OVFTOOL = BASE_DIR / 'ovftool' / 'ovftool'
if LOCAL_OVFTOOL.exists():
    DEFAULT_OVFTOOL = str(LOCAL_OVFTOOL)
else:
    DEFAULT_OVFTOOL = 'ovftool'  # Use system PATH

OVFTOOL_PATH = os.environ.get('OVFTOOL_PATH', DEFAULT_OVFTOOL)

# Deployment Options
DEFAULT_DISK_MODE = 'thin'  # thin, thick, or eagerZeroedThick
DEFAULT_POWER_ON = False

# Logging
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'app.log'
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Ensure directories exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
