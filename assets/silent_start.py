#!/usr/bin/env python3
import os
import sys
import shutil
import pwd
import grp
import subprocess
from pathlib import Path

def get_current_user():
    return pwd.getpwuid(os.getuid()).pw_name

def setup_directories():
    """Create necessary directories for logs and pid files."""
    dirs = {
        '/var/log/remotelypy': 0o755,
        '/var/run/remotelypy': 0o755,
    }
    
    for directory, perms in dirs.items():
        Path(directory).mkdir(parents=True, exist_ok=True)
        os.chmod(directory, perms)
        shutil.chown(directory, user=get_current_user(), group=get_current_user())
    
    return True

def create_systemd_service():
    """Create and install systemd service file."""
    service_content = f"""[Unit]
Description=RemotelyPy Controller Service
After=network.target

[Service]
Type=forking
User={get_current_user()}
Group={get_current_user()}
ExecStart=/usr/bin/python3 {os.path.abspath('controller.py')} --daemon \\
    --log-file /var/log/remotelypy/controller.log \\
    --pid-file /var/run/remotelypy/controller.pid \\
    --host %I \\
    --port 5555
PIDFile=/var/run/remotelypy/controller.pid
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
    
    service_path = '/etc/systemd/system/remotelypy-controller@.service'  # Note the @ for templating
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        os.chmod(service_path, 0o644)
        return True
    except PermissionError:
        print("Error: Need root privileges to create service file")
        return False

def reload_systemd():
    """Reload systemd daemon."""
    try:
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to reload systemd")
        return False

def enable_and_start_service():
    """Enable and start the service."""
    try:
        host = input("Enter IP/hostname to bind to [0.0.0.0]: ").strip() or "0.0.0.0"
        service_name = f"remotelypy-controller@{host}"
        subprocess.run(['systemctl', 'enable', service_name], check=True)
        subprocess.run(['systemctl', 'start', service_name], check=True)
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to enable/start service")
        return False

def detect_init_system():
    """Detect the init system being used."""
    # Check for systemd
    if os.path.exists('/run/systemd/system'):
        return 'systemd'
    # Check for upstart
    elif os.path.exists('/etc/init'):
        return 'upstart'
    # Assume sysvinit or other
    else:
        return 'other'

def create_init_script():
    """Create a classic init.d script for non-systemd systems."""
    script_content = f"""#!/bin/sh
### BEGIN INIT INFO
# Provides:          remotelypy-controller
# Required-Start:    $network $remote_fs
# Required-Stop:     $network $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Description:       RemotelyPy Controller Service
### END INIT INFO

BIND_ADDRESS="0.0.0.0"  # Can be changed in /etc/default/remotelypy-controller
[ -f /etc/default/remotelypy-controller ] && . /etc/default/remotelypy-controller

DAEMON="/usr/bin/python3 {os.path.abspath('controller.py')}"
DAEMON_OPTS="--daemon --log-file /var/log/remotelypy/controller.log --pid-file /var/run/remotelypy/controller.pid --host $BIND_ADDRESS --port 5555"
NAME="remotelypy-controller"
PIDFILE="/var/run/remotelypy/controller.pid"
USER="{get_current_user()}"

case "$1" in
    "start")
        echo "Starting $NAME..."
        start-stop-daemon --start --background --make-pidfile --pidfile $PIDFILE \\
            --chuid $USER --exec $DAEMON -- $DAEMON_OPTS
        ;;
    "stop")
        echo "Stopping $NAME..."
        start-stop-daemon --stop --pidfile $PIDFILE --retry 5
        ;;
    "restart")
        $0 "stop"
        $0 "start"
        ;;
    "status")
        if [ -f $PIDFILE ]; then
            if kill -0 $(cat $PIDFILE) 2>/dev/null; then
                echo "$NAME is running"
                exit 0
            fi
        fi
        echo "$NAME is not running"
        exit 1
        ;;
    *)
        echo "Usage: $0 {'start|stop|restart|status'}"
        exit 1
        ;;
esac

exit 0"""
    
    script_path = '/etc/init.d/remotelypy-controller'
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        return True
    except PermissionError:
        print("Error: Need root privileges to create init script")
        return False

    # Create default configuration file
    default_config = "BIND_ADDRESS=\"0.0.0.0\"\n"
    try:
        with open('/etc/default/remotelypy-controller', 'w') as f:
            f.write(default_config)
    except:
        print("Warning: Could not create default configuration file")

def setup_service():
    """Set up the service based on the init system."""
    init_system = detect_init_system()
    print(f"Detected init system: {init_system}")
    
    if init_system == 'systemd':
        if not create_systemd_service():
            return False
        if not reload_systemd():
            return False
        if not enable_and_start_service():
            return False
    else:
        if not create_init_script():
            return False
        # For non-systemd systems, manually start the service
        try:
            subprocess.run(['/etc/init.d/remotelypy-controller', 'start'], check=True)
            # Try to enable on boot if update-rc.d exists
            if os.path.exists('/usr/sbin/update-rc.d'):
                subprocess.run(['update-rc.d', 'remotelypy-controller', 'defaults'], check=True)
            return True
        except subprocess.CalledProcessError:
            print("Error: Failed to start service")
            return False
    return True

def stop_service():
    """Stop the service and all connections."""
    init_system = detect_init_system()
    
    try:
        if init_system == 'systemd':
            # List all running instances
            result = subprocess.run(['systemctl', 'list-units', 'remotelypy-controller@*', '--no-legend'], 
                                 capture_output=True, text=True)
            for line in result.stdout.splitlines():
                service_name = line.split()[0]
                subprocess.run(['systemctl', 'stop', service_name], check=True)
        else:
            subprocess.run(['/etc/init.d/remotelypy-controller', 'stop'], check=True)
        print("Service stopped successfully")
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to stop service")
        return False

def status_service():
    """Check service status."""
    init_system = detect_init_system()
    
    try:
        if init_system == 'systemd':
            subprocess.run(['systemctl', 'status', 'remotelypy-controller'], check=False)
        else:
            subprocess.run(['/etc/init.d/remotelypy-controller', 'status'], check=False)
        return True
    except subprocess.CalledProcessError:
        return False

def parse_arguments():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="RemotelyPy Service Manager")
    parser.add_argument('--start', action='store_true', help='Start the service')
    parser.add_argument('--stop', action='store_true', help='Stop the service')
    parser.add_argument('--status', action='store_true', help='Check service status')
    return parser.parse_args()

def main():
    """Main entry point for the silent start module."""
    if os.geteuid() != 0:
        print("Error: This script must be run as root")
        return 1

    args = parse_arguments()
    
    if args.stop:
        return 0 if stop_service() else 1
    elif args.status:
        return 0 if status_service() else 1
    elif args.start:
        print("Setting up RemotelyPy Controller...")
        steps = [
            ("Creating directories", setup_directories),
            ("Installing and starting service", setup_service)
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"Failed at: {step_name}")
                return 1
            print("Done!")
        
        print("\nRemotelyPy Controller has been installed and started!")
        print("You can check its status with:")
        if detect_init_system() == 'systemd':
            print("  systemctl status remotelypy-controller")
        else:
            print("  /etc/init.d/remotelypy-controller status")
        print("View logs with: tail -f /var/log/remotelypy/controller.log")
    else:
        print("Error: No action specified. Use --start, --stop, or --status")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
