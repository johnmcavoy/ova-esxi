# ovftool Directory

This directory should contain the VMware ovftool executable and related files.

## Installation Instructions

### Option 1: Extract from VMware Bundle (Recommended)

1. Download the ovftool bundle from VMware:
   - Visit: https://developer.vmware.com/tools/ovftool
   - Download: `VMware-ovftool-*-lin.x86_64.bundle`

2. Extract the files:
   ```bash
   # Make the bundle executable
   chmod +x VMware-ovftool-*.x86_64.bundle

   # Extract without installing system-wide
   ./VMware-ovftool-*.x86_64.bundle --extract /tmp/ovftool-extract

   # Copy the ovftool binary and libraries to this directory
   cp -r /tmp/ovftool-extract/vmware-ovftool/* /home/user/ova-esxi/ovftool/
   ```

3. Make ovftool executable:
   ```bash
   chmod +x /home/user/ova-esxi/ovftool/ovftool
   ```

4. Test it:
   ```bash
   /home/user/ova-esxi/ovftool/ovftool --version
   ```

### Option 2: Copy from Existing Installation

If ovftool is already installed elsewhere:

```bash
# Find existing ovftool
which ovftool

# Copy the entire ovftool directory
# Usually located at: /usr/lib/vmware-ovftool/ or /opt/vmware/ovftool/
cp -r /usr/lib/vmware-ovftool/* /home/user/ova-esxi/ovftool/
```

### Option 3: Manual Download

1. Download from VMware
2. Extract the contents to this directory
3. Ensure the `ovftool` binary is executable
4. Include all supporting libraries (.so files)

## Required Files

After installation, this directory should contain:

```
ovftool/
├── ovftool              (main executable)
├── ovftool.bin          (actual binary)
├── libcurl.so.4         (libraries)
├── libssl.so.1.0.0
├── libcrypto.so.1.0.0
├── libvmacore.so
├── libvim-types.so
├── libssoclient.so
└── ... (other supporting files)
```

## Verification

After placing the files, verify the installation:

```bash
# Test ovftool directly
./ovftool --version

# Or start the Flask application and check the home page
# It should show: "✓ ovftool is available"
```

## Troubleshooting

### Permission Denied
```bash
chmod +x ovftool
```

### Missing Libraries
Make sure all `.so` library files are present in this directory.

### Still Not Working
Check the application logs at `logs/app.log` for detailed error messages.

## Notes

- The Flask application is configured to look for ovftool at: `./ovftool/ovftool`
- All necessary shared libraries must be in this directory
- Make sure you have the Linux x86_64 version
