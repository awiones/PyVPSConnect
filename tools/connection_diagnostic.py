#!/usr/bin/env python3
"""
RemotelyPy Connection Diagnostic Tool

This script helps diagnose connection issues between RemotelyPy clients and controllers.
It tests various aspects of the connection and message exchange to identify where problems occur.
"""

import socket
import json
import ssl
import time
import sys
import os
import argparse
import uuid
import logging
from typing import Dict, Any, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('remotelypy-diagnostic')

class ConnectionDiagnostic:
    """Diagnostic tool for RemotelyPy connections."""
    
    def __init__(
        self, 
        server_host: str, 
        server_port: int, 
        use_ssl: bool = False,
        ssl_cert: Optional[str] = None
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.use_ssl = use_ssl
        self.ssl_cert = ssl_cert
        self.socket = None
        self.client_id = str(uuid.uuid4())
        
        # Resolve hostname to IP address
        try:
            self.server_ip = socket.gethostbyname(server_host)
        except socket.gaierror:
            self.server_ip = server_host  # Use as-is if resolution fails
    
    def run_diagnostics(self) -> None:
        """Run a series of diagnostic tests."""
        print("\n===== RemotelyPy Connection Diagnostics =====\n")
        
        # Test basic connectivity
        print("1. Testing basic TCP connectivity...")
        if not self._test_tcp_connection():
            print("   ❌ Basic TCP connection failed. Check firewall rules and that the server is running.")
            return
        print("   ✅ Basic TCP connection successful")
        
        # Test SSL if enabled
        if self.use_ssl:
            print("\n2. Testing SSL connection...")
            if not self._test_ssl_connection():
                print("   ❌ SSL connection failed. Check certificate configuration.")
                return
            print("   ✅ SSL connection successful")
        
        # Test full connection and registration
        print("\n3. Testing client registration...")
        socket_obj = self._establish_connection()
        if not socket_obj:
            print("   ❌ Failed to establish full connection")
            return
        
        if not self._test_registration(socket_obj):
            print("   ❌ Client registration failed")
            socket_obj.close()
            return
        print("   ✅ Client registration successful")
        
        # Test command execution
        print("\n4. Testing command execution...")
        if not self._test_command_execution(socket_obj):
            print("   ❌ Command execution failed")
            socket_obj.close()
            return
        print("   ✅ Command execution successful")
        
        # Test ping-pong
        print("\n5. Testing ping-pong message exchange...")
        if not self._test_ping_pong(socket_obj):
            print("   ❌ Ping-pong exchange failed")
            socket_obj.close()
            return
        print("   ✅ Ping-pong exchange successful")
        
        socket_obj.close()
        print("\n===== Diagnostics Complete =====")
        print("\nAll tests passed successfully. If you're still experiencing issues:")
        print("1. Check for version mismatches between client and controller")
        print("2. Examine controller logs for any errors")
        print("3. Ensure network conditions are stable")
        print("4. Verify the controller is properly handling command requests")
    
    def _test_tcp_connection(self) -> bool:
        """Test basic TCP connectivity to the server."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                result = s.connect_ex((self.server_ip, self.server_port))
                return result == 0
        except Exception as e:
            logger.error(f"TCP connection test failed: {str(e)}")
            return False
    
    def _test_ssl_connection(self) -> bool:
        """Test SSL connectivity to the server."""
        try:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            if self.ssl_cert:
                context.load_verify_locations(self.ssl_cert)
            else:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                ssl_sock = context.wrap_socket(s, server_hostname=self.server_host)
                result = ssl_sock.connect_ex((self.server_ip, self.server_port))
                return result == 0
        except Exception as e:
            logger.error(f"SSL connection test failed: {str(e)}")
            return False
    
    def _establish_connection(self) -> Optional[socket.socket]:
        """Establish a full connection to the server."""
        try:
            # Create a new socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            # Apply SSL if configured
            if self.use_ssl:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                if self.ssl_cert:
                    context.load_verify_locations(self.ssl_cert)
                else:
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=self.server_host)
            
            # Connect using the resolved IP address
            sock.connect((self.server_ip, self.server_port))
            return sock
        except Exception as e:
            logger.error(f"Connection establishment failed: {str(e)}")
            return None
    
    def _send_message(self, sock: socket.socket, message: Dict[str, Any]) -> bool:
        """Send a message to the server."""
        try:
            data = json.dumps(message).encode('utf-8') + b'\n'
            sock.sendall(data)
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    def _receive_message(self, sock: socket.socket, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Receive a message from the server."""
        buffer = b''
        sock.settimeout(timeout)
        
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    logger.error("Connection closed by server")
                    return None
                
                buffer += chunk
                
                if b'\n' in buffer:
                    message_data, buffer = buffer.split(b'\n', 1)
                    try:
                        message = json.loads(message_data.decode('utf-8'))
                        return message
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message as JSON: {str(e)}")
                        return None
        except socket.timeout:
            logger.error("Socket timeout while waiting for response")
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {str(e)}")
            return None
    
    def _test_registration(self, sock: socket.socket) -> bool:
        """Test client registration with the server."""
        system_info = {
            "hostname": socket.gethostname(),
            "platform": "diagnostic",
            "platform_version": "1.0",
            "python_version": sys.version,
            "client_id": self.client_id,
            "ip_address": "127.0.0.1"
        }
        
        # Send registration message
        if not self._send_message(sock, {
            "type": "registration",
            "system_info": system_info
        }):
            return False
        
        # Wait for acknowledgment (this might be implicit in the protocol)
        # For diagnostic purposes, we'll just wait a moment
        time.sleep(1)
        return True
    
    def _test_command_execution(self, sock: socket.socket) -> bool:
        """Test command execution through the server."""
        command_id = str(uuid.uuid4())
        
        # Send a simple command request
        if not self._send_message(sock, {
            "type": "command_request",
            "command_id": command_id,
            "command": "echo 'diagnostic test'"
        }):
            return False
        
        # Wait for response
        response = self._receive_message(sock, timeout=15)
        if not response:
            print("   ⚠️ No response received for command request")
            print("   This is likely the same issue you're experiencing with the client")
            print("   Possible causes:")
            print("     - Controller is not properly processing command requests")
            print("     - Controller is not sending responses back")
            print("     - Network issues are preventing responses from reaching the client")
            return False
        
        # Check if response is valid
        if response.get('type') != 'command_result' or response.get('command_id') != command_id:
            print(f"   ⚠️ Unexpected response: {response}")
            return False
        
        return True
    
    def _test_ping_pong(self, sock: socket.socket) -> bool:
        """Test ping-pong message exchange with the server."""
        # Send ping
        if not self._send_message(sock, {
            "type": "ping",
            "timestamp": time.time()
        }):
            return False
        
        # Wait for pong
        response = self._receive_message(sock)
        if not response or response.get('type') != 'pong':
            return False
        
        return True

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="RemotelyPy Connection Diagnostic Tool")
    parser.add_argument("--host", required=True, help="Controller server hostname or IP")
    parser.add_argument("--port", type=int, default=5555, help="Controller server port")
    parser.add_argument("--ssl", action="store_true", help="Use SSL encryption")
    parser.add_argument("--cert", help="Path to SSL certificate for verification")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        help="Logging level")
    return parser.parse_args()

def main():
    """Main entry point for the diagnostic tool."""
    args = parse_arguments()
    
    # Set the logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    diagnostic = ConnectionDiagnostic(
        server_host=args.host,
        server_port=args.port,
        use_ssl=args.ssl,
        ssl_cert=args.cert
    )
    
    try:
        diagnostic.run_diagnostics()
    except KeyboardInterrupt:
        print("\nDiagnostic tool terminated by user")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())