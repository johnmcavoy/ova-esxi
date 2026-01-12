#!/bin/bash

# OVA ESXi Deployer Setup Script

echo "============================================"
echo "OVA ESXi Deployer - Setup"
echo "============================================"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Check for ovftool
if command -v ovftool &> /dev/null; then
    OVFTOOL_VERSION=$(ovftool --version 2>&1 | head -1)
    echo "✓ Found $OVFTOOL_VERSION"
else
    echo "⚠ WARNING: ovftool not found in PATH"
    echo "  Please install VMware ovftool from:"
    echo "  https://developer.vmware.com/tools/ovftool"
    echo ""
    echo "  This application will not work without ovftool!"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "✓ Virtual environment created"

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"

# Create necessary directories
echo ""
echo "Creating application directories..."
mkdir -p uploads logs static

echo "✓ Directories created"

# Check if .env file exists, if not create a template
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env configuration file..."
    cat > .env << 'EOF'
# Flask Configuration
SECRET_KEY=change-this-to-a-random-secret-key
DEBUG=True
HOST=0.0.0.0
PORT=5000

# ESXi Default Configuration
ESXI_HOST=
ESXI_USERNAME=root
ESXI_PASSWORD=
ESXI_DATASTORE=datastore1
ESXI_NETWORK=VM Network

# OVFTool Path (leave blank to use system default)
OVFTOOL_PATH=ovftool
EOF
    echo "✓ Created .env file"
    echo ""
    echo "IMPORTANT: Edit .env file to configure your ESXi connection:"
    echo "  - Set ESXI_HOST to your ESXi server IP"
    echo "  - Set ESXI_PASSWORD to your ESXi root password"
    echo "  - Adjust other settings as needed"
fi

# Generate a random secret key suggestion
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

echo ""
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Suggested random SECRET_KEY for .env:"
echo "  SECRET_KEY=$SECRET_KEY"
echo ""
echo "To start the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Edit .env with your ESXi settings"
echo "  3. Run: python app.py"
echo ""
echo "The application will be available at:"
echo "  http://localhost:5000 (local)"
echo "  http://<your-server-ip>:5000 (network)"
echo ""
echo "For more information, see README.md"
echo ""
