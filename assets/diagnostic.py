#!/usr/bin/env python3
"""
RemotelyPy Diagnostic Tool

This module provides diagnostic functionality to check system configuration
and requirements for RemotelyPy.
"""

import os
import sys
import socket
import platform
import ssl
import subprocess
import logging
import shutil  # Added missing import
from typing import Dict, List, Tuple

logger = logging.getLogger('remotelypy-diagnostic')

class DiagnosticTool:
    def __init__(self):
        self.results = {
            'system': [],
            'network': [],
            'ssl': [],
            'permissions': []
        }

    def run_all_checks(self) -> bool:
        """Run all diagnostic checks and return overall status."""
        all_passed = True
        
        # System checks
        self._check_python_version()
        self._check_platform()
        self._check_dependencies()
        
        # Network checks
        self._check_network_interfaces()
        self._check_common_ports()
        
        # SSL checks
        self._check_ssl_support()
        self._check_certificates()
        
        # Permission checks
        self._check_directory_permissions()
        self._check_service_permissions()
        
        # Determine if any checks failed
        for category in self.results.values():
            for check in category:
                if not check['status']:
                    all_passed = False
                    
        return all_passed

    def _add_result(self, category: str, name: str, status: bool, message: str) -> None:
        """Add a check result."""
        self.results[category].append({
            'name': name,
            'status': status,
            'message': message
        })

    def _check_python_version(self) -> None:
        """Check Python version compatibility."""
        current_version = tuple(map(int, platform.python_version_tuple()))
        min_version = (3, 6, 0)
        
        status = current_version >= min_version
        message = (f"Python {platform.python_version()} detected. "
                  f"Minimum required: 3.6.0")
        
        self._add_result('system', 'Python Version', status, message)

    def _check_platform(self) -> None:
        """Check platform compatibility."""
        system = platform.system()
        status = system in ('Linux', 'Darwin')
        message = f"Operating System: {system} {platform.release()}"
        
        self._add_result('system', 'Platform', status, message)

    def _check_dependencies(self) -> None:
        """Check required system dependencies."""
        required_commands = ['openssl', 'systemctl', 'netstat']
        
        for cmd in required_commands:
            exists = bool(shutil.which(cmd))
            self._add_result(
                'system',
                f'Command: {cmd}',
                exists,
                f"{'Found' if exists else 'Not found'}: {cmd}"
            )

    def _check_network_interfaces(self) -> None:
        """Check available network interfaces."""
        try:
            # Get default interface
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                default_ip = s.getsockname()[0]
                status = True
                message = f"Default interface IP: {default_ip}"
        except Exception as e:
            status = False
            message = f"Failed to determine network interface: {str(e)}"
            
        self._add_result('network', 'Network Interface', status, message)

    def _check_common_ports(self) -> None:
        """Check if common ports are available."""
        ports = [5555, 443, 80]  # Default RemotelyPy port and common alternatives
        
        for port in ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    status = True
                    message = f"Port {port} is available"
            except Exception:
                status = False
                message = f"Port {port} is in use or unavailable"
            
            self._add_result('network', f'Port {port}', status, message)

    def _check_ssl_support(self) -> None:
        """Check SSL/TLS support."""
        status = True
        message = f"SSL version: {ssl.OPENSSL_VERSION}"
        
        self._add_result('ssl', 'SSL Support', status, message)

    def _check_certificates(self) -> None:
        """Check for SSL certificates."""
        cert_paths = ['cert.pem', 'key.pem']
        
        for cert in cert_paths:
            exists = os.path.exists(cert)
            self._add_result(
                'ssl',
                f'Certificate: {cert}',
                exists,
                f"{'Found' if exists else 'Not found'}: {cert}"
            )

    def _check_directory_permissions(self) -> None:
        """Check directory permissions."""
        paths = [
            '/var/log/remotelypy',
            '/var/run/remotelypy',
            os.path.expanduser('~/.remotelypy')
        ]
        
        for path in paths:
            if os.path.exists(path):
                writable = os.access(path, os.W_OK)
                message = f"{'Writable' if writable else 'Not writable'}: {path}"
            else:
                writable = False
                message = f"Directory does not exist: {path}"
            
            self._add_result('permissions', f'Path: {path}', writable, message)

    def _check_service_permissions(self) -> None:
        """Check service-related permissions."""
        has_sudo = os.geteuid() == 0
        self._add_result(
            'permissions',
            'Root Access',
            has_sudo,
            f"{'Running as root' if has_sudo else 'Not running as root'}"
        )

    def display_results(self) -> None:
        """Display diagnostic results in a formatted way."""
        print("\nRemotelyPy Diagnostic Results")
        print("=" * 50)
        
        for category, checks in self.results.items():
            print(f"\n{category.upper()}")
            print("-" * 50)
            
            for check in checks:
                status_symbol = "✓" if check['status'] else "✗"
                print(f"{status_symbol} {check['name']}: {check['message']}")

def main():
    """Main entry point for diagnostic tool."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Running RemotelyPy diagnostics...\n")
    
    tool = DiagnosticTool()
    all_passed = tool.run_all_checks()
    tool.display_results()
    
    print("\nDiagnostic Summary")
    print("=" * 50)
    if all_passed:
        print("\n✓ All checks passed! RemotelyPy should work correctly.")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
