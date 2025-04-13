#!/usr/bin/env python3
"""
RemotelyPy - Profile Manager Utility

This script provides a command-line interface for managing RemotelyPy configuration profiles.
"""

import sys
import argparse
import logging
from config_manager import ConfigManager

def create_parser():
    parser = argparse.ArgumentParser(description="RemotelyPy Profile Manager")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List profiles command
    list_parser = subparsers.add_parser('list', help='List all saved profiles')
    list_parser.add_argument('--mode', choices=['client', 'controller', 'all'], default='all',
                           help='Type of profiles to list')
    
    # Show profile command
    show_parser = subparsers.add_parser('show', help='Show details of a specific profile')
    show_parser.add_argument('--mode', choices=['client', 'controller'], required=True,
                           help='Type of profile')
    show_parser.add_argument('--name', required=True, help='Name of the profile to show')
    
    # Delete profile command
    delete_parser = subparsers.add_parser('delete', help='Delete a saved profile')
    delete_parser.add_argument('--mode', choices=['client', 'controller'], required=True,
                             help='Type of profile')
    delete_parser.add_argument('--name', required=True, help='Name of the profile to delete')
    
    # Export profile command
    export_parser = subparsers.add_parser('export', help='Export a profile to a file')
    export_parser.add_argument('--mode', choices=['client', 'controller'], required=True,
                             help='Type of profile')
    export_parser.add_argument('--name', required=True, help='Name of the profile to export')
    export_parser.add_argument('--output', required=True, help='Output file path')
    
    # Import profile command
    import_parser = subparsers.add_parser('import', help='Import a profile from a file')
    import_parser.add_argument('--mode', choices=['client', 'controller'], required=True,
                             help='Type of profile')
    import_parser.add_argument('--name', required=True, help='Name to save the profile as')
    import_parser.add_argument('--input', required=True, help='Input file path')
    
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    config_manager = ConfigManager()
    
    try:
        if args.command == 'list':
            if args.mode in ['client', 'all']:
                client_profiles = config_manager.list_profiles('client')
                print("\nClient Profiles:")
                if client_profiles:
                    for profile in client_profiles:
                        print(f"  - {profile}")
                else:
                    print("  No client profiles found.")
            
            if args.mode in ['controller', 'all']:
                controller_profiles = config_manager.list_profiles('controller')
                print("\nController Profiles:")
                if controller_profiles:
                    for profile in controller_profiles:
                        print(f"  - {profile}")
                else:
                    print("  No controller profiles found.")
        
        elif args.command == 'show':
            config = config_manager.load_profile(args.name, args.mode)
            if config:
                print(f"\nProfile: {args.name} ({args.mode})")
                print("=" * 50)
                for key, value in config.items():
                    print(f"{key}: {value}")
            else:
                print(f"Profile '{args.name}' not found or invalid.")
                return 1
        
        elif args.command == 'delete':
            if config_manager.delete_profile(args.name, args.mode):
                print(f"Profile '{args.name}' deleted successfully.")
            else:
                print(f"Failed to delete profile '{args.name}'.")
                return 1
        
        elif args.command == 'export':
            import json
            
            config = config_manager.load_profile(args.name, args.mode)
            if not config:
                print(f"Profile '{args.name}' not found or invalid.")
                return 1
            
            try:
                with open(args.output, 'w') as f:
                    json.dump(config, f, indent=4)
                print(f"Profile '{args.name}' exported to {args.output}")
            except Exception as e:
                print(f"Failed to export profile: {str(e)}")
                return 1
        
        elif args.command == 'import':
            import json
            
            try:
                with open(args.input, 'r') as f:
                    config = json.load(f)
                
                if config_manager.save_profile(args.name, config, args.mode):
                    print(f"Profile imported and saved as '{args.name}'.")
                else:
                    print("Failed to save imported profile.")
                    return 1
            except Exception as e:
                print(f"Failed to import profile: {str(e)}")
                return 1
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())