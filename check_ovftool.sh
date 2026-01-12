#!/bin/bash

# Check ovftool installation

echo "========================================"
echo "Checking ovftool Installation"
echo "======================================"
echo ""

# Check local ovftool
LOCAL_OVFTOOL="/home/user/ova-esxi/ovftool/ovftool"
if [ -f "$LOCAL_OVFTOOL" ]; then
    echo "✓ Found local ovftool at: $LOCAL_OVFTOOL"
    if [ -x "$LOCAL_OVFTOOL" ]; then
        echo "✓ ovftool is executable"
        echo ""
        echo "Version information:"
        $LOCAL_OVFTOOL --version
        echo ""
        echo "✓ Local ovftool is ready to use!"
    else
        echo "✗ ovftool found but not executable"
        echo "  Run: chmod +x ./ovftool/ovftool"
    fi
else
    echo "⚠ Local ovftool not found in ./ovftool/ directory"
    echo ""

    # Check system PATH
    if command -v ovftool &> /dev/null; then
        echo "✓ Found ovftool in system PATH:"
        which ovftool
        ovftool --version
    else
        echo "✗ ovftool not found"
        echo ""
        echo "Please install ovftool using one of these methods:"
        echo ""
        echo "Option 1: Local installation (Recommended)"
        echo "  - Place ovftool files in: ./ovftool/"
        echo "  - See ovftool/README.md for details"
        echo ""
        echo "Option 2: System-wide installation"
        echo "  - Download from: https://developer.vmware.com/tools/ovftool"
        echo "  - Run: sudo ./VMware-ovftool-*.bundle --console --required --eulas-agreed"
    fi
fi
