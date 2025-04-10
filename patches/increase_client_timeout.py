#!/usr/bin/env python3
"""
RemotelyPy Client Timeout Patch

This script patches the RemotelyPy client to increase timeout values,
which can help with slow or unreliable network connections.
"""

import os
import re
import sys
import shutil
import argparse

def backup_file(file_path):
    """Create a backup of the original file."""
    backup_path = f"{file_path}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")
    return backup_path

def patch_client_file(file_path, socket_timeout=60, command_timeout=120):
    """
    Patch the client file to increase timeout values.
    
    Args:
        file_path: Path to the client.py file
        socket_timeout: New socket timeout in seconds
        command_timeout: New command timeout in seconds
    """
    # Create backup
    backup_file(file_path)
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace socket timeout
    content = re.sub(
        r'self\.socket\.settimeout\(30\)',  # Default is 30 seconds
        f'self.socket.settimeout({socket_timeout})',
        content
    )
    
    # Replace command timeout in execute_command
    content = re.sub(
        r'timeout=60(\s+)# Timeout after 60 seconds',
        f'timeout={command_timeout}\\1# Timeout after {command_timeout} seconds',
        content
    )
    
    # Replace command timeout in error message
    content = re.sub(
        r'"Command timed out after 60 seconds"',
        f'"Command timed out after {command_timeout} seconds"',
        content
    )
    
    # Replace command timeout in _handle_user_input
    content = re.sub(
        r'while time\.time\(\) - start_time < 60:(\s+)# Increased timeout to 60 seconds',
        f'while time.time() - start_time < {command_timeout}:\\1# Increased timeout to {command_timeout} seconds',
        content
    )
    
    # Write modified content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Successfully patched {file_path}")
    print(f"- Socket timeout increased to {socket_timeout} seconds")
    print(f"- Command timeout increased to {command_timeout} seconds")

def main():
    parser = argparse.ArgumentParser(description="Patch RemotelyPy client to increase timeouts")
    parser.add_argument("--file", default="assets/client.py", help="Path to client.py file")
    parser.add_argument("--socket-timeout", type=int, default=60, help="Socket timeout in seconds")
    parser.add_argument("--command-timeout", type=int, default=120, help="Command timeout in seconds")
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found")
        return 1
    
    try:
        patch_client_file(args.file, args.socket_timeout, args.command_timeout)
        print("Patch applied successfully")
    except Exception as e:
        print(f"Error applying patch: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())