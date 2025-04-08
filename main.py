#!/usr/bin/env python3
"""
RemotelyPy - Main Entry Point

This script provides a unified interface to run different components
of the RemotelyPy system.
"""

import sys
import argparse
from assets.client import main as client_main
from assets.controller import main as controller_main
from assets.silent_start import main as silent_start_main
from assets.utilities import show_logo, show_version, show_full_version

def create_parser():
    # Display the logo when the program starts
    print(show_logo(small=True))
    
    parser = argparse.ArgumentParser(description="RemotelyPy - VPS Management System")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Version Command
    parser.add_argument('--version', action='store_true', help='Show version information')
    parser.add_argument('--full-version', action='store_true', help='Show detailed version information')

    # Silent Start Command
    silent_parser = subparsers.add_parser('silent-start', help='Install and run as a system service')
    silent_parser.add_argument('--start', action='store_true', help='Start the service')
    silent_parser.add_argument('--stop', action='store_true', help='Stop the service')
    silent_parser.add_argument('--status', action='store_true', help='Check service status')

    # Client Command
    client_parser = subparsers.add_parser('client', help='Run as a client')
    client_parser.add_argument('--host', required=True, help='Controller server hostname or IP')
    client_parser.add_argument('--port', type=int, default=5555, help='Controller server port')
    client_parser.add_argument('--ssl', action='store_true', help='Use SSL encryption')
    client_parser.add_argument('--cert', help='Path to SSL certificate')
    client_parser.add_argument('--id', help='Client identifier')
    client_parser.add_argument('--reconnect-delay', type=int, default=5,
                             help='Seconds between reconnection attempts')
    client_parser.add_argument('--log-level', default="INFO",
                             choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                             help="Logging level")

    # Controller Command
    controller_parser = subparsers.add_parser('controller', help='Run as a controller')
    controller_parser.add_argument('--host', default='0.0.0.0', help='Host interface to bind to')
    controller_parser.add_argument('--port', type=int, default=5555, help='Port to listen on')
    controller_parser.add_argument('--ssl', action='store_true', help='Enable SSL encryption')
    controller_parser.add_argument('--cert', help='Path to SSL certificate file')
    controller_parser.add_argument('--key', help='Path to SSL private key file')
    controller_parser.add_argument('--daemon', action='store_true',
                                 help='Run in daemon mode (background)')
    controller_parser.add_argument('--log-file', help='Log file path (required for daemon mode)')
    controller_parser.add_argument('--pid-file', help='PID file path (for daemon mode)')
    controller_parser.add_argument('--log-level', default="INFO",
                                 choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                                 help="Logging level")

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.version:
        print(show_version())
        return 0
        
    if args.full_version:
        print(show_full_version())
        return 0

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == 'silent-start':
            # Change the way we pass arguments to silent_start
            sys.argv = [sys.argv[0]] + [arg for arg in sys.argv[2:]]
            return silent_start_main()
        elif args.command == 'client':
            sys.argv = [sys.argv[0]] + [arg for arg in sys.argv[2:]]
            return client_main()
        elif args.command == 'controller':
            sys.argv = [sys.argv[0]] + [arg for arg in sys.argv[2:]]
            return controller_main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
