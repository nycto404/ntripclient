ntripclient
============

Ein leichter NTRIP-Client in reinem Python (keine externen Abhängigkeiten).

Installation
------------

Benötigt: Python 3.x

Benutzung (CLI)
---------------

Beispiel: Verbindung via HTTPS zu einem Caster und speichern der RTCM-Daten:

```bash
python3 ntripclient_cli.py --host caster.example.com --mountpoint MOUNT --user myuser --password mypass --https --output out.rtcm
```

Optionen:
- `--host` Hostname oder IP des NTRIP-Casters
- `--port` TCP-Port (Standard 2101)
- `--mountpoint` Mountpoint-Name
- `--user` Benutzername (optional)
- `--password` Passwort (optional)
- `--https` TLS (SSL) verwenden
- `--version` NTRIP-Version (1 oder 2), Standard ist 2

API
---

Das Paket stellt `NTRIPClient` zur Verfügung:

- `NTRIPClient(host, port, mountpoint, username, password, use_https, version)`
- `stream()` liefert einen Generator mit rohen Datenbytes
# ntripclient