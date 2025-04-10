#!/usr/bin/env python3
"""
RemotelyPy Client run() Method Fix

This script patches the RemotelyPy client to fix the message processing issue
in the run() method, which is likely causing command timeouts.
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

def patch_run_method(file_path):
    """
    Patch the run() method in the client file to properly process received messages.
    
    Args:
        file_path: Path to the client.py file
    """
    # Create backup
    backup_file(file_path)
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the run method
    run_method_pattern = r'def run\(self\) -> None:.*?while self\.is_connected:.*?message = self\._receive_message\(\).*?time\.sleep\(0\.1\)'
    run_method_match = re.search(run_method_pattern, content, re.DOTALL)
    
    if not run_method_match:
        print("Could not find the run() method in the client file")
        return False
    
    # Get the matched content
    run_method = run_method_match.group(0)
    
    # Replace the message processing part
    fixed_run_method = run_method.replace(
        "message = self._receive_message()",
        "message = self._receive_message()\n                if message:\n                    self._process_message(message)"
    )
    
    # Replace in the original content
    new_content = content.replace(run_method, fixed_run_method)
    
    # Write modified content back
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"Successfully patched run() method in {file_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Fix RemotelyPy client run() method")
    parser.add_argument("--file", default="assets/client.py", help="Path to client.py file")
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found")
        return 1
    
    try:
        if patch_run_method(args.file):
            print("Patch applied successfully")
        else:
            print("Failed to apply patch")
            return 1
    except Exception as e:
        print(f"Error applying patch: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())