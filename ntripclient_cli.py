"""CLI für den NTRIP-Client.

Beispiel:
  python3 ntripclient_cli.py --host example.com --mountpoint MOUNT --user foo --password bar --https --output out.rtcm
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ntripclient import NTRIPClient, NTRIPError


def main() -> int:
    p = argparse.ArgumentParser(description="Einfacher NTRIP-Client (HTTP/HTTPS, v1/v2)")
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=2101)
    p.add_argument("--mountpoint", default="")
    p.add_argument("--user")
    p.add_argument("--password")
    p.add_argument("--https", action="store_true")
    p.add_argument("--version", type=int, choices=(1, 2), default=2)
    p.add_argument("--serve-port", type=int, help="Serve the stream on localhost:PORT")
    p.add_argument("--output", help="Datei zum schreiben, sonst stdout")
    args = p.parse_args()

    client = NTRIPClient(
        host=args.host,
        port=args.port,
        mountpoint=args.mountpoint,
        username=args.user,
        password=args.password,
        use_https=args.https,
        version=args.version,
    )

    out_fp = None
    try:
        if args.serve_port:
            print(f"Starte lokalen Server auf 127.0.0.1:{args.serve_port}", file=sys.stderr)
            # Serve the stream to localhost:serve_port (blocks)
            client.serve_local(bind_host="127.0.0.1", bind_port=args.serve_port)
            return 0
        if args.output:
            out_path = Path(args.output)
            out_fp = out_path.open("wb")
        else:
            out_fp = sys.stdout.buffer
        for chunk in client.stream():
            out_fp.write(chunk)
            out_fp.flush()
    except KeyboardInterrupt:
        return 0
    except NTRIPError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}", file=sys.stderr)
        return 3
    finally:
        try:
            if out_fp and out_fp is not sys.stdout.buffer:
                out_fp.close()
        except Exception:
            pass
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
