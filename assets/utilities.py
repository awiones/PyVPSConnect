#!/usr/bin/env python3
"""
RemotelyPy Utilities

This module contains utility functions and constants used across the RemotelyPy system.
"""

import sys
import platform
import requests
import socket

__version__ = "2.2.2"
__author__ = "Awiones"
__license__ = "MIT"

# ASCII art logo
LOGO = """
██████╗ ███████╗███╗   ███╗ ██████╗ ████████╗███████╗██╗  ██╗   ██╗██████╗ ██╗   ██╗
██╔══██╗██╔════╝████╗ ████║██╔═══██╗╚══██╔══╝██╔════╝██║  ╚██╗ ██╔╝██╔══██╗╚██╗ ██╔╝
██████╔╝█████╗  ██╔████╔██║██║   ██║   ██║   █████╗  ██║   ╚████╔╝ ██████╔╝ ╚████╔╝ 
██╔══██╗██╔══╝  ██║╚██╔╝██║██║   ██║   ██║   ██╔══╝  ██║    ╚██╔╝  ██╔═══╝   ╚██╔╝  
██║  ██║███████╗██║ ╚═╝ ██║╚██████╔╝   ██║   ███████╗███████╗██║   ██║        ██║   
╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚══════╝╚═╝   ╚═╝        ╚═╝   
"""

# Small banner for less verbose output
SMALL_BANNER = """
╔═══════════════════════════════════════╗
║           RemotelyPy v{:8}      ║
╚═══════════════════════════════════════╝
""".format(__version__)

def show_version():
    """Display version information."""
    return f"RemotelyPy v{__version__}"

def show_full_version():
    """Display detailed version information."""
    return f"""
RemotelyPy v{__version__}
Author: {__author__}
License: {__license__}
Python: {sys.version.split()[0]}
Platform: {platform.system()} {platform.release()}
"""

def show_logo(small=False):
    """
    Display the RemotelyPy logo.
    
    Args:
        small: If True, shows the small banner instead of the full ASCII art
    """
    if small:
        return SMALL_BANNER
    return LOGO

def get_public_ip() -> str:
    """Get the public IP address of the system with improved reliability."""
    # Try multiple services to get public IP
    ip_services = [
        'https://api.ipify.org',
        'https://ifconfig.me/ip',
        'https://icanhazip.com',
        'https://ident.me'
    ]
    
    # First try: AWS EC2 metadata service (specific to EC2 instances)
    try:
        response = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout=2)
        if response.status_code == 200:
            public_ip = response.text.strip()
            if public_ip and public_ip != "0.0.0.0":
                return public_ip
    except:
        pass
    
    # Second try: External IP services
    for service in ip_services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                public_ip = response.text.strip()
                if public_ip and public_ip != "0.0.0.0":
                    return public_ip
        except:
            continue
    
    # Third try: Local IP as fallback
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "0.0.0.0"  # Return default if all methods fail
