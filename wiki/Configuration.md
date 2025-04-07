# Configuration Guide

## Controller Configuration

### Command Line Options

| Option     | Description          | Default |
| ---------- | -------------------- | ------- |
| --host     | Bind interface       | 0.0.0.0 |
| --port     | Listen port          | 5555    |
| --ssl      | Enable SSL           | False   |
| --cert     | SSL certificate path | None    |
| --key      | SSL key path         | None    |
| --daemon   | Run in background    | False   |
| --log-file | Log file location    | None    |

### Service Configuration

The controller can run as a system service with:

```bash
sudo python3 silent_start.py --start
```

## Client Configuration

### Command Line Options

| Option | Description            | Default        |
| ------ | ---------------------- | -------------- |
| --host | Controller IP/hostname | Required       |
| --port | Controller port        | 5555           |
| --ssl  | Enable SSL             | False          |
| --cert | SSL certificate        | None           |
| --id   | Custom client ID       | Auto-generated |
