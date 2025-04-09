#!/usr/bin/env python3
"""
RemotelyPy Controller

This script runs on your local machine and manages connections with multiple VPS clients.
It can send commands to individual or all connected clients and display their responses.
"""

import socket
import threading
import json
import ssl
import logging
import argparse
import sys
import time
import os
import datetime
import subprocess  # Add this import
from typing import Dict, List, Any, Optional, Tuple, Set
import uuid
from collections import defaultdict
from assets.utilities import get_public_ip

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('remotelypy-controller')

class ClientConnection:
    """Manages an individual client connection."""
    
    def __init__(self, client_socket, address, controller):
        """
        Initialize a client connection.
        
        Args:
            client_socket: Connected socket object
            address: Client address tuple (ip, port)
            controller: Reference to the main controller
        """
        self.socket = client_socket
        self.address = address
        self.controller = controller
        self.client_id = None
        self.system_info = {}
        self.connected_time = datetime.datetime.now()
        self.last_seen = datetime.datetime.now()
        self.is_active = True
        self.response_handlers = {}
        self.lock = threading.Lock()
        
        # Start the client handler in a separate thread
        self.thread = threading.Thread(target=self._handle_client)
        self.thread.daemon = True
        self.thread.start()
    
    def _handle_client(self) -> None:
        """Handle communication with this client."""
        buffer = b''
        
        try:
            while self.is_active:
                try:
                    # Receive data with timeout
                    self.socket.settimeout(60)  # 60 second timeout
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        logger.info(f"Client {self.get_identifier()} disconnected")
                        break
                    
                    buffer += chunk
                    
                    # Process complete messages (delimited by newlines)
                    while b'\n' in buffer:
                        try:
                            message_data, buffer = buffer.split(b'\n', 1)
                            self._process_message(message_data)
                        except ValueError:
                            # Invalid message format, clear buffer
                            logger.warning(f"Invalid message format from {self.get_identifier()}, clearing buffer")
                            buffer = b''
                            break
                        
                except socket.timeout:
                    # Send ping on timeout to check connection
                    if not self.send_ping():
                        break
                    continue
                    
        except Exception as e:
            logger.error(f"Error handling client {self.get_identifier()}: {str(e)}")
        finally:
            self._cleanup()
    
    def _process_message(self, message_data: bytes) -> None:
        """
        Process a received message.
        
        Args:
            message_data: Raw message bytes
        """
        try:
            # Check if message_data is empty or invalid
            if not message_data or not message_data.strip():
                logger.warning(f"Received empty message from {self.get_identifier()}")
                return

            # Try to decode and parse the message
            try:
                decoded_data = message_data.decode('utf-8')
                message = json.loads(decoded_data)
            except UnicodeDecodeError:
                logger.error(f"Invalid UTF-8 data received from {self.get_identifier()}")
                return
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from {self.get_identifier()}: {str(e)}")
                logger.debug(f"Raw message: {message_data}")
                return

            self.last_seen = datetime.datetime.now()
            
            message_type = message.get('type')
            
            if message_type == 'registration':
                # Handle client registration
                self.system_info = message.get('system_info', {})
                self.client_id = self.system_info.get('client_id')
                logger.info(f"Client registered: {self.get_identifier()}")
                
                # Notify controller of successful registration
                self.controller.client_registered(self)
                
            elif message_type == 'chat':
                # Handle chat message
                chat_msg = message.get('message', '')
                logger.info(f"Chat from {self.get_identifier()}: {chat_msg}")
                
                # Broadcast to all other clients
                broadcast_msg = {
                    "type": "chat",
                    "message": chat_msg,
                    "sender": self.get_identifier(),
                    "timestamp": message.get('timestamp', time.time())
                }
                
                # Broadcast to all other clients
                self.controller.broadcast_message(broadcast_msg, exclude=self)
                
            elif message_type == 'command_result':
                # Handle command result
                command_id = message.get('command_id')
                result = message.get('result', {})
                
                with self.lock:
                    # Check if we have a handler for this command
                    if command_id in self.response_handlers:
                        callback = self.response_handlers.pop(command_id)
                        callback(result)
                    else:
                        logger.warning(f"Received result for unknown command ID: {command_id}")
                        
            elif message_type == 'command_response':
                # Handle response to a command request
                command_id = message.get('command_id')
                result = message.get('result', {})
                
                with self.lock:
                    # Check if we have a handler for this command
                    if command_id in self.response_handlers:
                        callback = self.response_handlers.pop(command_id)
                        callback(result)
                    else:
                        logger.warning(f"Received response for unknown command ID: {command_id}")
                        
            elif message_type == 'pong':
                # Handle ping response (just update last_seen which is already done)
                pass
                
            elif message_type == 'command_request':
                # Handle command request from client
                command_id = message.get('command_id', 'unknown')
                command = message.get('command', '')
                
                logger.info(f"Received command request from {self.get_identifier()}: {command}")
                
                # Execute the command on the controller
                result = self.controller._execute_command(command)
                
                # Send the result back to the client
                self._send_message({
                    "type": "command_response",
                    "command_id": command_id,
                    "result": result
                })
                
            else:
                logger.warning(f"Received unknown message type from {self.get_identifier()}: {message_type}")
                
        except Exception as e:
            logger.error(f"Error processing message from {self.get_identifier()}: {str(e)}")
    
    def send_command(self, command: str, callback=None) -> str:
        """
        Send a command to this client.
        
        Args:
            command: Shell command to execute
            callback: Function to call with the result
            
        Returns:
            Command ID
        """
        command_id = str(uuid.uuid4())
        
        message = {
            "type": "command",
            "command_id": command_id,
            "command": command
        }
        
        with self.lock:
            if callback:
                self.response_handlers[command_id] = callback
        
        self._send_message(message)
        return command_id
    
    def send_ping(self) -> bool:
        """
        Send a ping to check if the client is still connected.
        
        Returns:
            True if the ping was sent successfully
        """
        return self._send_message({
            "type": "ping",
            "timestamp": time.time()
        })
        
    def request_command(self, command: str, callback=None) -> str:
        """
        Send a command request to the controller.
        
        Args:
            command: Shell command to execute on the controller
            callback: Function to call with the result
            
        Returns:
            Command ID
        """
        command_id = str(uuid.uuid4())
        
        message = {
            "type": "command_request",
            "command_id": command_id,
            "command": command
        }
        
        with self.lock:
            if callback:
                self.response_handlers[command_id] = callback
        
        self._send_message(message)
        return command_id
    
    def _send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send a message to the client.
        
        Args:
            message: Dictionary message to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Convert message to JSON and add newline delimiter
            data = json.dumps(message).encode('utf-8') + b'\n'
            self.socket.sendall(data)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {self.get_identifier()}: {str(e)}")
            self._cleanup()  # Mark as inactive and remove from controller
            return False
    
    def get_identifier(self) -> str:
        """Get a human-readable identifier for this client."""
        if self.client_id:
            hostname = self.system_info.get('hostname', 'unknown')
            return f"{hostname} ({self.client_id[:8]})"
        else:
            return f"{self.address[0]}:{self.address[1]}"
    
    def get_info(self) -> Dict[str, Any]:
        """Get complete information about this client."""
        return {
            "client_id": self.client_id,
            "address": f"{self.address[0]}:{self.address[1]}",
            "connected_time": self.connected_time.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "system_info": self.system_info
        }
    
    def _cleanup(self) -> None:
        """Clean up resources when connection is lost."""
        if self.is_active:
            self.is_active = False
            try:
                self.socket.close()
            except Exception:
                pass
            
            # Notify controller that this client is gone
            self.controller.client_disconnected(self)
            
            # Call any pending callbacks with error
            with self.lock:
                for command_id, callback in self.response_handlers.items():
                    callback({
                        "status": "error",
                        "error": "Client disconnected before receiving response"
                    })
                self.response_handlers.clear()

class RemotelyPyController:
    """Main controller for managing RemotelyPy clients."""
    
    def __init__(
        self, 
        host: str = '0.0.0.0', 
        port: int = 5555,
        use_ssl: bool = False,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        auth_token: Optional[str] = None
    ):
        """
        Initialize the RemotelyPyController.
        
        Args:
            host: Host interface to bind to (or public IP for display only)
            port: Port to listen on
            use_ssl: Whether to use SSL encryption
            cert_file: Path to SSL certificate file
            key_file: Path to SSL private key file
            auth_token: Optional authentication token for clients
        """
        # Always bind to 0.0.0.0 (all interfaces) for maximum compatibility
        self.bind_ip = '0.0.0.0'
        self.port = port
        self.use_ssl = use_ssl
        self.cert_file = cert_file
        self.key_file = key_file
        self.auth_token = auth_token
        
        # Handle public IP address determination
        if host and host not in ['0.0.0.0', 'localhost', '127.0.0.1']:
            # If a specific public IP was provided, use it
            self.public_ip = host
        else:
            # Otherwise try to detect it
            self.public_ip = get_public_ip()
        
        self.clients = {}  # Maps client_id to ClientConnection objects
        self.clients_lock = threading.Lock()
        
        self.server_socket = None
        self.is_running = False
        self.main_thread = None
        
        # Set up health check thread
        self.health_check_thread = threading.Thread(target=self._health_check_loop)
        self.health_check_thread.daemon = True

    def _get_private_ip(self) -> str:
        """Get the private IP address of the machine."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "unknown"

    def start(self) -> bool:
        """
        Start the controller server.
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Wrap with SSL if configured
            if self.use_ssl:
                if not (self.cert_file and self.key_file and 
                        os.path.exists(self.cert_file) and os.path.exists(self.key_file)):
                    logger.error("SSL enabled but certificate or key file not found")
                    return False
                
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
                self.server_socket = context.wrap_socket(self.server_socket, server_side=True)
            
            # Bind to all interfaces (0.0.0.0) to accept connections on both public and private IPs
            try:
                self.server_socket.bind((self.bind_ip, self.port))
            except socket.error as e:
                logger.error(f"Could not bind to {self.bind_ip}: {e}")
                return False
                
            self.server_socket.listen(5)
            self.is_running = True
            
            # Verify we have a valid public IP for clients to connect to
            if self.public_ip == '0.0.0.0' or self.public_ip == 'localhost' or self.public_ip == '127.0.0.1':
                logger.warning("Could not determine public IP address. Clients may have trouble connecting.")
                logger.warning("Consider specifying your public IP with --host parameter.")
            
            # Show detailed network information
            private_ip = self._get_private_ip()
            logger.info("RemotelyPy Controller Network Information:")
            logger.info("-" * 50)
            logger.info(f"Binding Address: {self.bind_ip}:{self.port} (listening on all interfaces)")
            logger.info(f"Private Network: {private_ip}:{self.port}")
            logger.info(f"Public Address: {self.public_ip}:{self.port} (for client connections)")
            logger.info("-" * 50)
            logger.info("Firewall Configuration:")
            logger.info(f"- Ensure port {self.port} is open for incoming TCP connections")
            logger.info("- If connection fails, verify firewall rules")
            logger.info("-" * 50)
            
            # Start the main server thread
            self.main_thread = threading.Thread(target=self._accept_connections)
            self.main_thread.daemon = True
            self.main_thread.start()
            
            # Start health check thread
            self.health_check_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server: {str(e)}")
            if self.server_socket:
                self.server_socket.close()
            return False
    
    def stop(self) -> None:
        """Stop the controller and disconnect all clients."""
        logger.info("Stopping controller server...")
        
        self.is_running = False
        
        # Close the server socket to stop accepting new connections
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        
        # Disconnect all clients
        with self.clients_lock:
            client_copies = list(self.clients.values())
        
        for client in client_copies:
            try:
                client.socket.close()
            except Exception:
                pass
        
        logger.info("Controller server stopped")
    
    def _accept_connections(self) -> None:
        """Accept incoming client connections."""
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                logger.info(f"New connection from {address[0]}:{address[1]}")
                
                # Create a new client connection
                ClientConnection(client_socket, address, self)
                
            except OSError:
                # Socket was closed, likely during shutdown
                if not self.is_running:
                    break
            except Exception as e:
                logger.error(f"Error accepting connection: {str(e)}")
    
    def _health_check_loop(self) -> None:
        """Periodically check health of client connections."""
        while self.is_running:
            time.sleep(30)  # Check every 30 seconds
            
            if not self.is_running:
                break
                
            current_time = datetime.datetime.now()
            
            with self.clients_lock:
                client_copies = list(self.clients.values())
            
            for client in client_copies:
                # If client hasn't been seen in 2 minutes, ping it
                if (current_time - client.last_seen).total_seconds() > 120:
                    if not client.send_ping():
                        # Failed to send ping, client will clean itself up
                        continue
    
    def client_registered(self, client: ClientConnection) -> None:
        """
        Handle client registration.
        
        Args:
            client: The client connection object
        """
        if not client.client_id:
            logger.warning(f"Client from {client.address[0]}:{client.address[1]} registered without client_id")
            return
        
        with self.clients_lock:
            # If we already have this client ID, disconnect the old one
            if client.client_id in self.clients:
                old_client = self.clients[client.client_id]
                logger.info(f"Replacing existing connection for {client.get_identifier()}")
                old_client.socket.close()
            
            # Add the new client
            self.clients[client.client_id] = client
    
    def client_disconnected(self, client: ClientConnection) -> None:
        """
        Handle client disconnection.
        
        Args:
            client: The client connection object
        """
        if client.client_id:
            with self.clients_lock:
                if client.client_id in self.clients and self.clients[client.client_id] is client:
                    logger.info(f"Removing disconnected client: {client.get_identifier()}")
                    del self.clients[client.client_id]
    
    def get_clients(self) -> List[Dict[str, Any]]:
        """
        Get a list of all connected clients.
        
        Returns:
            List of client information dictionaries
        """
        with self.clients_lock:
            return [client.get_info() for client in self.clients.values() if client.is_active]
    
    def get_client_by_id(self, client_id: str) -> Optional[ClientConnection]:
        """
        Get a client by its ID.
        
        Args:
            client_id: The client identifier
            
        Returns:
            ClientConnection object or None if not found
        """
        with self.clients_lock:
            # Try exact match first
            if client_id in self.clients:
                return self.clients[client_id]
            
            # Try partial match (starts with)
            for cid, client in self.clients.items():
                if cid.startswith(client_id):
                    return client
            
            return None
    
    def send_command(self, command: str, client_ids: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Send a command to one or more clients.
        
        Args:
            command: Shell command to execute
            client_ids: List of client IDs to send to (None for all clients)
            
        Returns:
            Dictionary mapping client IDs to command IDs
        """
        results = {}
        
        with self.clients_lock:
            # Determine which clients to target
            target_clients = []
            if client_ids is None:
                # Send to all clients
                target_clients = list(self.clients.values())
            else:
                # Send to specific clients
                for client_id in client_ids:
                    client = self.get_client_by_id(client_id)
                    if client:
                        target_clients.append(client)
                    else:
                        logger.warning(f"Client ID not found: {client_id}")
        
        # Send the command to each target client
        for client in target_clients:
            if client.is_active:
                command_id = client.send_command(command)
                results[client.client_id] = command_id
        
        return results

    def broadcast_message(self, message: Dict[str, Any], exclude: Optional[ClientConnection] = None) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast
            exclude: Optional client to exclude from broadcast
        """
        with self.clients_lock:
            for client in self.clients.values():
                if client.is_active and client != exclude:
                    client._send_message(message)
                    
    def _execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a shell command on the controller and return the result.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Handle cd command specially
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

class CommandLineInterface:
    """Command-line interface for the RemotelyPyController."""
    
    def __init__(self, controller: RemotelyPyController):
        """
        Initialize the CLI.
        
        Args:
            controller: RemotelyPyController instance
        """
        self.controller = controller
        self.running = False
        self.pending_commands = defaultdict(dict)  # {command_id: {client_id: result}}
        self.commands_lock = threading.Lock()
    
    def start(self) -> None:
        """Start the CLI and enter the main loop."""
        self.running = True
        self.show_help()
        
        while self.running:
            try:
                command = input("\nRemotelyPy> ").strip()
                
                if not command:
                    continue
                
                self.process_command(command)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' command to quit")
            except EOFError:
                self.running = False
                print("\nExiting...")
    
    def show_help(self) -> None:
        """Show help information."""
        print("\nRemotelyPy Controller - Available Commands:")
        print("  help             - Show this help message")
        print("  list             - List all connected clients")
        print("  info <client_id> - Show detailed information about a client")
        print("  cmd <command>    - Send command to all clients")
        print("  cmd <client_id> <command> - Send command to a specific client")
        print("  shell <client_id> - Enter interactive shell mode with a client")
        print("  local <command>  - Execute command locally on the controller")
        print("  exit             - Exit the controller")
    
    def process_command(self, command_line: str) -> None:
        """
        Process a command entered in the CLI.
        
        Args:
            command_line: The complete command line input
        """
        parts = command_line.split(maxsplit=1)
        command = parts[0].lower()
        
        if command == "help":
            self.show_help()
            
        elif command == "exit":
            self.running = False
            self.controller.stop()
            
        elif command == "list":
            self.list_clients()
            
        elif command == "info":
            if len(parts) < 2:
                print("Error: Client ID required")
                return
                
            self.show_client_info(parts[1])
            
        elif command == "cmd":
            if len(parts) < 2:
                print("Error: Command required")
                return
                
            cmd_parts = parts[1].split(maxsplit=1)
            
            if len(cmd_parts) == 1:
                # Send to all clients
                self.send_command_to_all(cmd_parts[0])
            else:
                # Check if first part is a client ID
                client_id = cmd_parts[0]
                cmd = cmd_parts[1]
                
                client = self.controller.get_client_by_id(client_id)
                if client:
                    self.send_command_to_client(client, cmd)
                else:
                    # Assume the whole thing is a command for all clients
                    self.send_command_to_all(parts[1])
                    
        elif command == "shell":
            if len(parts) < 2:
                print("Error: Client ID required")
                return
            self.start_interactive_shell(parts[1])
            return
            
        elif command == "local":
            if len(parts) < 2:
                print("Error: Command required")
                return
            self.execute_local_command(parts[1])
            return
            
        else:
            print(f"Unknown command: {command}")
    
    def list_clients(self) -> None:
        """List all connected clients."""
        clients = self.controller.get_clients()
        
        if not clients:
            print("No clients connected")
            return
            
        print(f"\n{'ID':<10} {'Hostname':<20} {'IP Address':<15} {'Connected Since':<25}")
        print("-" * 70)
        
        for client in clients:
            client_id = client['client_id'][:8]  # Show first 8 chars of UUID
            hostname = client['system_info'].get('hostname', 'unknown')
            ip = client['address'].split(':')[0]
            connected_time = client['connected_time'].split('.')[0]  # Remove microseconds
            
            print(f"{client_id:<10} {hostname:<20} {ip:<15} {connected_time:<25}")
    
    def show_client_info(self, client_id: str) -> None:
        """
        Show detailed information about a client.
        
        Args:
            client_id: The client identifier (can be partial)
        """
        # Find clients that match the partial ID
        matching_clients = []
        for client in self.controller.get_clients():
            if client['client_id'].startswith(client_id):
                matching_clients.append(client)
        
        if not matching_clients:
            print(f"No clients found with ID starting with '{client_id}'")
            return
            
        if len(matching_clients) > 1:
            print(f"Multiple clients found matching '{client_id}':")
            for client in matching_clients:
                print(f"  {client['client_id'][:8]} - {client['system_info'].get('hostname', 'unknown')}")
            return
            
        # Display detailed information for the single matched client
        client = matching_clients[0]
        
        print(f"\nClient Information - {client['system_info'].get('hostname', 'unknown')}")
        print("-" * 50)
        print(f"Client ID:      {client['client_id']}")
        print(f"IP Address:     {client['address']}")
        print(f"Connected:      {client['connected_time']}")
        print(f"Last Seen:      {client['last_seen']}")
        print(f"Platform:       {client['system_info'].get('platform', 'unknown')} {client['system_info'].get('platform_version', '')}")
        print(f"Python Version: {client['system_info'].get('python_version', 'unknown').split()[0]}")
    
    def send_command_to_all(self, command: str) -> None:
        """
        Send a command to all connected clients.
        
        Args:
            command: Shell command to execute
        """
        clients = self.controller.get_clients()
        
        if not clients:
            print("No clients connected")
            return
            
        print(f"Sending command to {len(clients)} client(s): {command}")
        
        # Initialize result tracking
        command_id = str(uuid.uuid4())
        with self.commands_lock:
            for client in clients:
                self.pending_commands[command_id][client['client_id']] = None
        
        # Define callback for handling results
        def handle_result(client_id, result):
            with self.commands_lock:
                self.pending_commands[command_id][client_id] = result
                
                # Check if all results are in
                all_received = all(v is not None for v in self.pending_commands[command_id].values())
                
                if all_received:
                    # Display all results
                    self.display_command_results(command_id)
        
        # Send to each client
        for client in clients:
            client_id = client['client_id']
            client_obj = self.controller.get_client_by_id(client_id)
            
            if client_obj:
                client_obj.send_command(
                    command, 
                    callback=lambda result, cid=client_id: handle_result(cid, result)
                )
    
    def send_command_to_client(self, client: ClientConnection, command: str) -> None:
        """
        Send a command to a specific client.
        
        Args:
            client: The client connection object
            command: Shell command to execute
        """
        print(f"Sending command to {client.get_identifier()}: {command}")
        
        def handle_result(result):
            self.display_single_result(client.get_identifier(), result)
        
        client.send_command(command, callback=handle_result)
    
    def display_command_results(self, command_id: str) -> None:
        """
        Display results from all clients for a specific command.
        
        Args:
            command_id: The command identifier
        """
        with self.commands_lock:
            results = self.pending_commands.pop(command_id, {})
        
        print("\nCommand Results:")
        print("-" * 50)
        
        for client_id, result in results.items():
            client = self.controller.get_client_by_id(client_id)
            identifier = client.get_identifier() if client else client_id[:8]
            
            print(f"\n[{identifier}]")
            self._print_result(result)
    
    def display_single_result(self, identifier: str, result: Dict[str, Any]) -> None:
        """
        Display result from a single client.
        
        Args:
            identifier: The client identifier
            result: The command result dictionary
        """
        print(f"\nResult from {identifier}:")
        print("-" * 50)
        self._print_result(result)
    
    def _print_result(self, result: Dict[str, Any]) -> None:
        """
        Print a command result in a readable format.
        
        Args:
            result: The command result dictionary
        """
        if result is None:
            print("No response received")
            return
            
        status = result.get('status')
        
        if status == 'success':
            exit_code = result.get('exit_code', 0)
            print(f"Exit Code: {exit_code}")
            
            if result.get('stdout'):
                print("\nStandard Output:")
                print(result['stdout'].rstrip())
                
            if result.get('stderr'):
                print("\nStandard Error:")
                print(result['stderr'].rstrip())
                
        elif status == 'error':
            print(f"Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"Unknown result format: {result}")

    def start_interactive_shell(self, client_id: str) -> None:
        """Start an interactive shell session with a client."""
        client = self.controller.get_client_by_id(client_id)
        if not client:
            print(f"No client found with ID starting with '{client_id}'")
            return
            
    def execute_local_command(self, command: str) -> None:
        """
        Execute a command locally on the controller.
        
        Args:
            command: Shell command to execute
        """
        print(f"Executing local command: {command}")
        result = self.controller._execute_command(command)
        
        if result.get('status') == 'success':
            print(f"\nExit Code: {result.get('exit_code', 0)}")
            
            if result.get('stdout'):
                print("\nStandard Output:")
                print(result['stdout'].rstrip())
                
            if result.get('stderr'):
                print("\nStandard Error:")
                print(result['stderr'].rstrip())
                
            print(f"\nCurrent directory: {result.get('cwd', os.getcwd())}")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")

        print(f"\nStarting interactive shell with {client.get_identifier()}")
        print("Type 'exit' to return to controller shell")
        
        current_dir = "~"  # Will be updated with first command response
        
        while True:
            try:
                # Show prompt with hostname and current directory
                command = input(f"\n{client.system_info.get('hostname', 'remote')}:{current_dir}$ ").strip()
                
                if not command:
                    continue
                    
                if command.lower() == 'exit':
                    print("Exiting interactive shell")
                    break
                
                # Send command and wait for result
                result = None
                def handle_result(cmd_result):
                    nonlocal result
                    result = cmd_result
                
                client.send_command(command, callback=handle_result)
                
                # Wait for result
                while result is None:
                    time.sleep(0.1)
                
                # Update current directory if provided
                if result.get('cwd'):
                    current_dir = result['cwd'].replace(os.path.expanduser('~'), '~')
                
                # Display result
                if result.get('status') == 'success':
                    if result.get('stdout'):
                        print(result['stdout'].rstrip())
                    if result.get('stderr'):
                        print(result['stderr'].rstrip(), file=sys.stderr)
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to return to controller shell")
            except EOFError:
                break

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="RemotelyPy Controller")
    parser.add_argument("--host", help="Public IP address for clients to connect to (defaults to auto-detected)")
    parser.add_argument("--port", type=int, default=5555, help="Port to listen on")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL encryption")
    parser.add_argument("--cert", help="Path to SSL certificate file")
    parser.add_argument("--key", help="Path to SSL private key file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        help="Logging level")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode (background)")
    parser.add_argument("--log-file", help="Log file path (required for daemon mode)")
    parser.add_argument("--pid-file", help="PID file path (for daemon mode)")
    return parser.parse_args()

def setup_daemon_logging(log_file: str) -> None:
    """Setup logging for daemon mode."""
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logging.getLogger().handlers = [file_handler]

def write_pid_file(pid_file: str) -> None:
    """Write PID to file."""
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

def main():
    """Main entry point for the controller module."""
    args = parse_arguments()
    
    # Set the logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    if args.daemon:
        if not args.log_file:
            print("Error: --log-file is required for daemon mode")
            return 1
            
        # Fork the process
        try:
            pid = os.fork()
            if pid > 0:
                # Exit parent process
                sys.exit(0)
        except OSError as err:
            print(f'Fork failed: {err}')
            sys.exit(1)
            
        # Decouple from parent environment
        os.chdir('/')
        os.umask(0)
        os.setsid()
        
        # Fork again
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as err:
            print(f'Fork failed: {err}')
            sys.exit(1)
            
        # Setup daemon logging
        setup_daemon_logging(args.log_file)
        
        # Write PID file if specified
        if args.pid_file:
            write_pid_file(args.pid_file)
    
    # Create and start the controller
    controller = RemotelyPyController(
        host=args.host if args.host else get_public_ip(),
        port=args.port,
        use_ssl=args.ssl,
        cert_file=args.cert,
        key_file=args.key
    )
    
    if not controller.start():
        logger.error("Failed to start controller. Exiting.")
        return 1
    
    if args.daemon:
        # In daemon mode, just keep the main thread running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            controller.stop()
            if args.pid_file:
                try:
                    os.unlink(args.pid_file)
                except:
                    pass
    else:
        # Interactive mode with CLI
        try:
            cli = CommandLineInterface(controller)
            cli.start()
        except KeyboardInterrupt:
            pass
        finally:
            controller.stop()
    
    return 0

def detect_init_system() -> str:
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

def stop_service():
    """Stop the service and all connections."""
    init_system = detect_init_system()
    
    try:
        if init_system == 'systemd':
            # List all running instances
            result = subprocess.run(['systemctl', 'list-units', 'remotelypy-controller@*', '--no-legend'], 
                                 capture_output=True, text=True)
            services = [line.split()[0] for line in result.stdout.splitlines()]
            
            if not services:
                print("No running controller services found")
                return True
                
            if len(services) > 1:
                print("\nMultiple controller services found:")
                for i, service in enumerate(services, 1):
                    print(f"{i}. {service}")
                choice = input("\nEnter number to stop (or 'all'): ").strip()
                
                if choice.lower() == 'all':
                    for service in services:
                        subprocess.run(['systemctl', 'stop', service], check=True)
                elif choice.isdigit() and 1 <= int(choice) <= len(services):
                    subprocess.run(['systemctl', 'stop', services[int(choice)-1]], check=True)
                else:
                    print("Invalid choice")
                    return False
            else:
                subprocess.run(['systemctl', 'stop', services[0]], check=True)
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
            subprocess.run(['systemctl', 'status', 'remotelypy-controller@*'], check=False)
        else:
            subprocess.run(['/etc/init.d/remotelypy-controller', 'status'], check=False)
        return True
    except subprocess.CalledProcessError:
        return False

if __name__ == "__main__":
    sys.exit(main())
