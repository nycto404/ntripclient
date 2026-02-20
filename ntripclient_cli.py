"""CLI für den NTRIP-Client.

Beispiel:
  python3 ntripclient_cli.py --host example.com --mountpoint MOUNT --user foo --password bar --https --output out.rtcm
"""

import argparse
import sys
import os

from ntripclient import NTRIPClient, NTRIPError

def get_stdout_binary():
    # Python 3.4: sys.stdout may not have 'buffer' in all environments
    if hasattr(sys.stdout, 'buffer'):
        return sys.stdout.buffer
    else:
        # Fallback: open fd 1 as binary, unbuffered
        return os.fdopen(sys.stdout.fileno(), 'wb', 0)

def main():
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
    stdout_binary = None
    try:
        if args.serve_port:
            print("Starte lokalen Server auf 0.0.0.0:{}".format(args.serve_port), file=sys.stderr)
            client.serve_local(bind_host="0.0.0.0", bind_port=args.serve_port)
            return 0
        if args.output:
            out_fp = open(args.output, "wb")
        else:
            stdout_binary = get_stdout_binary()
            out_fp = stdout_binary
        for chunk in client.stream():
            out_fp.write(chunk)
            out_fp.flush()
    except KeyboardInterrupt:
        return 0
    except NTRIPError as e:
        print("Fehler: {}".format(e), file=sys.stderr)
        return 2
    except Exception as e:
        print("Unerwarteter Fehler: {}".format(e), file=sys.stderr)
        return 3
    finally:
        try:
            if out_fp is not None and args.output:
                out_fp.close()
            elif out_fp is not None and out_fp is not sys.stdout and out_fp is not sys.stdout.buffer:
                # Only close if we opened a new file object for stdout
                out_fp.close()
        except Exception:
            pass
        client.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
