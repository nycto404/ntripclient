"""Minimaler, reiner-Python NTRIP-Client (v1 + v2, http/https).

Ziele:
- Verbindet per TCP/SSL zum NTRIP-Caster
- Unterstützt NTRIP v1 und v2 (Header `Ntrip-Version: Ntrip/2.0`)
- Liefert einen Byte-Stream (Generator) mit den RTCM-Daten
"""
from __future__ import annotations

import socket
import ssl
import base64
import threading
from typing import Generator, Optional, List


class NTRIPError(Exception):
    pass


class NTRIPClient:
    def __init__(
        self,
        host: str,
        port: int = 2101,
        mountpoint: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_https: bool = False,
        version: int = 2,
        timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.mountpoint = mountpoint.lstrip("/")
        self.username = username
        self.password = password
        self.use_https = use_https
        self.version = int(version)
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._rest: bytes = b""

    def _create_connection(self) -> socket.socket:
        sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        if self.use_https:
            ctx = ssl.create_default_context()
            sock = ctx.wrap_socket(sock, server_hostname=self.host)
        return sock

    def connect(self) -> None:
        if self._sock:
            return
        self._sock = self._create_connection()
        path = f"/{self.mountpoint}" if self.mountpoint else "/"
        lines = [f"GET {path} HTTP/1.1"]
        lines.append(f"Host: {self.host}:{self.port}")
        lines.append("User-Agent: NTRIP ntripclient/1.0")
        lines.append("Accept: */*")
        if self.version == 2:
            lines.append("Ntrip-Version: Ntrip/2.0")
        if self.username:
            cred = f"{self.username}:{self.password or ''}".encode("utf-8")
            b64 = base64.b64encode(cred).decode("ascii")
            lines.append(f"Authorization: Basic {b64}")
        # Leave connection open for streaming
        request = "\r\n".join(lines) + "\r\n\r\n"
        self._sock.sendall(request.encode("ascii"))

        # Read headers
        header = bytearray()
        while b"\r\n\r\n" not in header:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise NTRIPError("Verbindung geschlossen bevor Antwort empfangen wurde")
            header.extend(chunk)
        head, rest = header.split(b"\r\n\r\n", 1)
        self._rest = rest
        # Parse status
        first_line = head.split(b"\r\n", 1)[0].decode("ascii", errors="ignore")
        parts = first_line.split()
        if len(parts) < 2:
            raise NTRIPError(f"Ungültige Antwort des Casters: {first_line}")
        try:
            code = int(parts[1])
        except ValueError:
            raise NTRIPError(f"Ungültiger Statuscode in Antwort: {first_line}")
        if code != 200:
            reason = " ".join(parts[2:]) if len(parts) > 2 else ""
            raise NTRIPError(f"Caster antwortete mit {code} {reason}")

    def stream(self, chunk_size: int = 4096) -> Generator[bytes, None, None]:
        """Yields raw bytes from the caster until the connection closes."""
        if not self._sock:
            self.connect()
        if self._rest:
            yield self._rest
            self._rest = b""
        assert self._sock is not None
        try:
            while True:
                data = self._sock.recv(chunk_size)
                if not data:
                    break
                yield data
        finally:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def serve_local(self, bind_host: str = "127.0.0.1", bind_port: int = 2947, backlog: int = 5) -> None:
        """Startet einen lokalen TCP-Server auf `bind_host:bind_port` und leitet
        den RTCM-Stream an alle verbundenen Clients weiter.

        Die Methode blockiert bis ein Abbruch (KeyboardInterrupt) erfolgt oder der
        Stream endet.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((bind_host, bind_port))
        server.listen(backlog)

        clients: List[socket.socket] = []
        clients_lock = threading.Lock()
        stop_event = threading.Event()

        def accept_loop() -> None:
            server.settimeout(1.0)
            while not stop_event.is_set():
                try:
                    conn, addr = server.accept()
                except socket.timeout:
                    continue
                with clients_lock:
                    clients.append(conn)

        accept_thread = threading.Thread(target=accept_loop, daemon=True)
        accept_thread.start()

        try:
            for chunk in self.stream():
                with clients_lock:
                    dead: List[socket.socket] = []
                    for c in clients:
                        try:
                            c.sendall(chunk)
                        except Exception:
                            try:
                                c.close()
                            except Exception:
                                pass
                            dead.append(c)
                    for d in dead:
                        clients.remove(d)
        except KeyboardInterrupt:
            pass
        finally:
            stop_event.set()
            try:
                server.close()
            except Exception:
                pass
            with clients_lock:
                for c in clients:
                    try:
                        c.close()
                    except Exception:
                        pass

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
