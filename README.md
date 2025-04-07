# PyVPSConnect

<p align="center">
  <img src="https://github.com/awiones/PyVPSConnect/blob/main/logo.png" alt="PyVPSConnect Logo" width="300">
</p>

A powerful Python tool to control and manage multiple VPS instances from a central location with secure communications and real-time monitoring.

## Quick Start

```bash
# Start Controller (Background)
sudo python3 silent_start.py --start

# Start Client
python3 client.py --host your_controller_ip --port 5555

# Stop Controller
sudo python3 silent_start.py --stop
```

## Features

- **Remote Control**: Execute commands on any connected VPS
- **Interactive Shell**: Full terminal access to remote VPS
- **Secure**: SSL encryption and client authentication
- **Daemon Mode**: Run controller in background
- **Auto-Recovery**: Automatic reconnection on connection loss
- **Multi-Client**: Manage unlimited VPS instances
- **Real-Time**: Instant command execution and response

## Installation

### Controller Setup

```bash
# Clone repository
git clone https://github.com/awiones/PyVPSConnect.git
cd PyVPSConnect

# Start as background service
sudo python3 silent_start.py --start

# Check status
sudo python3 silent_start.py --status
```

### Client Setup

```bash
# Copy client.py to your VPS
scp client.py user@vps_ip:~/

# Run client
python3 client.py --host controller_ip --port 5555
```

## Basic Usage

### Controller Commands

| Command | Description |
|---------|-------------|
| `list` | Show connected VPS instances |
| `info <id>` | Show VPS details |
| `cmd <command>` | Run command on all VPS |
| `cmd <id> <command>` | Run command on specific VPS |
| `shell <id>` | Interactive shell |
| `exit` | Exit controller |

### Example Session

```bash
PyVPSConnect> list
ID         Hostname          IP             Connected Since
----------------------------------------------------------------
e2b18581   vps1.example     192.168.1.100  2023-04-07 15:21:08

PyVPSConnect> shell e2b1
Connected to vps1.example...
vps1:~$ ls
vps1:~$ cd /etc
vps1:/etc$ exit

PyVPSConnect> cmd df -h
Sending to all VPS...
```

## Configuration

### Controller Options

```bash
python3 controller.py [OPTIONS]
  --host HOST         Bind interface (default: 0.0.0.0)
  --port PORT        Listen port (default: 5555)
  --ssl              Enable SSL
  --cert FILE        SSL certificate path
  --key FILE         SSL key path
  --daemon           Run in background
  --log-file FILE    Log file location
```

### Client Options

```bash
python3 client.py [OPTIONS]
  --host HOST        Controller IP/hostname
  --port PORT        Controller port
  --ssl             Enable SSL
  --cert FILE       SSL certificate
  --id ID           Custom client ID
```

## Service Management

### Using silent_start.py

```bash
sudo python3 silent_start.py --start    # Start service
sudo python3 silent_start.py --stop     # Stop service
sudo python3 silent_start.py --status   # Check status
```

### Logs

```bash
tail -f /var/log/pyvpsconnect/controller.log
```

## Security Best Practices

- Enable SSL in production environments
- Use custom certificates for better security
- Keep controller behind firewall
- Use strong authentication tokens
- Regular security audits recommended

## System Requirements

- Python 3.6+
- Linux OS
- Root access (controller setup only)
- Basic networking knowledge

## Troubleshooting

<details>
<summary>Connection Issues</summary>

- Check firewall rules
- Verify port availability
- Ensure correct IP/hostname
- Test network connectivity between hosts
</details>

<details>
<summary>Permission Errors</summary>

- Run controller setup as root
- Check log directory permissions
- Verify user permissions
- Ensure Python has necessary system access
</details>

## Support & Community

- [Report issues on GitHub](https://github.com/awiones/PyVPSConnect/issues)
- [Check documentation](https://github.com/awiones/PyVPSConnect/wiki) for updates

## License

This project is licensed under the MIT License - see the LICENSE file for details.
