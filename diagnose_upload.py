#!/usr/bin/env python3
"""
Diagnostic script to test upload capability and identify issues
"""
import os
import sys
from pathlib import Path

print("=" * 60)
print("OVA Upload Diagnostics")
print("=" * 60)
print()

# Check Python version
print(f"✓ Python version: {sys.version}")
print()

# Check upload directory
upload_dir = Path(__file__).parent / 'uploads'
print(f"Upload directory: {upload_dir}")
print(f"  Exists: {upload_dir.exists()}")

if upload_dir.exists():
    # Check permissions
    can_write = os.access(upload_dir, os.W_OK)
    print(f"  Writable: {can_write}")

    # Check space
    stat = os.statvfs(upload_dir)
    free_space_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
    print(f"  Free space: {free_space_gb:.2f} GB")

    if free_space_gb < 20:
        print(f"  ⚠ WARNING: Less than 20GB free space available!")

    # List current files
    files = list(upload_dir.glob('*.ova'))
    print(f"  Current OVA files: {len(files)}")
    for f in files[:5]:  # Show first 5
        size_gb = f.stat().st_size / (1024**3)
        print(f"    - {f.name} ({size_gb:.2f} GB)")
else:
    print("  ✗ Directory does not exist!")

print()

# Check logs directory
log_dir = Path(__file__).parent / 'logs'
print(f"Logs directory: {log_dir}")
print(f"  Exists: {log_dir.exists()}")

if log_dir.exists():
    can_write = os.access(log_dir, os.W_OK)
    print(f"  Writable: {can_write}")

    log_file = log_dir / 'app.log'
    if log_file.exists():
        size = log_file.stat().st_size
        print(f"  Log file size: {size} bytes")
        print(f"  Last 10 lines of log:")
        print("  " + "-" * 56)
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(f"  {line.rstrip()}")
        except Exception as e:
            print(f"  Error reading log: {e}")
        print("  " + "-" * 56)
    else:
        print("  No log file found (app may not have been started yet)")
else:
    print("  ✗ Directory does not exist!")

print()

# Check configuration
try:
    import config
    print("Configuration:")
    print(f"  MAX_CONTENT_LENGTH: {config.MAX_CONTENT_LENGTH / (1024**3):.1f} GB")
    print(f"  DEBUG: {config.DEBUG}")
    print(f"  HOST: {config.HOST}")
    print(f"  PORT: {config.PORT}")
    print(f"  OVFTOOL_PATH: {config.OVFTOOL_PATH}")
except Exception as e:
    print(f"  ✗ Error loading config: {e}")

print()

# Check Flask availability
try:
    import flask
    print(f"✓ Flask version: {flask.__version__}")
except ImportError:
    print("✗ Flask not installed!")

print()

# Test file creation
print("Testing file write capability:")
test_file = upload_dir / '.test_upload'
try:
    with open(test_file, 'w') as f:
        f.write('test')
    test_file.unlink()
    print("  ✓ Can create and delete files in upload directory")
except Exception as e:
    print(f"  ✗ Cannot write to upload directory: {e}")

print()
print("=" * 60)
print("Diagnostics Complete")
print("=" * 60)
print()
print("If you're experiencing upload issues:")
print("1. Check that you have enough free disk space (20GB+)")
print("2. Ensure the uploads directory is writable")
print("3. Check app.log for error messages")
print("4. Try uploading a smaller file first to test")
print("5. Check browser console (F12) for JavaScript errors")
print()
