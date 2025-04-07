# Client Usage Guide

## Running the Client

Basic connection:

```bash
python3 client.py --host controller_ip --port 5555
```

With SSL:

```bash
python3 client.py --host controller_ip --port 5555 --ssl --cert /path/to/cert
```

## Interactive Shell

The client provides a styled prompt showing:

- Username
- Hostname
- Current directory

Example:

```bash
┌──(username㉿hostname)-[~/current/path]
└─$
```

### Available Commands

- All standard shell commands
- Directory navigation (cd)
- /quit to exit
