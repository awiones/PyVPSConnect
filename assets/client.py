#!/usr/bin/env python3
"""
RemotelyPy Client

This script runs on VPS instances and connects back to a central controller.
It receives commands, executes them, and returns the results to the controller.
"""

import socket
import subprocess
import os
import sys
import json
import ssl
import time
import logging
import uuid
import platform
import argparse
import threading
from typing import Dict, Any, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('remotelypy-client')

class PyVPSClient:
    """Client for PyVPSConnect that runs on VPS instances."""
    
    def __init__(
        self, 
        server_host: str, 
        server_port: int, 
        use_ssl: bool = False,
        ssl_cert: Optional[str] = None,
        reconnect_delay: int = 5,
        client_id: Optional[str] = None
    ):
        """
        Initialize the PyVPSClient.
        
        Args:
            server_host: Hostname or IP of the controller server
            server_port: Port number of the controller server
            use_ssl: Whether to use SSL encryption
            ssl_cert: Path to SSL certificate file for verification
            reconnect_delay: Seconds to wait between reconnection attempts
            client_id: Client identifier (generated if not provided)
        """
        self.server_host = server_host
        self.server_port = server_port
        self.use_ssl = use_ssl
        self.ssl_cert = ssl_cert
        self.reconnect_delay = reconnect_delay
        self.client_id = client_id or str(uuid.uuid4())
        self.socket = None
        self.is_connected = False
        self.system_info = self._gather_system_info()
        
        # Resolve hostname to IP address
        try:
            self.server_ip = socket.gethostbyname(server_host)
        except socket.gaierror:
            self.server_ip = server_host  # Use as-is if resolution fails

    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather system information to send to the controller."""
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "client_id": self.client_id,
            "ip_address": self._get_ip_address()
        }
        
    def _get_ip_address(self) -> str:
        """Get the machine's IP address."""
        try:
            # This creates a socket but doesn't actually connect
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"  # Fallback to localhost
    
    def connect(self) -> bool:
        """
        Connect to the controller server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create a new socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)  # Set timeout to 30 seconds
            
            # Apply SSL if configured
            if self.use_ssl:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                if self.ssl_cert:
                    context.load_verify_locations(self.ssl_cert)
                else:
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    logger.warning("SSL certificate validation is disabled. Connection is encrypted but not verified.")
                
                self.socket = context.wrap_socket(self.socket, server_hostname=self.server_host)
            
            # Connect using the resolved IP address
            logger.info(f"Attempting to connect to {self.server_ip}:{self.server_port}")
            self.socket.connect((self.server_ip, self.server_port))
            self.is_connected = True
            
            # Send initial system information
            if not self._send_message({
                "type": "registration",
                "system_info": self.system_info
            }):
                logger.error("Failed to send registration message")
                self.socket.close()
                self.is_connected = False
                return False
            
            logger.info(f"Connected to controller at {self.server_ip}:{self.server_port}")
            return True
            
        except socket.timeout:
            logger.error("Connection attempt timed out")
            if self.socket:
                self.socket.close()
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            if self.socket:
                self.socket.close()
            self.is_connected = False
            return False
    
    def _send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send a message to the controller.
        
        Args:
            message: Dictionary containing the message
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Convert the message to JSON and add a newline as a message delimiter
            data = json.dumps(message).encode('utf-8') + b'\n'
            self.socket.sendall(data)
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            self.is_connected = False
            return False
    
    def _receive_message(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message from the controller.
        
        Returns:
            Decoded message dictionary or None if reception failed
        """
        try:
            # Read until newline delimiter
            buffer = b''
            while b'\n' not in buffer:
                chunk = self.socket.recv(4096)
                if not chunk:
                    logger.error("Connection closed by server")
                    self.is_connected = False
                    return None
                buffer += chunk
            
            # Split at the first newline
            message_data, remaining = buffer.split(b'\n', 1)
            
            # If there's more data, it's a problem in the protocol implementation
            if remaining:
                logger.warning(f"Received extra data after message delimiter: {remaining}")
            
            # Parse the JSON message
            return json.loads(message_data.decode('utf-8'))
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message as JSON: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {str(e)}")
            self.is_connected = False
            return None
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a shell command and return the result.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Change directory if cd command
            if command.strip().startswith('cd '):
                new_dir = command.strip()[3:]
                try:
                    os.chdir(os.path.expanduser(new_dir))
                    return {
                        "status": "success",
                        "exit_code": 0,
                        "stdout": f"Changed directory to {os.getcwd()}",
                        "stderr": "",
                        "cwd": os.getcwd()
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "error": str(e),
                        "cwd": os.getcwd()
                    }

            # Execute other commands
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60  # Timeout after 60 seconds
            )
            
            return {
                "status": "success",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "cwd": os.getcwd()  # Include current working directory
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "Command timed out after 60 seconds",
                "cwd": os.getcwd()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "cwd": os.getcwd()
            }

    def _send_chat_message(self, message: str) -> bool:
        """Send a chat message to the controller."""
        return self._send_message({
            "type": "chat",
            "message": message,
            "timestamp": time.time()
        })

    def run(self) -> None:
        """
        Main client loop that handles connection and command processing.
        """
        try:
            if not self.connect():
                logger.error("Failed to establish initial connection")
                return

            # Start message input thread
            input_thread = threading.Thread(target=self._handle_user_input)
            input_thread.daemon = True
            input_thread.start()

            while self.is_connected:
                # Receive and process messages from controller
                message = self._receive_message()
                if not message:
                    # Connection lost or invalid message
                    self.is_connected = False
                    break

                # Process message based on type
                if message.get("type") == "command":
                    command_id = message.get("command_id", "unknown")
                    command = message.get("command", "")
                    
                    logger.info(f"Executing command from controller: {command}")
                    result = self.execute_command(command)
                    
                    # Send the result back
                    self._send_message({
                        "type": "command_result",
                        "command_id": command_id,
                        "result": result
                    })
                elif message.get("type") == "ping":
                    self._send_message({
                        "type": "pong",
                        "timestamp": time.time()
                    })

            logger.info("Connection lost. Reconnecting...")
            time.sleep(self.reconnect_delay)
            self.run()  # Attempt to reconnect

        except KeyboardInterrupt:
            logger.info("Client shutting down...")
            if self.socket:
                self.socket.close()
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            if self.socket:
                self.socket.close()
            self.is_connected = False
            time.sleep(self.reconnect_delay)
            self.run()  # Attempt to reconnect

    def _handle_user_input(self) -> None:
        """Handle user input for executing local commands."""
        print("\nYou can now execute commands locally.")
        print("Type '/quit' to exit.")
        
        # Get username for prompt
        try:
            import pwd
            username = pwd.getpwuid(os.getuid()).pw_name
        except:
            username = "user"
        
        hostname = self.system_info.get('hostname', 'unknown')
        current_dir = "~"

        while True:
            try:
                # Update current directory
                current_dir = os.getcwd().replace(os.path.expanduser('~'), '~')
                
                # Create styled prompt
                prompt = f"\n┌──({username}㉿{hostname})-[{current_dir}]\n└─$ "
                command = input(prompt)
                
                if command.strip():
                    if command.strip() == '/quit':
                        logger.info("Exiting...")
                        os._exit(0)
                    
                    if self.is_connected:
                        # Execute command locally and display result
                        result = self.execute_command(command)
                        if result['status'] == 'success':
                            if result.get('stdout'):
                                print(result['stdout'].rstrip())
                            if result.get('stderr'):
                                print(result['stderr'].rstrip(), file=sys.stderr)
                        else:
                            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
                    else:
                        print("Not connected to controller")
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\nUse '/quit' to exit")
                continue
            except Exception as e:
                logger.error(f"Error handling input: {str(e)}")

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="RemotelyPy Client")
    parser.add_argument("--host", required=True, help="Controller server hostname or IP")
    parser.add_argument("--port", type=int, default=5555, help="Controller server port")
    parser.add_argument("--ssl", action="store_true", help="Use SSL encryption")
    parser.add_argument("--cert", help="Path to SSL certificate for verification")
    parser.add_argument("--id", help="Client identifier (UUID generated if not provided)")
    parser.add_argument("--reconnect-delay", type=int, default=5, help="Seconds between reconnection attempts")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        help="Logging level")
    return parser.parse_args()

def main():
    """Main entry point for the client module."""
    args = parse_arguments()
    
    # Set the logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    logger.info("Starting RemotelyPy Client...")
    client = PyVPSClient(
        server_host=args.host,
        server_port=args.port,
        use_ssl=args.ssl,
        ssl_cert=args.cert,
        client_id=args.id,
        reconnect_delay=args.reconnect_delay
    )
    
    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("Client terminated by user")
    return 0

if __name__ == "__main__":
    sys.exit(main())