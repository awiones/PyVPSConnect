# Controller Usage Guide

## Interactive Mode Commands

| Command            | Description             | Example             |
| ------------------ | ----------------------- | ------------------- |
| help               | Show help menu          | `help`              |
| list               | List connected clients  | `list`              |
| info <id>          | Show client details     | `info abc123`       |
| cmd <command>      | Send to all clients     | `cmd uptime`        |
| cmd <id> <command> | Send to specific client | `cmd abc123 ls -la` |
| shell <id>         | Interactive shell       | `shell abc123`      |
| exit               | Exit controller         | `exit`              |

## Service Management

```bash
# Start service
sudo python3 silent_start.py --start

# Stop service
sudo python3 silent_start.py --stop

# Check status
sudo python3 silent_start.py --status
```
