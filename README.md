# ssh4door

A lightweight fake SSH server for remote access. Listens for SSH connections, authenticates clients, and provides shell access. Built with [Paramiko](https://github.com/paramiko/paramiko).

**⚠️ WARNING:** This tool opens a backdoor to your system. Use only on your own machines or with explicit authorization.

## Features

- Interactive shell and single-command (`exec`) support
- Root mode (passwordless login when run as root)
- Custom port, password, and host binding
- Background daemon mode with PID file
- Simple process management (`kill.sh`)

## Requirements

- Python 3.8+
- `sudo` (for privileged ports or root mode)

## Installation

```bash
git clone https://github.com/yourusername/ssh4door.git
cd ssh4door
chmod +x setup.sh kill.sh
./setup.sh
```

## Usage

```bash
source venv/bin/activate

# Foreground mode (default port 999, password 12345)
sudo python3 ssh4door.py

# Background daemon
sudo python3 ssh4door.py --bg

# Custom port and password
sudo python3 ssh4door.py --port 2222 --password mysecret

# Custom host, PID file, log file
sudo python3 ssh4door.py --host 0.0.0.0 --pid-file /tmp/ssh4door.pid --log-file /tmp/ssh4door.log

# Stop the daemon
./kill.sh
```

### CLI Options

| Argument | Short | Description | Default |
|---|---|---|---|
| `--bg` | `-b` | Run in background (daemon) | off |
| `--port` | `-p` | Listening port | `999` |
| `--password` | `-P` | SSH password | `12345` |
| `--host` | `-H` | Bind address | `0.0.0.0` |
| `--pid-file` | | PID file path | `/tmp/ssh4door.pid` |
| `--log-file` | | Log file path (bg mode) | `/tmp/ssh4door.log` |

## Connecting

```bash
# Password auth (non-root mode)
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 999 user@<host-ip>

# Single command execution
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 999 user@<host-ip> "uname -a"
```

## How It Works

1. Creates an RSA host key (stored as `server.key`)
2. Listens for SSH connections on the specified port
3. Authenticates via password (or passwordless if running as root)
4. Spawns a PTY-based shell for each connected client
5. `exec` commands run in a subprocess and return output

## License

Apache 2.0
