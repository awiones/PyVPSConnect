# RemotelyPy

<p align="center">
  <img src="https://github.com/awiones/RemotelyPy/blob/main/logo.jpeg" alt="RemotelyPy Logo" width="300">
</p>

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Unix-lightgrey)]()

A secure Python-based remote management system for controlling multiple VPS instances through a central controller.

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

## 🚀 Features

- **Secure Communication**: SSL encryption for all connections
- **Interactive CLI**: User-friendly command-line interface
- **Multi-Client Support**: Manage multiple VPS instances simultaneously
- **Service Integration**: Native systemd/init.d support
- **Shell Sessions**: Interactive shell with remote systems
- **Command Broadcasting**: Execute commands across all clients
- **Real-time Monitoring**: Live client status and health checks
- **Auto-Reconnection**: Reliable connection handling

## 📦 Installation

### Prerequisites

- Python 3.6 or higher
- Linux/Unix-based system
- Root access (for service installation)
- OpenSSL (for certificate generation)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/awiones/RemotelyPy.git
cd RemotelyPy

# Optional: Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate SSL certificates (recommended)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

## 🔧 Usage

### Controller Setup

```bash
# Start in interactive mode
python main.py controller --port 5555

# Start with SSL encryption
python main.py controller --port 5555 --ssl --cert cert.pem --key key.pem

# Install as system service
sudo python main.py silent-start --start
```

### Client Connection

```bash
# Basic connection
python main.py client --host controller.example.com --port 5555

# Secure connection with SSL
python main.py client --host controller.example.com --port 5555 --ssl --cert cert.pem
```

## 📚 Documentation

### Controller Commands

| Command                     | Description                      |
| --------------------------- | -------------------------------- |
| `help`                      | Show available commands          |
| `list`                      | List connected clients           |
| `info <client_id>`          | Show client details              |
| `cmd <command>`             | Broadcast command to all clients |
| `cmd <client_id> <command>` | Send command to specific client  |
| `shell <client_id>`         | Start interactive shell session  |
| `exit`                      | Exit controller                  |

### Service Management

```bash
# Start service
sudo python main.py silent-start --start

# Stop service
sudo python main.py silent-start --stop

# Check status
sudo python main.py silent-start --status
```

## 🔒 Security Best Practices

1. **SSL Configuration**

   - Always use SSL in production environments
   - Use strong certificates from trusted authorities
   - Regularly rotate certificates

2. **Network Security**

   - Run behind a firewall
   - Use VPN when possible
   - Limit access to specific IP ranges

3. **Access Control**
   - Implement strong authentication
   - Use principle of least privilege
   - Regular security audits

## 🔍 Troubleshooting

### Common Issues

1. **Connection Refused**

   - Check if the controller is running
   - Verify firewall settings
   - Ensure correct port configuration

2. **SSL Certificate Errors**

   - Verify certificate paths
   - Check certificate expiration
   - Ensure proper certificate permissions

3. **Service Start Failure**
   - Check system logs (`journalctl -xe`)
   - Verify user permissions
   - Validate configuration files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 👥 Authors

- **Al Ghozali Ramadhan** - _Initial work_ - [Awiones](https://github.com/awiones)

## 🙏 Acknowledgments

- OpenSSL for secure communication
- Python community for excellent libraries
- All contributors who help improve this project
