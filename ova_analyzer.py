"""
OVA Analyzer Module
Analyzes OVA files using ovftool to extract deployment parameters
"""
import subprocess
import re
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class OVAAnalyzer:
    """Analyzes OVA files to extract deployment parameters"""

    def __init__(self, ovftool_path: str = 'ovftool'):
        self.ovftool_path = ovftool_path

    def verify_ovftool(self) -> bool:
        """Check if ovftool is available"""
        try:
            result = subprocess.run(
                [self.ovftool_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def analyze_ova(self, ova_path: str) -> Dict:
        """
        Analyze an OVA file to extract all parameters

        Args:
            ova_path: Path to the OVA file

        Returns:
            Dictionary containing analysis results
        """
        if not Path(ova_path).exists():
            raise FileNotFoundError(f"OVA file not found: {ova_path}")

        logger.info(f"Analyzing OVA: {ova_path}")

        # Run ovftool with --verifyOnly to get detailed information
        try:
            result = subprocess.run(
                [
                    self.ovftool_path,
                    '--hideEula',
                    '--acceptAllEulas',
                    '--verifyOnly',
                    ova_path
                ],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            analysis = {
                'file_path': ova_path,
                'file_name': Path(ova_path).name,
                'valid': result.returncode == 0,
                'output': result.stdout + result.stderr,
                'properties': self._extract_properties(result.stdout + result.stderr),
                'networks': self._extract_networks(result.stdout + result.stderr),
                'hardware': self._extract_hardware(result.stdout + result.stderr),
                'deployment_options': self._extract_deployment_options(result.stdout + result.stderr),
                'requires_vcenter': self._check_vcenter_requirement(result.stdout + result.stderr),
                'warnings': self._extract_warnings(result.stdout + result.stderr),
                'errors': self._extract_errors(result.stdout + result.stderr)
            }

            logger.info(f"Analysis complete. Valid: {analysis['valid']}, Properties: {len(analysis['properties'])}")

            return analysis

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout analyzing {ova_path}")
            raise Exception("Analysis timeout - file may be too large or corrupted")
        except Exception as e:
            logger.error(f"Error analyzing {ova_path}: {str(e)}")
            raise

    def _extract_properties(self, output: str) -> List[Dict]:
        """Extract OVF properties from ovftool output"""
        properties = []

        # Look for property definitions
        # Pattern: Property key="propertyId" label="Label" type="type" ...
        property_pattern = re.compile(
            r'Property\s+(?:key|ovf:key)="([^"]+)"[^>]*(?:label|ovf:label)="([^"]*)"[^>]*(?:type|ovf:type)="([^"]*)"',
            re.IGNORECASE
        )

        # Also look for the alternative format that ovftool might output
        prop_lines = re.finditer(r'Property:\s+(\S+)\s+\(([^)]+)\)\s*(.+)?', output, re.MULTILINE)

        for match in prop_lines:
            prop_id = match.group(1)
            prop_type = match.group(2)
            description = match.group(3) or ""

            # Check if property is required
            is_required = 'required' in description.lower() or '*' in description

            properties.append({
                'key': prop_id,
                'label': prop_id.replace('_', ' ').title(),
                'type': prop_type,
                'description': description.strip(),
                'required': is_required,
                'value': ''
            })

        # Additional pattern matching for XML-style property definitions
        xml_properties = property_pattern.finditer(output)
        for match in xml_properties:
            prop_key = match.group(1)
            prop_label = match.group(2)
            prop_type = match.group(3)

            # Avoid duplicates
            if not any(p['key'] == prop_key for p in properties):
                properties.append({
                    'key': prop_key,
                    'label': prop_label or prop_key,
                    'type': prop_type,
                    'description': '',
                    'required': False,
                    'value': ''
                })

        # Look for password fields
        for prop in properties:
            if 'password' in prop['key'].lower() or 'pwd' in prop['key'].lower():
                prop['type'] = 'password'

        return properties

    def _extract_networks(self, output: str) -> List[Dict]:
        """Extract network mappings from ovftool output"""
        networks = []

        # Pattern: Network "NetworkName"
        network_pattern = re.compile(r'Network\s+"([^"]+)"', re.IGNORECASE)

        for match in network_pattern.finditer(output):
            network_name = match.group(1)
            if network_name not in [n['name'] for n in networks]:
                networks.append({
                    'name': network_name,
                    'target': ''  # To be filled by user
                })

        return networks

    def _extract_hardware(self, output: str) -> Dict:
        """Extract hardware specifications"""
        hardware = {
            'cpus': None,
            'memory_mb': None,
            'disks': []
        }

        # Extract CPU count
        cpu_match = re.search(r'(\d+)\s+virtual\s+(?:CPU|cpus?)', output, re.IGNORECASE)
        if cpu_match:
            hardware['cpus'] = int(cpu_match.group(1))

        # Extract memory
        mem_match = re.search(r'(\d+)\s*(?:MB|MiB)\s+(?:of\s+)?memory', output, re.IGNORECASE)
        if mem_match:
            hardware['memory_mb'] = int(mem_match.group(1))

        # Extract disk information
        disk_pattern = re.compile(r'Disk\s+\d+.*?(\d+(?:\.\d+)?)\s*(GB|MB|TB)', re.IGNORECASE)
        for match in disk_pattern.finditer(output):
            size = float(match.group(1))
            unit = match.group(2).upper()

            # Convert to GB
            if unit == 'MB':
                size = size / 1024
            elif unit == 'TB':
                size = size * 1024

            hardware['disks'].append({
                'size_gb': round(size, 2)
            })

        return hardware

    def _extract_deployment_options(self, output: str) -> List[Dict]:
        """Extract deployment options/configurations"""
        options = []

        # Look for deployment option configurations
        config_pattern = re.compile(r'Configuration\s+"([^"]+)"', re.IGNORECASE)

        for match in config_pattern.finditer(output):
            option_name = match.group(1)
            options.append({
                'id': option_name,
                'label': option_name
            })

        return options

    def _check_vcenter_requirement(self, output: str) -> bool:
        """Check if the OVA requires vCenter (vs standalone ESXi)"""
        # Look for indicators that vCenter is required
        vcenter_indicators = [
            'vcenter',
            'distributed virtual switch',
            'dvs',
            'resource pool',
            'vapp',
            'vm folder'
        ]

        output_lower = output.lower()
        for indicator in vcenter_indicators:
            if indicator in output_lower:
                logger.warning(f"Possible vCenter requirement detected: {indicator}")

        # Most OVAs can be deployed to standalone ESXi
        # This is a conservative check
        return 'requires vcenter' in output_lower or 'vcenter only' in output_lower

    def _extract_warnings(self, output: str) -> List[str]:
        """Extract warning messages"""
        warnings = []

        warning_pattern = re.compile(r'Warning:(.+?)(?:\n|$)', re.IGNORECASE)
        for match in warning_pattern.finditer(output):
            warning = match.group(1).strip()
            if warning:
                warnings.append(warning)

        return warnings

    def _extract_errors(self, output: str) -> List[str]:
        """Extract error messages"""
        errors = []

        error_pattern = re.compile(r'Error:(.+?)(?:\n|$)', re.IGNORECASE)
        for match in error_pattern.finditer(output):
            error = match.group(1).strip()
            if error:
                errors.append(error)

        return errors

    def get_full_probe(self, ova_path: str) -> str:
        """
        Get full probe output for detailed inspection

        Args:
            ova_path: Path to the OVA file

        Returns:
            Raw ovftool output
        """
        try:
            result = subprocess.run(
                [
                    self.ovftool_path,
                    '--hideEula',
                    '--acceptAllEulas',
                    ova_path
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.stdout + "\n\n" + result.stderr
        except Exception as e:
            logger.error(f"Error getting probe: {str(e)}")
            return f"Error: {str(e)}"
