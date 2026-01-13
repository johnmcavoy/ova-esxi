# Troubleshooting Guide

## Upload Issues

### Large File Upload Fails

**Symptoms:**
- Upload progress bar shows progress but then fails
- "Upload error occurred" or "Network Error" message
- Browser console shows network error

**Common Causes & Solutions:**

#### 1. Request Timeout (Most Common for Large Files)

The Flask development server may timeout on large uploads (10GB+).

**Solution A: Use Production WSGI Server**

For large file uploads, use gunicorn with increased timeout:

```bash
# Install gunicorn
pip install gunicorn

# Run with increased timeout (3600 seconds = 1 hour)
gunicorn --bind 0.0.0.0:5000 --timeout 3600 --workers 1 app:app
```

**Solution B: Upload Smaller Files First**

Test with a smaller OVA file (< 5GB) to verify the system works, then try larger files.

#### 2. Disk Space Issues

**Check available space:**
```bash
df -h /home/user/ova-esxi/uploads
```

**Requirement:** At least 20GB+ free space needed

**Solution:** Free up disk space or change upload directory in config.py

#### 3. Network Interruption

**Symptoms:** Upload stops at random percentage

**Solution:**
- Use wired connection instead of WiFi
- Ensure stable network connection
- Try uploading during low-traffic hours

#### 4. Browser Timeout

Some browsers have built-in request timeouts.

**Solution:**
- Use Chrome or Firefox (better for large uploads)
- Don't minimize browser during upload
- Keep browser tab active

#### 5. File Permissions

**Check upload directory permissions:**
```bash
ls -la /home/user/ova-esxi/uploads
```

**Solution:**
```bash
# Make sure directory is writable
chmod 755 /home/user/ova-esxi/uploads
```

#### 6. Reverse Proxy Timeout (If using nginx/Apache)

If running behind a reverse proxy, it may have timeout limits.

**For nginx**, add to server block:
```nginx
client_body_timeout 3600s;
proxy_read_timeout 3600s;
proxy_connect_timeout 3600s;
client_max_body_size 20G;
```

**For Apache**, add:
```apache
Timeout 3600
ProxyTimeout 3600
LimitRequestBody 21474836480
```

### Diagnostic Commands

#### Run Full Diagnostics
```bash
cd /home/user/ova-esxi
python3 diagnose_upload.py
```

This will check:
- Disk space
- Directory permissions
- Configuration
- Log files

#### Check Application Logs
```bash
tail -f /home/user/ova-esxi/logs/app.log
```

Watch logs in real-time during upload to see errors.

#### Check System Resources
```bash
# Check disk usage
df -h

# Check memory
free -h

# Check if app is running
ps aux | grep python | grep app.py
```

#### Test with curl
```bash
# Test upload with a small file
curl -F "file=@small-test.ova" http://localhost:5000/upload -v
```

## Deployment Issues

### ovftool Not Found

**Symptoms:**
- "ovftool not found" on home page
- Analysis fails

**Solution:**
```bash
# Run ovftool check
./check_ovftool.sh

# Install to local directory (see ovftool/README.md)
```

### ESXi Connection Failed

**Symptoms:**
- Deployment fails immediately
- "Cannot connect to ESXi" error

**Solutions:**

1. **Check ESXi host is reachable:**
```bash
ping <esxi-host-ip>
```

2. **Verify credentials:**
- Try logging into ESXi web interface with same credentials

3. **Check ESXi SSH/HTTPS enabled:**
- SSH: ESXi > Host > Manage > Services > SSH (must be running)
- HTTPS: Usually enabled by default

4. **Firewall rules:**
```bash
# Check if ports are accessible
telnet <esxi-host-ip> 443
telnet <esxi-host-ip> 902
```

### Network Mapping Errors

**Symptoms:**
- "Network 'xyz' not found" error during deployment

**Solution:**
- Network names are case-sensitive
- Verify network exists in ESXi: Networking > Port groups
- Use exact network name from ESXi

### Insufficient Datastore Space

**Symptoms:**
- Deployment fails midway
- "No space left on device" error

**Solution:**
- Check datastore free space in ESXi
- Clean up old VMs or snapshots
- Use different datastore

## Analysis Issues

### Analysis Takes Too Long

**Symptoms:**
- Analysis spinner runs forever
- Page times out

**Solution:**
- Large OVA files (15GB+) can take 2-5 minutes to analyze
- Check app.log for progress:
```bash
tail -f logs/app.log
```

### No Properties Found

This is normal for some OVAs. Not all OVAs have configurable OVF properties.

**What you can still configure:**
- Network mappings (required)
- Hardware resources (CPU, RAM)
- Disk provisioning mode
- ESXi settings

## Performance Issues

### Application Slow

**Possible causes:**
- Running on underpowered system
- Large upload in progress
- Multiple deployments running

**Solutions:**
- Use dedicated server for large deployments
- Deploy one VM at a time for large OVAs
- Restart application: `./start.sh`

### High Disk I/O

**During upload:** Normal - file being written to disk
**During deployment:** Normal - ovftool working

**Monitor:**
```bash
iotop  # If installed
# or
vmstat 1
```

## Getting Help

### Collect Information

Before reporting an issue, collect:

1. **Diagnostic output:**
```bash
python3 diagnose_upload.py > diagnostics.txt
```

2. **Application logs:**
```bash
tail -100 logs/app.log > app-log.txt
```

3. **Browser console errors:**
- Press F12 in browser
- Go to Console tab
- Screenshot any errors

4. **System information:**
```bash
uname -a
python3 --version
df -h
free -h
```

### Error Log Locations

- Application: `logs/app.log`
- ESXi: `/var/log/hostd.log` (on ESXi host)
- Browser: Press F12 → Console tab

### Common Error Messages

| Error Message | Cause | Solution |
|--------------|-------|----------|
| "Upload error occurred" | Network/timeout | Use gunicorn, check network |
| "ovftool not found" | Missing ovftool | Install ovftool |
| "Network 'X' not found" | Invalid network name | Check ESXi network name |
| "No space left" | Disk full | Free up space |
| "Permission denied" | File permissions | Fix directory permissions |
| "Connection refused" | ESXi not reachable | Check host/firewall |

### Quick Fixes

```bash
# Restart application
./start.sh

# Clear uploads and start fresh
rm -rf uploads/*.ova
./start.sh

# Check everything is working
python3 diagnose_upload.py

# Start with production server
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --timeout 3600 --workers 1 app:app
```

## Still Having Issues?

1. Check this troubleshooting guide thoroughly
2. Run diagnostics: `python3 diagnose_upload.py`
3. Check logs: `tail -f logs/app.log`
4. Check browser console (F12)
5. Try with a smaller OVA file first
6. Report issue with diagnostic output
