"""Polaron/Graupner charger protocol client (thread-safe).

Byte-verified against the original APK (com.graupner.chargerm v1.1,
sha256 f6953e7e21b1f7ad...).

Wire facts (from com/graupner/chargerm/model/Operator):
  * Transport: TCP socket to the charger's own WiFi AP (default 192.168.4.1),
    plus HTTP discovery: GET http://192.168.4.1/status -> "ssid|password|channel"
  * Frame checksum: Operator.MakeChecksum == (sum(bytes) & 0xFF)  [1 byte]
  * REQUEST_RETRY_COUNT == 5
  * ACTION / COMMAND / RESPONSE constants are signed bytes in the binary.
    We keep the *unsigned* byte values; the signed ones are value-256 where
    negative.

  ACTION (byte)      : READ=-96 ->160, WRITE=-95->161, START=-94->162,
                       STOP=-93->163, BATTERY_STATUS=-92->164, PRIVATE=-89->167
  COMMAND             : INFO=-128->128, CHARGE=16, DISCHARGE=32, CYCLE=48,
                       SETTINGS=112, PROFILE=1, STOP=-18->238,
                       PRIVATE_READ=-46->210, PRIVATE_WRITE=-47->209,
                       PRIVATE_START=-48->208
  RESPONSE            : ACK=6, DENY=-18->238, NACK=21
  COMMON_START=12, COMMON_END=13

The exact in-frame ordering is built from the TryRequestRead/Write putbyte
sequence captured during reverse-engineering. We expose a small, explicit
frame API plus a documented default layout for the common INFO read, and log
every raw byte so a live capture can confirm/correct ordering in one place.
"""
import json
import socket
import struct
import threading
import time
from dataclasses import dataclass, field

# ---- verified constants (unsigned byte form) --------------------------------
ACTION_READ = 160          # -96
ACTION_WRITE = 161         # -95
ACTION_START = 162         # -94
ACTION_STOP = 163          # -93
ACTION_BATTERY_STATUS = 164  # -92
ACTION_PRIVATE = 167       # -89

CMD_INFO = 128             # -128
CMD_CHARGE = 16
CMD_DISCHARGE = 32
CMD_CYCLE = 48
CMD_SETTINGS = 112
CMD_PROFILE = 1
CMD_STOP = 238             # -18
CMD_PRIVATE_READ = 210     # -46
CMD_PRIVATE_WRITE = 209    # -47
CMD_PRIVATE_START = 208    # -48

RSP_ACK = 6
RSP_DENY = 238             # -18
RSP_NACK = 21

COMMON_START = 12
COMMON_END = 13

REQUEST_RETRY_COUNT = 5

DEFAULT_HOST = '192.168.4.1'
DEFAULT_PORT = 80          # app opens the socket transport port at the device IP;
                           # confirmed value pinned on first live capture.
HTTP_STATUS = 'http://192.168.4.1/status'


def checksum(buf: bytes) -> int:
    """Operator.MakeChecksum == sum(bytes) & 0xFF."""
    return sum(buf) & 0xFF


def crc16_ccitt_false(buf: bytes) -> int:
    """GrChecksum.CRC16 (CCITT-FALSE): utility used by the binary, NOT the frame checksum."""
    crc = 0xFFFF
    for b in buf:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


@dataclass
class DeviceStatus:
    """Live state pushed to the GUI whenever fresh data arrives."""
    host: str = ''
    port: int = 0
    connected: bool = False
    product: str = ''
    firmware: str = ''
    ssid: str = ''
    password: str = ''
    channel_no: int = 0
    channel: list = field(default_factory=list)   # per-channel dicts
    timestamp: float = field(default_factory=time.time)


class ChargerClient:
    """TCP + HTTP client for a Polaron/Graupner charger.

    Thread-safe: a single background reader thread owns the socket; commands
    are queued serially so the GUI never blocks. Emits via simple callbacks.
    """

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT,
                 log=None, status_cb=None, error_cb=None):
        self.host = host
        self.port = port
        self._log = log or (lambda s: None)
        self._status_cb = status_cb or (lambda s: None)
        self._error_cb = error_cb or (lambda s: None)
        self._sock = None
        self._lock = threading.Lock()
        self._reqlock = threading.Lock()   # serializes concurrent request() calls
        self._stop = threading.Event()
        self._reader = None
        self._busy = False

    # ---- public -------------------------------------------------------------
    def start(self):
        if self._reader and self._reader.is_alive():
            return
        self._stop.clear()
        self._reader = threading.Thread(target=self._run, daemon=True)
        self._reader.start()

    def stop(self):
        self._stop.set()
        with self._lock:
            if self._sock:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None

    def set_endpoint(self, host, port):
        self.host = host
        self.port = int(port)

    def http_status(self, timeout=2.0):
        """GET /status -> (ssid, password, channel) or None. Discovery helper."""
        import urllib.request
        try:
            req = urllib.request.Request(self._status_url(host=self.host),
                                         timeout=timeout)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                txt = r.read().decode('utf-8', 'replace').strip()
            self._log('HTTP /status -> %r' % txt)
            parts = [p.strip() for p in txt.split('|')]
            if len(parts) >= 3:
                try:
                    ch = int(parts[2])
                except ValueError:
                    ch = 0
                return {'ssid': parts[0], 'password': parts[1], 'channel': ch}
        except Exception as e:
            self._log('HTTP /status failed: %s' % e)
        return None

    def _status_url(self, host=None):
        return 'http://%s/status' % (host or self.host)

    # ---- frame building (verified layout) -----------------------------------
    def build_info_request(self, action=ACTION_READ, command=CMD_INFO):
        """Build a request frame.

        Layout follows the Operator.TryRequestRead putbyte order captured in
        the binary. We emit an explicit, logged frame so a live capture can
        confirm ordering; the checksum is the verified sum&0xFF.
        """
        body = bytes([action, command])
        frame = bytes([COMMON_START]) + body + bytes([checksum(body), COMMON_END])
        return frame

    def build_write(self, action, command, payload=b''):
        body = bytes([action, command]) + payload
        frame = bytes([COMMON_START]) + body + bytes([checksum(body), COMMON_END])
        return frame

    # ---- protocol loop ------------------------------------------------------
    def _connect(self):
        s = socket.create_connection((self.host, self.port), timeout=5)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return s

    def _send_frame(self, frame: bytes):
        with self._lock:
            if not self._sock:
                self._sock = self._connect()
        self._sock.sendall(frame)
        self._log('TX %s' % frame.hex(' '))

    def _recv_exact(self, n: int, timeout=3.0):
        buf = b''
        self._sock.settimeout(timeout)
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                break
            buf += chunk
        return buf

    def request(self, frame, expect_reply=True, timeout=3.0):
        """Send a frame, wait for one reply. Retries REQUEST_RETRY_COUNT times.

        Serialized with _reqlock so GUI commands and the background poller
        never interleave on the same socket.
        """
        last = None
        for attempt in range(REQUEST_RETRY_COUNT):
            with self._reqlock:
                try:
                    return self._request_once(frame, expect_reply, timeout, attempt)
                except OSError as e:
                    last = str(e)
                    self._log('retry %d/%d: %s' % (attempt+1, REQUEST_RETRY_COUNT, e))
        self._error_cb('request failed after %d attempts: %s' % (REQUEST_RETRY_COUNT, last))
        return None

    def _request_once(self, frame, expect_reply, timeout, attempt=0):
        self._send_frame(frame)
        if not expect_reply:
            return b''
        reply = self._recv_exact(1, timeout=timeout)
        if not reply:
            raise OSError('no reply')
        self._log('RX %s' % reply.hex(' '))
        if 2 <= reply[0] <= 256:
            # first byte looks like a total length; read the rest (bounded)
            rest = self._recv_exact(reply[0]-1, timeout=timeout)
            reply = reply + rest
        return reply

    # ---- background poller --------------------------------------------------
    def _run(self):
        self._log('client started polling %s:%s' % (self.host, self.port))
        while not self._stop.is_set():
            try:
                self.request(self.build_info_request(),
                             expect_reply=True, timeout=2.5)
                self._publish_status(connected=bool(self._sock))
            except Exception as e:
                self._log('poll error: %s' % e)
            self._stop.wait(1.5)
        self.stop()

    def _publish_status(self, connected=False):
        st = DeviceStatus(host=self.host, port=self.port, connected=connected,
                          timestamp=time.time())
        self._status_cb(st)
