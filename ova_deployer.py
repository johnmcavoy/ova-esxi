"""
OVA Deployer Module
Handles deployment of OVA files to ESXi using ovftool
"""
import subprocess
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DeploymentJob:
    """Represents a single deployment job"""

    def __init__(self, job_id: str, vm_name: str, ova_path: str, config: Dict):
        self.job_id = job_id
        self.vm_name = vm_name
        self.ova_path = ova_path
        self.config = config
        self.status = 'pending'  # pending, running, completed, failed
        self.progress = 0
        self.output = []
        self.error = None
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'vm_name': self.vm_name,
            'ova_path': self.ova_path,
            'status': self.status,
            'progress': self.progress,
            'output': self.output,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class OVADeployer:
    """Handles OVA deployment to ESXi"""

    def __init__(self, ovftool_path: str = 'ovftool'):
        self.ovftool_path = ovftool_path
        self.jobs: Dict[str, DeploymentJob] = {}
        self.job_counter = 0
        self.lock = threading.Lock()

    def generate_vm_names(self, base_name: str, count: int, naming_type: str,
                          custom_names: Optional[List[str]] = None) -> List[str]:
        """
        Generate VM names based on naming strategy

        Args:
            base_name: Base name for VMs
            count: Number of VMs to deploy
            naming_type: 'static' or 'dynamic'
            custom_names: List of custom names for static naming

        Returns:
            List of VM names
        """
        vm_names = []

        if naming_type == 'static' and custom_names:
            # Use provided custom names
            vm_names = custom_names[:count]
            # If not enough names provided, pad with numbered names
            if len(vm_names) < count:
                for i in range(len(vm_names), count):
                    vm_names.append(f"{base_name}-{i + 1}")
        else:
            # Dynamic naming with timestamp and counter
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            if count == 1:
                vm_names = [f"{base_name}-{timestamp}"]
            else:
                for i in range(count):
                    vm_names.append(f"{base_name}-{timestamp}-{i + 1}")

        return vm_names

    def create_deployment_jobs(self, ova_path: str, vm_names: List[str],
                                esxi_config: Dict, properties: Dict,
                                network_mappings: Dict) -> List[str]:
        """
        Create deployment jobs for multiple VMs

        Args:
            ova_path: Path to OVA file
            vm_names: List of VM names
            esxi_config: ESXi connection configuration
            properties: OVF properties to set
            network_mappings: Network name mappings

        Returns:
            List of job IDs
        """
        job_ids = []

        with self.lock:
            for vm_name in vm_names:
                self.job_counter += 1
                job_id = f"deploy-{self.job_counter}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                config = {
                    'esxi': esxi_config,
                    'properties': properties,
                    'network_mappings': network_mappings,
                    'vm_name': vm_name
                }

                job = DeploymentJob(job_id, vm_name, ova_path, config)
                self.jobs[job_id] = job
                job_ids.append(job_id)

                logger.info(f"Created deployment job {job_id} for VM {vm_name}")

        return job_ids

    def start_deployment(self, job_id: str) -> bool:
        """
        Start a deployment job

        Args:
            job_id: Job ID to start

        Returns:
            True if started successfully
        """
        if job_id not in self.jobs:
            logger.error(f"Job {job_id} not found")
            return False

        job = self.jobs[job_id]

        if job.status != 'pending':
            logger.warning(f"Job {job_id} is not in pending state")
            return False

        # Start deployment in background thread
        thread = threading.Thread(target=self._run_deployment, args=(job,))
        thread.daemon = True
        thread.start()

        return True

    def _run_deployment(self, job: DeploymentJob):
        """
        Execute the deployment (runs in background thread)

        Args:
            job: DeploymentJob to execute
        """
        job.status = 'running'
        job.started_at = datetime.now()
        job.output.append(f"Starting deployment of {job.vm_name}")

        try:
            # Build ovftool command
            cmd = self._build_ovftool_command(job)

            logger.info(f"Executing deployment command for {job.vm_name}")
            job.output.append(f"Command: {' '.join([c if not any(x in c for x in ['password=', 'pass=']) else '***' for c in cmd])}")

            # Execute ovftool
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Read output line by line
            for line in process.stdout:
                line = line.strip()
                if line:
                    job.output.append(line)
                    logger.debug(f"Job {job.job_id}: {line}")

                    # Try to extract progress
                    if '%' in line:
                        try:
                            # Look for patterns like "Opening OVA source: 50%"
                            import re
                            match = re.search(r'(\d+)%', line)
                            if match:
                                job.progress = int(match.group(1))
                        except:
                            pass

            # Wait for completion
            process.wait()

            if process.returncode == 0:
                job.status = 'completed'
                job.progress = 100
                job.output.append(f"Successfully deployed {job.vm_name}")
                logger.info(f"Deployment {job.job_id} completed successfully")
            else:
                job.status = 'failed'
                job.error = f"Deployment failed with exit code {process.returncode}"
                job.output.append(f"ERROR: {job.error}")
                logger.error(f"Deployment {job.job_id} failed: {job.error}")

        except Exception as e:
            job.status = 'failed'
            job.error = str(e)
            job.output.append(f"EXCEPTION: {str(e)}")
            logger.exception(f"Exception in deployment {job.job_id}")

        finally:
            job.completed_at = datetime.now()

    def _build_ovftool_command(self, job: DeploymentJob) -> List[str]:
        """
        Build ovftool command line

        Args:
            job: DeploymentJob

        Returns:
            Command as list of arguments
        """
        config = job.config
        esxi = config['esxi']

        cmd = [
            self.ovftool_path,
            '--acceptAllEulas',
            '--hideEula',
            '--noSSLVerify',  # May be needed for self-signed certs
            '--allowExtraConfig',
            f"--name={job.vm_name}",
            f"--datastore={esxi.get('datastore', 'datastore1')}",
        ]

        # Disk provisioning mode
        disk_mode = esxi.get('disk_mode', 'thin')
        cmd.append(f"--diskMode={disk_mode}")

        # Power on after deployment
        if esxi.get('power_on', False):
            cmd.append('--powerOn')

        # Network mappings
        for network_name, target_network in config.get('network_mappings', {}).items():
            if target_network:
                cmd.append(f"--net:{network_name}={target_network}")

        # OVF Properties
        for key, value in config.get('properties', {}).items():
            if value:  # Only add non-empty properties
                cmd.append(f"--prop:{key}={value}")

        # Deployment option (if specified)
        if esxi.get('deployment_option'):
            cmd.append(f"--deploymentOption={esxi['deployment_option']}")

        # Source OVA
        cmd.append(job.ova_path)

        # Target ESXi
        target = (f"vi://{esxi['username']}:{esxi['password']}@"
                  f"{esxi['host']}")

        cmd.append(target)

        return cmd

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a deployment job"""
        if job_id in self.jobs:
            return self.jobs[job_id].to_dict()
        return None

    def get_all_jobs(self) -> List[Dict]:
        """Get all deployment jobs"""
        with self.lock:
            return [job.to_dict() for job in self.jobs.values()]

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job

        Args:
            job_id: Job to cancel

        Returns:
            True if cancelled successfully
        """
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.status == 'pending':
                job.status = 'cancelled'
                job.error = 'Cancelled by user'
                logger.info(f"Job {job_id} cancelled")
                return True
            else:
                logger.warning(f"Cannot cancel job {job_id} in status {job.status}")
                return False
        return False
