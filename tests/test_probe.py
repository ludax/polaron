"""Verification for the Connect gate (ChargerClient.probe) + /status parser.

* test_unreachable  - charger absent -> ok=False with a detail message
* test_tcp_ok       - probe TCP branch succeeds vs a plain socket listener
* test_parse_status - /status body parsing (pure, deterministic, no network)
* test_probe_ok     - probe() returns ok=True when a port accepts TCP
"""
import os
import socket
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import protocol as P  # noqa: E402


class FakeClient(P.ChargerClient):
    def __init__(self, host, port):
        super().__init__(host=host, port=port,
                         log=lambda s: print('  LOG:', s))


def test_unreachable():
    c = FakeClient('10.255.255.1', 80)
    r = c.probe(timeout=2.0)
    print('unreachable: ok=%s tcp=%s http=%s detail=%r' %
          (r['ok'], r['tcp'], r['http'], r['detail']))
    assert r['ok'] is False
    assert r['tcp'] is False and r['http'] is False
    assert r['detail'].startswith('TCP 10.255.255.1:80 unreachable')


def test_parse_status():
    f = P.ChargerClient._parse_status
    assert f('PolaronAp|sekrit|6') == \
        {'ssid': 'PolaronAp', 'password': 'sekrit', 'channel': 6}
    assert f('my ssid | pw |  11 ') == \
        {'ssid': 'my ssid', 'password': 'pw', 'channel': 11}
    assert f('only|two') is None
    assert f('') is None
    assert f(None) is None
    assert f('a|b|notanumber')['channel'] == 0


def tcp_listener():
    """Plain socket listener that accepts and holds connections."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', 0))
    port = srv.getsockname()[1]
    srv.listen(16)
    stop = threading.Event()

    def run():
        while not stop.is_set():
            try:
                conn, _ = srv.accept()
            except OSError:
                break
            conn.settimeout(5)
            try:
                conn.recv(16)
            except OSError:
                pass
            finally:
                conn.close()
        srv.close()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return port, stop


def test_tcp_ok():
    port, stop = tcp_listener()
    time.sleep(0.3)
    try:
        c = FakeClient('127.0.0.1', port)
        r = c.probe(timeout=2.0)
        print('tcp ok: ok=%s tcp=%s http=%s info=%r' %
              (r['ok'], r['tcp'], r['http'], r['info']))
        assert r['ok'] is True
        assert r['tcp'] is True
    finally:
        stop.set()
