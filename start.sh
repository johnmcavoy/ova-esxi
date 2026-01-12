#!/bin/bash

# OVA ESXi Deployer Start Script

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check for ovftool
if ! command -v ${OVFTOOL_PATH:-ovftool} &> /dev/null; then
    echo "WARNING: ovftool not found!"
    echo "The application will start but OVA operations will fail"
    echo "Please install ovftool from: https://developer.vmware.com/tools/ovftool"
    echo ""
fi

# Start the application
echo "Starting OVA ESXi Deployer..."
echo "Access the application at: http://${HOST:-0.0.0.0}:${PORT:-5000}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
