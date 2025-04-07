# Installation Guide

## Prerequisites

- Python 3.6 or higher
- Linux-based operating system
- Root access (for controller setup)
- Basic networking knowledge

## Controller Installation

1. Clone the repository:

```bash
git clone https://github.com/awiones/PyVPSConnect.git
cd PyVPSConnect
```

2. Install as background service:

```bash
sudo python3 silent_start.py --start
```

3. Verify installation:

```bash
sudo python3 silent_start.py --status
```

## Client Installation

1. Copy client files to VPS:

```bash
scp client.py user@vps_ip:~/
```

2. Run the client:

```bash
python3 client.py --host controller_ip --port 5555
```
