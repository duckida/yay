from os import urandom
from binascii import b2a_base64
import socket as usocket
import ssl
import time

TYPE_TEXT = const(0x1)
TYPE_BINARY = const(0x2)
TYPE_CONNECTION_CLOSE = const(0x8)
TYPE_PING = const(0x9)
TYPE_PONG = const(0xA)
TYPE_CONTINUATION = const(0x0)

_NEED_MORE = object()
_MAX_FRAME = const(65536)
_READ_CHUNK = const(2048)


class WebSocket:
    def __init__(self):
        self._stream = None
        self._buf = b""
        self._frag = b""
        self._frag_type = 0

    def connect(self, url, timeout=10):
        try:
            proto, _, host, path = url.split("/", 3)
        except ValueError:
            proto, _, host = url.split("/", 2)
            path = ""

        if proto == "ws:":
            port = 80
        elif proto == "wss:":
            port = 443
        else:
            raise Exception("Unsupported URL!")

        if ":" in host:
            host, port = host.split(":", 1)

        sockaddr = usocket.getaddrinfo(host, int(port), 0, usocket.SOCK_STREAM)[0][-1]

        s = usocket.socket()
        try:
            # Every network operation below is bounded. Without this a stalled
            # DNS/TCP/TLS/HTTP handshake hangs the whole program forever.
            s.settimeout(timeout)
            s.connect(sockaddr)
            if proto == "wss:":
                s = ssl.wrap_socket(s, server_hostname=host)
                # MicroPython's SSLSocket has no settimeout; it inherits the
                # timeout set on the plain socket above, which covers the
                # handshake and the HTTP upgrade response.

            key = urandom(16)

            s.write(f"GET /{path} HTTP/1.1\r\n")
            s.write(f"Host: {host}\r\n")
            s.write("Upgrade: websocket\r\n")
            s.write("Connection: Upgrade\r\n")
            s.write(f"Sec-WebSocket-Key: {b2a_base64(key)[:-1]}\r\n")
            s.write("Sec-WebSocket-Version: 13\r\n")
            s.write("\r\n")

            l = s.readline()
            l = l.split(b" ", 2)
            if len(l) < 2:
                raise Exception("Invalid HTTP response")
            status_code = int(l[1])
            count = 0
            while True:
                l = s.readline()
                if not l or l == b"\r\n":
                    break
                count += 1
                if count > 100:
                    raise Exception("Too many HTTP headers")
        except Exception:
            try:
                s.close()
            except Exception:
                pass
            raise

        if status_code != 101:
            try:
                s.close()
            except Exception:
                pass
            raise Exception(f"Received HTTP {status_code} on connection upgrade!")

        # recv() must never block: it is called from the main loop.
        s.setblocking(False)
        self._stream = s
        self._buf = b""
        self._frag = b""
        self._frag_type = 0

    def _read_some(self):
        if self._stream is None:
            return False
        try:
            data = self._stream.read(_READ_CHUNK)
        except OSError as e:
            code = e.args[0] if e.args else None
            # Non-blocking "no data yet" results.
            if code in (11, 110, 115, -0x6900, -0x6880):
                return False
            self.close()
            raise
        if data is None:
            return False
        if len(data) == 0:
            # Peer closed the TCP connection.
            self.close()
            return False
        self._buf += data
        if len(self._buf) > _MAX_FRAME + 16:
            self.close()
            raise Exception("WebSocket receive buffer too large")
        return True

    def _parse(self):
        buf = self._buf
        n = len(buf)
        if n < 2:
            return _NEED_MORE

        b0 = buf[0]
        b1 = buf[1]
        fin = b0 & 0x80
        opcode = b0 & 0x0F
        masked = b1 & 0x80
        length = b1 & 0x7F
        pos = 2

        if length == 126:
            if n < 4:
                return _NEED_MORE
            length = (buf[2] << 8) | buf[3]
            pos = 4
        elif length == 127:
            if n < 10:
                return _NEED_MORE
            length = 0
            for i in range(8):
                length = (length << 8) | buf[2 + i]
            pos = 10
            if length > _MAX_FRAME:
                self.close()
                raise Exception("WebSocket frame too large")

        if masked:
            if n < pos + 4:
                return _NEED_MORE
            mask = buf[pos:pos + 4]
            pos += 4
        else:
            mask = None

        if n < pos + length:
            return _NEED_MORE

        payload = buf[pos:pos + length]
        self._buf = buf[pos + length:]
        if mask is not None:
            p = bytearray(payload)
            for i in range(length):
                p[i] ^= mask[i & 3]
            payload = bytes(p)

        if opcode == TYPE_CONNECTION_CLOSE:
            try:
                self._send_frame(b"", TYPE_CONNECTION_CLOSE)
            except Exception:
                pass
            self.close()
            return None

        if opcode == TYPE_PING:
            try:
                self._send_frame(payload, TYPE_PONG)
            except Exception:
                self.close()
                raise
            return None

        if opcode == TYPE_PONG:
            return None

        if opcode == TYPE_CONTINUATION:
            self._frag += payload
            if len(self._frag) > _MAX_FRAME:
                self.close()
                raise Exception("WebSocket message too large")
            if not fin:
                return None
            payload = self._frag
            opcode = self._frag_type
            self._frag = b""
            self._frag_type = 0
        elif not fin:
            self._frag = payload
            self._frag_type = opcode
            return None

        if opcode != TYPE_TEXT and opcode != TYPE_BINARY:
            self.close()
            raise Exception(f"Unsupported WebSocket opcode {opcode}")

        return payload, opcode

    def recv(self):
        if self._stream is None:
            return None, None

        while True:
            res = self._parse()
            if res is _NEED_MORE:
                if not self._read_some():
                    return None, None
                continue
            if res is None:
                # A control or partial frame was handled. Keep parsing if
                # more bytes are already buffered.
                if self._buf:
                    continue
                return None, None
            return res

    def _write_all(self, data, timeout=5):
        written = 0
        deadline = time.ticks_ms() + timeout * 1000
        while written < len(data):
            try:
                n = self._stream.write(data[written:])
            except OSError as e:
                code = e.args[0] if e.args else None
                if code in (11, 110, 115, -0x6900, -0x6880):
                    if time.ticks_diff(time.ticks_ms(), deadline) > 0:
                        raise OSError("WebSocket send timed out")
                    time.sleep(0.01)
                    continue
                raise
            if n is None:
                n = 0
            if n == 0:
                if time.ticks_diff(time.ticks_ms(), deadline) > 0:
                    raise OSError("WebSocket send timed out")
                time.sleep(0.01)
                continue
            written += n

    def _send_frame(self, data, msgtype):
        if self._stream is None:
            raise OSError("WebSocket is not connected")

        data_len = len(data)
        if data_len < 126:
            header = bytearray(2)
            header[0] = 0x80 | msgtype
            header[1] = 0x80 | data_len
        elif data_len < 65536:
            header = bytearray(4)
            header[0] = 0x80 | msgtype
            header[1] = 0x80 | 126
            header[2] = (data_len >> 8) & 0xFF
            header[3] = data_len & 0xFF
        else:
            header = bytearray(10)
            header[0] = 0x80 | msgtype
            header[1] = 0x80 | 127
            for i in range(8):
                header[2 + i] = (data_len >> (56 - 8 * i)) & 0xFF

        # RFC 6455: every client-to-server frame must be masked with a fresh
        # 4-byte key. Slack closes the connection if this is missing/invalid.
        mask = urandom(4)
        masked = bytearray(data)
        for i in range(data_len):
            masked[i] ^= mask[i & 3]

        # The SSLSocket is non-blocking; this loops with a bounded deadline.
        self._write_all(header)
        self._write_all(mask)
        if data_len:
            self._write_all(masked)

    def send(self, data, msgtype=TYPE_TEXT):
        if isinstance(data, str):
            data = data.encode()
        self._send_frame(data, msgtype)

    def close(self):
        s = self._stream
        self._stream = None
        self._buf = b""
        self._frag = b""
        self._frag_type = 0
        if s is not None:
            try:
                s.close()
            except Exception:
                pass

    def connected(self):
        return self._stream is not None
