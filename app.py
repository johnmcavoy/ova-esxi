"""
Flask OVA Deployment Application
Main application file
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session

import config
from ova_analyzer import OVAAnalyzer
from ova_deployer import OVADeployer

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config)

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize analyzer and deployer
analyzer = OVAAnalyzer(config.OVFTOOL_PATH)
deployer = OVADeployer(config.OVFTOOL_PATH)

# Store analysis results in memory (in production, use Redis or database)
analysis_cache = {}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Home page"""
    # Check if ovftool is available
    ovftool_available = analyzer.verify_ovftool()

    # Get list of uploaded OVAs
    ova_files = []
    if config.UPLOAD_FOLDER.exists():
        for file_path in config.UPLOAD_FOLDER.glob('*.ova'):
            ova_files.append({
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                'analyzed': file_path.name in analysis_cache
            })

    return render_template('index.html',
                           ovftool_available=ovftool_available,
                           ova_files=ova_files)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle OVA file upload"""
    if 'file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = config.UPLOAD_FOLDER / filename

        try:
            file.save(file_path)
            flash(f'File {filename} uploaded successfully', 'success')
            logger.info(f"Uploaded file: {filename}")
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'error')
            logger.error(f"Upload error: {str(e)}")

        return redirect(url_for('index'))
    else:
        flash('Invalid file type. Only .ova files are allowed', 'error')
        return redirect(url_for('index'))


@app.route('/analyze/<filename>')
def analyze_ova(filename):
    """Analyze an OVA file"""
    file_path = config.UPLOAD_FOLDER / secure_filename(filename)

    if not file_path.exists():
        flash('File not found', 'error')
        return redirect(url_for('index'))

    try:
        # Check if already analyzed
        if filename in analysis_cache:
            analysis = analysis_cache[filename]
        else:
            # Perform analysis
            logger.info(f"Starting analysis of {filename}")
            analysis = analyzer.analyze_ova(str(file_path))
            analysis_cache[filename] = analysis

        return render_template('analysis.html',
                               filename=filename,
                               analysis=analysis)

    except Exception as e:
        flash(f'Error analyzing file: {str(e)}', 'error')
        logger.error(f"Analysis error: {str(e)}")
        return redirect(url_for('index'))


@app.route('/api/analyze/<filename>')
def api_analyze(filename):
    """API endpoint for OVA analysis"""
    file_path = config.UPLOAD_FOLDER / secure_filename(filename)

    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404

    try:
        if filename in analysis_cache:
            analysis = analysis_cache[filename]
        else:
            analysis = analyzer.analyze_ova(str(file_path))
            analysis_cache[filename] = analysis

        return jsonify(analysis)

    except Exception as e:
        logger.error(f"API analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/deploy/<filename>')
def deploy_form(filename):
    """Show deployment configuration form"""
    file_path = config.UPLOAD_FOLDER / secure_filename(filename)

    if not file_path.exists():
        flash('File not found', 'error')
        return redirect(url_for('index'))

    # Get or perform analysis
    if filename in analysis_cache:
        analysis = analysis_cache[filename]
    else:
        try:
            analysis = analyzer.analyze_ova(str(file_path))
            analysis_cache[filename] = analysis
        except Exception as e:
            flash(f'Error analyzing file: {str(e)}', 'error')
            return redirect(url_for('index'))

    # Prepare default ESXi configuration
    esxi_config = {
        'host': config.ESXI_HOST,
        'username': config.ESXI_USERNAME,
        'password': config.ESXI_PASSWORD,
        'datastore': config.ESXI_DATASTORE,
        'network': config.ESXI_NETWORK,
        'disk_mode': config.DEFAULT_DISK_MODE,
        'power_on': config.DEFAULT_POWER_ON
    }

    return render_template('deploy.html',
                           filename=filename,
                           analysis=analysis,
                           esxi_config=esxi_config)


@app.route('/api/deploy', methods=['POST'])
def api_deploy():
    """API endpoint to start deployment"""
    try:
        data = request.json

        filename = data.get('filename')
        vm_base_name = data.get('vm_base_name', 'VM')
        vm_count = int(data.get('vm_count', 1))
        naming_type = data.get('naming_type', 'dynamic')  # dynamic or static
        custom_names = data.get('custom_names', [])  # For static naming

        esxi_config = data.get('esxi_config', {})
        properties = data.get('properties', {})
        network_mappings = data.get('network_mappings', {})

        # Validate
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400

        file_path = config.UPLOAD_FOLDER / secure_filename(filename)
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        if vm_count < 1 or vm_count > 100:
            return jsonify({'error': 'VM count must be between 1 and 100'}), 400

        # Generate VM names
        vm_names = deployer.generate_vm_names(
            vm_base_name,
            vm_count,
            naming_type,
            custom_names
        )

        # Create deployment jobs
        job_ids = deployer.create_deployment_jobs(
            str(file_path),
            vm_names,
            esxi_config,
            properties,
            network_mappings
        )

        # Start all jobs
        for job_id in job_ids:
            deployer.start_deployment(job_id)

        logger.info(f"Started {len(job_ids)} deployment jobs for {filename}")

        return jsonify({
            'success': True,
            'message': f'Started deployment of {len(job_ids)} VMs',
            'job_ids': job_ids,
            'vm_names': vm_names
        })

    except Exception as e:
        logger.error(f"Deployment error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/jobs')
def jobs_list():
    """Show all deployment jobs"""
    jobs = deployer.get_all_jobs()
    return render_template('jobs.html', jobs=jobs)


@app.route('/api/jobs')
def api_jobs():
    """API endpoint to get all jobs"""
    jobs = deployer.get_all_jobs()
    return jsonify(jobs)


@app.route('/api/jobs/<job_id>')
def api_job_status(job_id):
    """API endpoint to get job status"""
    job = deployer.get_job_status(job_id)
    if job:
        return jsonify(job)
    else:
        return jsonify({'error': 'Job not found'}), 404


@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
def api_cancel_job(job_id):
    """API endpoint to cancel a job"""
    if deployer.cancel_job(job_id):
        return jsonify({'success': True, 'message': 'Job cancelled'})
    else:
        return jsonify({'error': 'Cannot cancel job'}), 400


@app.route('/api/probe/<filename>')
def api_probe(filename):
    """API endpoint to get raw ovftool probe output"""
    file_path = config.UPLOAD_FOLDER / secure_filename(filename)

    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404

    try:
        output = analyzer.get_full_probe(str(file_path))
        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings page for ESXi configuration"""
    if request.method == 'POST':
        # Save settings to session or database
        session['esxi_host'] = request.form.get('esxi_host', '')
        session['esxi_username'] = request.form.get('esxi_username', 'root')
        session['esxi_password'] = request.form.get('esxi_password', '')
        session['esxi_datastore'] = request.form.get('esxi_datastore', 'datastore1')
        session['esxi_network'] = request.form.get('esxi_network', 'VM Network')

        flash('Settings saved', 'success')
        return redirect(url_for('settings'))

    # Get current settings
    current_settings = {
        'esxi_host': session.get('esxi_host', config.ESXI_HOST),
        'esxi_username': session.get('esxi_username', config.ESXI_USERNAME),
        'esxi_password': session.get('esxi_password', config.ESXI_PASSWORD),
        'esxi_datastore': session.get('esxi_datastore', config.ESXI_DATASTORE),
        'esxi_network': session.get('esxi_network', config.ESXI_NETWORK),
    }

    return render_template('settings.html', settings=current_settings)


@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    """Delete an uploaded OVA file"""
    file_path = config.UPLOAD_FOLDER / secure_filename(filename)

    try:
        if file_path.exists():
            file_path.unlink()
            # Remove from cache
            if filename in analysis_cache:
                del analysis_cache[filename]
            flash(f'File {filename} deleted successfully', 'success')
            logger.info(f"Deleted file: {filename}")
        else:
            flash('File not found', 'error')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
        logger.error(f"Delete error: {str(e)}")

    return redirect(url_for('index'))


if __name__ == '__main__':
    logger.info(f"Starting Flask application on {config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
