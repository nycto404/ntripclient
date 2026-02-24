# ntripclient

A lightweight NTRIP client in pure Python (no external dependencies).

## Installation

Requires: Python 3.x

## Usage (CLI)

Example: Connect via HTTPS to a caster and save the RTCM data:

```bash
python3 ntripclient_cli.py --host caster.example.com --mountpoint MOUNT --user myuser --password mypass --https --output out.rtcm
```

## Options
--host Hostname or IP of the NTRIP caster
--port TCP port (default 2101)
--mountpoint Mountpoint name
--user Username (optional)
--password Password (optional)
--https Use TLS (SSL)
--version NTRIP version (1 or 2), default is 2

## API
The package provides NTRIPClient:

NTRIPClient(host, port, mountpoint, username, password, use_https, version)