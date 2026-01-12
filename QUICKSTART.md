# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install ovftool

**Download ovftool from VMware:**
- Visit: https://developer.vmware.com/tools/ovftool
- Create a free account if needed
- Download: `VMware-ovftool-*-lin.x86_64.bundle`

**Place ovftool in the application directory:**

```bash
cd /home/user/ova-esxi

# Extract the bundle
chmod +x ~/Downloads/VMware-ovftool-*.bundle
~/Downloads/VMware-ovftool-*.bundle --extract /tmp/ovftool-extract

# Copy to ovftool directory
cp -r /tmp/ovftool-extract/vmware-ovftool/* ./ovftool/

# Make executable
chmod +x ./ovftool/ovftool

# Verify it works
./ovftool/ovftool --version
```

Or run the check script:
```bash
./check_ovftool.sh
```

### Step 2: Setup Python Environment

```bash
# Run the setup script
./setup.sh

# This will:
# - Create a Python virtual environment
# - Install Flask and dependencies
# - Create necessary directories
# - Generate a .env configuration file
```

### Step 3: Configure ESXi Settings

Edit the `.env` file with your ESXi connection details:

```bash
nano .env
```

Update these values:
```bash
ESXI_HOST=192.168.1.100        # Your ESXi server IP
ESXI_USERNAME=root              # ESXi username
ESXI_PASSWORD=your-password     # ESXi password
ESXI_DATASTORE=datastore1       # Your datastore name
ESXI_NETWORK=VM Network         # Your network name
```

### Step 4: Start the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Start the Flask app
python app.py
```

Or use the start script:
```bash
./start.sh
```

### Step 5: Access the Web Interface

Open your browser to:
- **Local**: http://localhost:5000
- **Network**: http://YOUR_SERVER_IP:5000

## 📋 Using the Application

### 1. Upload an OVA
- Click "Choose File" on the home page
- Select your `.ova` file
- Click "Upload"

### 2. Analyze the OVA
- Click "Analyze" next to your uploaded file
- Review:
  - ✓ Hardware requirements (CPU, RAM, Disk)
  - ✓ Network adapters needed
  - ✓ Configurable OVF properties
  - ✓ ESXi compatibility (standalone vs vCenter)

### 3. Deploy the OVA
- Click "Deploy" to configure deployment
- Set options:
  - **VM Base Name**: Name for your VM(s)
  - **VM Count**: How many instances (1-100)
  - **Naming Strategy**:
    - Dynamic: Auto-generated with timestamp
    - Static: Custom names for each VM
  - **ESXi Settings**: Host, credentials, datastore
  - **Network Mappings**: Map OVA networks to ESXi
  - **OVF Properties**: Configure required parameters

### 4. Monitor Deployment
- Click "Deployments" in the navigation
- Watch real-time progress
- View detailed logs
- Check for errors

## 🔧 Troubleshooting

### ovftool not found
```bash
# Check installation
./check_ovftool.sh

# If not found, see ovftool/README.md
```

### Can't connect to ESXi
- Verify ESXi IP is correct: `ping YOUR_ESXI_IP`
- Check ESXi credentials
- Ensure SSH/HTTPS is enabled on ESXi
- Check firewall rules

### Deployment fails
- Check "Deployments" page for error logs
- Common issues:
  - Missing required OVF properties
  - Invalid network mapping
  - Insufficient datastore space
  - OVA requires vCenter (not standalone ESXi)

### Web interface won't load
```bash
# Check if Flask is running
ps aux | grep python

# Check the port is available
netstat -tuln | grep 5000

# View logs
tail -f logs/app.log
```

## 📚 Next Steps

- Read the full README.md for detailed documentation
- Check API endpoints for automation
- Configure multiple ESXi targets
- Set up reverse proxy for HTTPS (production)

## 🆘 Need Help?

1. Check logs: `logs/app.log`
2. Run diagnostics: `./check_ovftool.sh`
3. Review README.md for detailed docs
4. Check ovftool/README.md for ovftool setup

## 🎯 Common Use Cases

### Deploy Single VM
- VM Count: 1
- Naming: Dynamic or Static
- Configure all OVF properties
- Click "Start Deployment"

### Deploy Multiple VMs
- VM Count: 10
- Naming: Dynamic (auto-generates unique names)
- All VMs get same configuration
- Click "Start Deployment"

### Custom Named VMs
- VM Count: 3
- Naming: Static
- Enter custom names for each VM
- Click "Start Deployment"
