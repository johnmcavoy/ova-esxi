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

            output_text = result.stdout + result.stderr
            properties = self._extract_properties(output_text)
            networks = self._extract_networks(output_text)
            hardware = self._extract_hardware(output_text)

            analysis = {
                'file_path': ova_path,
                'file_name': Path(ova_path).name,
                'valid': result.returncode == 0,
                'output': output_text,
                'properties': properties,
                'networks': networks,
                'hardware': hardware,
                'deployment_options': self._extract_deployment_options(output_text),
                'requires_vcenter': self._check_vcenter_requirement(output_text),
                'warnings': self._extract_warnings(output_text),
                'errors': self._extract_errors(output_text),
                'mandatory_fields': self._get_mandatory_fields(properties, networks),
                'amendable_fields': self._get_amendable_fields(hardware)
            }

            logger.info(f"Analysis complete. Valid: {analysis['valid']}, "
                       f"Properties: {len(properties)}, Networks: {len(networks)}")

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

        # Parse the structured Properties section
        # Format:
        # Properties:
        #   Key:         propertyKey
        #   Category:    Category Name
        #   Label:       Property Label
        #   Type:        type
        #   Description: Description text
        #   Value:       default_value

        lines = output.split('\n')
        in_properties_section = False
        current_property = None

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Detect Properties section
            if line.startswith('Properties:'):
                in_properties_section = True
                i += 1
                continue

            # Exit Properties section when we hit another main section
            if in_properties_section and line and not line.startswith(' ') and ':' in line:
                if any(section in line for section in ['Deployment Options:', 'References:', 'Virtual Machines:', 'Networks:']):
                    in_properties_section = False

            if in_properties_section and line.startswith('  '):
                # Parse property fields
                if line.startswith('  Key:'):
                    # Save previous property if exists
                    if current_property and current_property.get('key'):
                        properties.append(current_property)

                    # Start new property
                    key_value = line.split('Key:', 1)[1].strip()
                    current_property = {
                        'key': key_value,
                        'label': key_value.replace('_', ' ').title(),
                        'type': 'string',
                        'description': '',
                        'category': '',
                        'required': False,
                        'value': '',
                        'default_value': ''
                    }

                elif current_property:
                    if line.startswith('  Label:'):
                        current_property['label'] = line.split('Label:', 1)[1].strip()
                    elif line.startswith('  Type:'):
                        current_property['type'] = line.split('Type:', 1)[1].strip()
                    elif line.startswith('  Description:'):
                        desc = line.split('Description:', 1)[1].strip()
                        # Description might span multiple lines
                        j = i + 1
                        while j < len(lines) and lines[j].startswith('               '):
                            desc += ' ' + lines[j].strip()
                            j += 1
                        current_property['description'] = desc
                    elif line.startswith('  Value:'):
                        current_property['default_value'] = line.split('Value:', 1)[1].strip()
                        current_property['value'] = current_property['default_value']
                    elif line.startswith('  Category:'):
                        current_property['category'] = line.split('Category:', 1)[1].strip()

            i += 1

        # Don't forget the last property
        if current_property and current_property.get('key'):
            properties.append(current_property)

        # Mark password fields
        for prop in properties:
            if 'password' in prop['type'].lower() or 'password' in prop['key'].lower():
                prop['type'] = 'password'

            # Check if required based on type (e.g., types without default values)
            if prop['type'] and 'password' in prop['type'].lower():
                prop['required'] = True

        logger.info(f"Extracted {len(properties)} properties from OVA")
        return properties

    def _extract_networks(self, output: str) -> List[Dict]:
        """Extract network mappings from ovftool output"""
        networks = []

        # Pattern: Network "NetworkName" with optional description
        # Look for network blocks in the output
        lines = output.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]

            # Match network name
            network_match = re.search(r'^\s*Name:\s+(.+?)$', line)
            if network_match and i > 0 and 'Networks:' in lines[i-1]:
                network_name = network_match.group(1).strip()
                description = ''

                # Check next line for description
                if i + 1 < len(lines):
                    desc_match = re.search(r'^\s*Description:\s+(.+?)$', lines[i + 1])
                    if desc_match:
                        description = desc_match.group(1).strip()

                # Avoid duplicates
                if network_name not in [n['name'] for n in networks]:
                    networks.append({
                        'name': network_name,
                        'description': description,
                        'target': '',  # To be filled by user
                        'required': True  # All network mappings are required
                    })
            i += 1

        # Fallback: simple pattern matching if structured parsing didn't work
        if not networks:
            network_pattern = re.compile(r'Network\s+"([^"]+)"', re.IGNORECASE)
            for match in network_pattern.finditer(output):
                network_name = match.group(1)
                if network_name not in [n['name'] for n in networks]:
                    networks.append({
                        'name': network_name,
                        'description': '',
                        'target': '',
                        'required': True
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

        # Parse the structured Deployment Options section
        # Format:
        # Deployment Options:
        #   Id:          OptionId
        #   Label:       Option Label
        #   Description: Description text (can span multiple lines)

        lines = output.split('\n')
        in_options_section = False
        current_option = None

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect Deployment Options section
            if line.startswith('Deployment Options:'):
                in_options_section = True
                i += 1
                continue

            # Exit section when we hit another main section
            if in_options_section and line and not line.startswith(' ') and ':' in line:
                if any(section in line for section in ['References:', 'Virtual Machines:', 'Networks:', 'Properties:']):
                    in_options_section = False

            if in_options_section and line.startswith('  '):
                # Parse deployment option fields
                if line.startswith('  Id:'):
                    # Save previous option if exists
                    if current_option and current_option.get('id'):
                        options.append(current_option)

                    # Start new option
                    option_id = line.split('Id:', 1)[1].strip()
                    current_option = {
                        'id': option_id,
                        'label': option_id,
                        'description': ''
                    }

                elif current_option:
                    if line.startswith('  Label:'):
                        current_option['label'] = line.split('Label:', 1)[1].strip()
                    elif line.startswith('  Description:'):
                        desc = line.split('Description:', 1)[1].strip()
                        # Description might span multiple lines
                        j = i + 1
                        while j < len(lines) and lines[j].startswith('               '):
                            desc += ' ' + lines[j].strip()
                            j += 1
                        current_option['description'] = desc

            i += 1

        # Don't forget the last option
        if current_option and current_option.get('id'):
            options.append(current_option)

        logger.info(f"Extracted {len(options)} deployment options from OVA")
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

    def _get_mandatory_fields(self, properties: List[Dict], networks: List[Dict]) -> Dict:
        """
        Identify mandatory fields that must be configured for deployment

        Returns:
            Dictionary categorizing mandatory fields
        """
        mandatory = {
            'vm_name': {
                'field': 'VM Name',
                'description': 'Unique name for the virtual machine',
                'required': True
            },
            'esxi_connection': {
                'host': {'field': 'ESXi Host', 'description': 'IP address or hostname', 'required': True},
                'username': {'field': 'Username', 'description': 'ESXi login username', 'required': True},
                'password': {'field': 'Password', 'description': 'ESXi login password', 'required': True},
                'datastore': {'field': 'Datastore', 'description': 'Storage location for VM files', 'required': True}
            },
            'networks': [],
            'properties': []
        }

        # All networks are mandatory
        for network in networks:
            mandatory['networks'].append({
                'name': network['name'],
                'description': network.get('description', 'Network adapter'),
                'required': True
            })

        # Required OVF properties
        for prop in properties:
            if prop.get('required', False):
                mandatory['properties'].append({
                    'key': prop['key'],
                    'label': prop['label'],
                    'type': prop['type'],
                    'description': prop.get('description', ''),
                    'required': True
                })

        return mandatory

    def _get_amendable_fields(self, hardware: Dict) -> Dict:
        """
        Identify fields that can be modified but are not required

        Returns:
            Dictionary of amendable/optional fields
        """
        amendable = {
            'hardware': {},
            'deployment_settings': {}
        }

        # Hardware can be modified
        if hardware.get('cpus'):
            amendable['hardware']['cpus'] = {
                'field': 'Virtual CPUs',
                'current_value': hardware['cpus'],
                'amendable': True,
                'description': 'Number of virtual CPU cores'
            }

        if hardware.get('memory_mb'):
            amendable['hardware']['memory'] = {
                'field': 'Memory',
                'current_value': f"{hardware['memory_mb']} MB",
                'amendable': True,
                'description': 'Amount of RAM allocated to the VM'
            }

        if hardware.get('disks'):
            amendable['hardware']['disks'] = {
                'field': 'Virtual Disks',
                'current_value': f"{len(hardware['disks'])} disk(s)",
                'amendable': False,  # Disk count typically fixed
                'description': 'Virtual disk configuration (size usually fixed)'
            }

        # Deployment settings
        amendable['deployment_settings'] = {
            'disk_mode': {
                'field': 'Disk Provisioning',
                'options': ['thin', 'thick', 'eagerZeroedThick'],
                'default': 'thin',
                'amendable': True,
                'description': 'How disk space is allocated'
            },
            'power_on': {
                'field': 'Power On After Deployment',
                'options': [True, False],
                'default': False,
                'amendable': True,
                'description': 'Automatically power on VM after deployment'
            }
        }

        return amendable

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
