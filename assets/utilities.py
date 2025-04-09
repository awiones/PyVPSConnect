#!/usr/bin/env python3
"""
RemotelyPy Utilities

This module contains utility functions and constants used across the RemotelyPy system.
"""

import sys
import platform
import requests
import socket

__version__ = "2.2.0"
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
║           RemotelyPy v{:8}        ║
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
    """Get the public IP address of the system."""
    try:
        # Try to get the public IP using an external service
        response = requests.get('https://api.ipify.org')
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    try:
        # Fallback to getting local IP if public IP fetch fails
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "0.0.0.0"  # Return default if all methods fail
