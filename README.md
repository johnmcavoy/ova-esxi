# OVA ESXi Deployer

A Flask web application for analyzing and deploying OVA files to standalone ESXi servers using VMware ovftool.

## Features

- **Upload OVA Files**: Store OVA files in a local repository on the Ubuntu host
- **Analyze OVAs**: Extract parameters, properties, network requirements, and hardware specifications
- **Detect ESXi Compatibility**: Identify which OVAs can be deployed to standalone ESXi vs requiring vCenter
- **Web-Based Configuration**: User-friendly forms to configure all deployment parameters
- **Multiple Deployments**: Deploy multiple instances of the same OVA with a single operation
- **Flexible Naming**:
  - Dynamic naming with timestamps
  - Static naming with custom VM names
- **Real-Time Monitoring**: Track deployment progress and view logs
- **Remote Access**: Access the application from any device on your network

## Requirements

### Software Requirements

1. **Python 3.8+**
2. **VMware ovftool** - Download from [VMware Developer Portal](https://developer.vmware.com/tools/ovftool)
3. **ESXi Server** (standalone, no vCenter required)

### Python Dependencies

- Flask 3.0.0
- Werkzeug 3.0.1

## Installation

### 1. Install ovftool

You have two options for installing ovftool:

#### Option A: Local Installation (Recommended)

Place ovftool directly in the application's `ovftool/` directory:

```bash
# Download from VMware (requires free account)
# https://developer.vmware.com/tools/ovftool

# Extract the bundle to a temporary location
chmod +x VMware-ovftool-*-lin.x86_64.bundle
./VMware-ovftool-*-lin.x86_64.bundle --extract /tmp/ovftool-extract

# Copy to application directory
cp -r /tmp/ovftool-extract/vmware-ovftool/* /home/user/ova-esxi/ovftool/

# Make executable
chmod +x /home/user/ova-esxi/ovftool/ovftool

# Verify installation
./ovftool/ovftool --version
```

See `ovftool/README.md` for detailed instructions.

#### Option B: System-Wide Installation

Install ovftool system-wide (requires sudo):

```bash
# Download from VMware
# https://developer.vmware.com/tools/ovftool

# Install system-wide
chmod +x VMware-ovftool-*-lin.x86_64.bundle
sudo ./VMware-ovftool-*-lin.x86_64.bundle --console --required --eulas-agreed

# Verify installation
ovftool --version
```

**Note**: The application will automatically use the local `ovftool/ovftool` if present, otherwise it will look for ovftool in your system PATH.

### 2. Clone or Download This Repository

```bash
cd /home/user
git clone <repository-url> ova-esxi
cd ova-esxi
```

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Configure the Application

Edit `config.py` or set environment variables:

```bash
# Optional: Set default ESXi credentials
export ESXI_HOST="192.168.1.100"
export ESXI_USERNAME="root"
export ESXI_PASSWORD="your-password"
export ESXI_DATASTORE="datastore1"
export ESXI_NETWORK="VM Network"

# Optional: Set Flask configuration
export SECRET_KEY="your-secret-key"
export HOST="0.0.0.0"  # Listen on all interfaces
export PORT="5000"
```

## Usage

### Start the Application

```bash
# Activate virtual environment (if using)
source venv/bin/activate

# Run the Flask application
python app.py
```

The application will be available at:
- Local: `http://localhost:5000`
- Network: `http://<your-server-ip>:5000`

### Workflow

1. **Upload OVA File**
   - Navigate to the home page
   - Click "Choose File" and select your OVA file
   - Click "Upload"

2. **Analyze OVA**
   - Click "Analyze" next to your uploaded OVA
   - Review the analysis results:
     - Hardware specifications (CPU, RAM, Disks)
     - Network adapters required
     - OVF properties (configurable parameters)
     - Required vs optional parameters
     - ESXi compatibility status

3. **Configure Deployment**
   - Click "Deploy" to open the deployment form
   - Configure deployment settings:
     - **VM Base Name**: Base name for your VM(s)
     - **VM Count**: Number of instances to deploy (1-100)
     - **Naming Strategy**: Choose dynamic or static naming
     - **ESXi Settings**: Host, credentials, datastore
     - **Network Mappings**: Map OVA networks to ESXi networks
     - **OVF Properties**: Fill in required and optional properties

4. **Deploy**
   - Click "Start Deployment"
   - Monitor progress in the Deployments page
   - View detailed logs for each deployment job

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ESXI_HOST` | - | ESXi server IP or hostname |
| `ESXI_USERNAME` | `root` | ESXi login username |
| `ESXI_PASSWORD` | - | ESXi login password |
| `ESXI_DATASTORE` | `datastore1` | Default datastore name |
| `ESXI_NETWORK` | `VM Network` | Default network name |
| `HOST` | `0.0.0.0` | Flask listen address |
| `PORT` | `5000` | Flask listen port |
| `SECRET_KEY` | auto-generated | Flask secret key |
| `DEBUG` | `True` | Debug mode (disable in production) |
| `OVFTOOL_PATH` | `ovftool` | Path to ovftool binary |

### Deployment Options

- **Disk Provisioning Modes**:
  - `thin`: Thin provisioning (grows as needed)
  - `thick`: Thick provisioning (full size allocated)
  - `eagerZeroedThick`: Thick eager zeroed (best performance)

- **Naming Strategies**:
  - **Dynamic**: Auto-generated names with timestamp (e.g., `MyVM-20240115-123456-1`)
  - **Static**: Custom names specified for each VM

## API Endpoints

The application provides REST API endpoints for automation:

### Upload and Analysis

- `GET /` - Home page
- `POST /upload` - Upload OVA file
- `GET /analyze/<filename>` - Analyze OVA (web page)
- `GET /api/analyze/<filename>` - Analyze OVA (JSON)
- `GET /api/probe/<filename>` - Raw ovftool output

### Deployment

- `GET /deploy/<filename>` - Deployment form
- `POST /api/deploy` - Start deployment (JSON)
- `GET /jobs` - List all jobs (web page)
- `GET /api/jobs` - List all jobs (JSON)
- `GET /api/jobs/<job_id>` - Get job status
- `POST /api/jobs/<job_id>/cancel` - Cancel pending job

### Settings

- `GET /settings` - Settings page
- `POST /settings` - Save settings

## Example: Analyze OVA using ovftool CLI

```bash
# Verify OVA file
ovftool --hideEula --acceptAllEulas --verifyOnly /path/to/your.ova

# Get full probe information
ovftool /path/to/your.ova

# Deploy manually
ovftool \
  --acceptAllEulas \
  --name=MyVM \
  --datastore=datastore1 \
  --net:"VM Network"="VM Network" \
  --prop:hostname=myhost \
  /path/to/your.ova \
  vi://root:password@192.168.1.100
```

## Security Considerations

⚠️ **Important Security Notes:**

1. **Use HTTPS in Production**: Configure a reverse proxy (nginx, Apache) with SSL/TLS
2. **Restrict Network Access**: Use firewall rules to limit access to trusted IPs
3. **Change Default Secret Key**: Set a strong `SECRET_KEY` environment variable
4. **Secure Credentials**: Use environment variables, not hardcoded passwords
5. **File Upload Limits**: The app limits uploads to 10GB by default
6. **ESXi Certificate Validation**: Currently disabled (`--noSSLVerify`) - enable in production

### Production Deployment Example (with nginx)

```nginx
server {
    listen 443 ssl;
    server_name ova-deployer.example.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for large file uploads
        proxy_read_timeout 600s;
        client_max_body_size 10G;
    }
}
```

## Troubleshooting

### ovftool Not Found

```bash
# Find ovftool
which ovftool

# If not in PATH, set in config.py or environment
export OVFTOOL_PATH="/usr/bin/ovftool"
```

### Connection to ESXi Failed

- Verify ESXi host is reachable: `ping <esxi-host>`
- Check credentials are correct
- Ensure SSH/HTTPS is enabled on ESXi
- Verify firewall rules allow connections

### Deployment Fails

- Check the job logs in the Deployments page
- Common issues:
  - Missing required OVF properties
  - Invalid network mappings
  - Insufficient datastore space
  - Incompatible OVA (requires vCenter)

### OVA Analysis Shows No Properties

- Some OVAs have no configurable properties
- The OVA can still be deployed with network/datastore settings

## File Structure

```
ova-esxi/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── ova_analyzer.py        # OVA analysis module
├── ova_deployer.py        # Deployment module
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── analysis.html
│   ├── deploy.html
│   ├── jobs.html
│   └── settings.html
├── static/               # Static files (CSS, JS)
├── uploads/              # Uploaded OVA files
└── logs/                 # Application logs
```

## Contributing

Contributions are welcome! Areas for improvement:

- Database backend for persistence (SQLite, PostgreSQL)
- User authentication and multi-user support
- Advanced deployment options (resource pools, VM folders)
- OVA template library
- Scheduled deployments
- Email notifications
- Integration with Ansible/Terraform

## License

This project is provided as-is for educational and practical use.

## Support

For issues, questions, or contributions, please open an issue in the repository.

## Acknowledgments

- Built with Flask web framework
- Uses VMware ovftool for OVA operations
- Designed for standalone ESXi deployments
