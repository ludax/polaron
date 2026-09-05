"""Charger Link — Windows/any-OS GUI for Polaron/Graupner chargers.

Main entry point. Wires the intro/Connect screen, the main screen stack
(Charge/Discharge/Cycle/Setting/Profile/Store/Balance/Data), the verified
protocol client, and the APK image assets into one application.

Run:
    python main.py                 # normal GUI
    QT_QPA_PLATFORM=offscreen
    python main.py --screenshot    # render intro + every screen to PNGs

"""
import os, sys, signal, time
os.environ.setdefault('QT_PLUGIN_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qt_plugins'))
from PySide6.QtCore import Qt, QTimer, QSize, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPen
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGridLayout, QScrollArea, QFrame, QSizePolicy,
    QFileDialog, QLineEdit, QMessageBox, QSpacerItem,
)
import assets as A
import widgets as W
import protocol as P

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, 'screens')
os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------- status bar
class StatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(34)
        self.setStyleSheet("background:#FF333333;border:none;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        self.dot = QLabel('●')
        self.dot.setStyleSheet("color:#F44336;font-size:11pt;")
        self.msg = QLabel('Disconnected')
        self.msg.setStyleSheet("color:#EEEEEE;font-size:10pt;")
        lay.addWidget(self.dot)
        lay.addWidget(self.msg, 1)
        self.conn_lbl = QLabel('')
        self.conn_lbl.setStyleSheet("color:#EEEEEE;font-size:9pt;")
        lay.addWidget(self.conn_lbl)

    def set_connected(self, ok, host=''):
        self.dot.setStyleSheet(f"color:{'#4CAF50' if ok else '#F44336'};font-size:11pt;")
        self.msg.setText('Connected' if ok else 'Disconnected')
        self.conn_lbl.setText(f'{host}' if host and ok else '')

    def set_text(self, msg):
        self.msg.setText(str(msg))

    def flash(self, msg, level='info'):
        color = {'error': '#FF8A80', 'info': '#EEEEEE', 'success': '#B9F6CA'}.get(level, '#EEEEEE')
        self.msg.setStyleSheet(f"color:{color};font-size:10pt;")
        self.msg.setText(str(msg))
        QTimer.singleShot(4000, lambda: self.msg.setStyleSheet("color:#EEEEEE;font-size:10pt;"))



# ---------------------------------------------------------------- intro view
class IntroScreen(QWidget):
    """Connect screen: logo, WiFi info, host/port, big Connect button.

    Connect is VERIFIED before anything else happens: `_on_connect` runs
    `client.probe(host, port)` on a worker thread (TCP connect + HTTP
    /status). Only a positive probe emits `connect_ready(res)`; a failed
    probe emits `connect_failed(reason)` and the user stays on this screen
    with a red status flash. Never show "connected" green without a
    real response from the charger.
    """
    connect_ready = Signal(object)   # res dict from client.probe() when ok
    connect_failed = Signal(str)     # human-readable reason

    def __init__(self, client, status, parent=None):
        super().__init__(parent)
        self.client = client
        self.status = status
        self.setStyleSheet(f"background:{W.PANE.name()};border:none;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 30, 40, 40)

        logo = QLabel('')
        pm = A.pixmap('clogo', 120, 120)
        logo.setPixmap(pm)
        logo.setAlignment(Qt.AlignCenter)
        lay.addWidget(logo, 0, Qt.AlignTop)
        title = QLabel('Graupner Charger Link')
        f = QFont(); f.setPointSize(20); f.setBold(True)
        title.setFont(f)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#222;background:transparent;")
        lay.addWidget(title, 0, Qt.AlignTop)
        sub = QLabel('Connect to your charger over WiFi')
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color:#666;font-size:11pt;background:transparent;")
        lay.addWidget(sub, 0, Qt.AlignTop)

        lay.addSpacing(12)
        info = QLabel('Your charger creates a WiFi network.\n'
                      'Connect to it, then press Connect.\n'
                      'Typical defaults — check the sticker on the charger:')
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color:#444;font-size:10pt;line-height:16px;background:transparent;")
        lay.addWidget(info, 0, Qt.AlignTop)
        lay.addSpacing(8)
        self.ssid_lbl = QLabel('SSID: —   Password: —   Channel: —')
        self.ssid_lbl.setAlignment(Qt.AlignCenter)
        self.ssid_lbl.setStyleSheet("color:#000;font-size:11pt;font-weight:bold;background:transparent;")
        lay.addWidget(self.ssid_lbl, 0, Qt.AlignTop)

        lay.addStretch(1)

        hostgrid = QGridLayout()
        hostgrid.setContentsMargins(0, 8, 0, 8)
        hl = QLabel('Host:'); hl.setStyleSheet("color:#333;font-size:11pt;background:transparent;")
        vl = QLabel('Port:'); vl.setStyleSheet("color:#333;font-size:11pt;background:transparent;")
        self.host_edit = QLineEdit('192.168.4.1')
        self.port_edit = QLineEdit('80')
        for e in (self.host_edit, self.port_edit):
            e.setFixedWidth(180)
            e.setStyleSheet("QLineEdit{background:#FFF;border:1px solid #AAA;padding:4px;font-size:11pt;}")
        hostgrid.addWidget(hl, 0, 0)
        hostgrid.addWidget(self.host_edit, 0, 1)
        hostgrid.addWidget(vl, 1, 0)
        hostgrid.addWidget(self.port_edit, 1, 1)
        hostgrid.setRowStretch(2, 1)
        wrapper = QWidget()
        wl = QHBoxLayout(wrapper); wl.setContentsMargins(0, 0, 0, 0); wl.addStretch(1)
        wl.addLayout(hostgrid); wl.addStretch(1)
        lay.addWidget(wrapper)

        self.connect_btn = W.RoundImageButton('connect', 'Connect', size=130)
        self.connect_btn.clicked.connect(self._on_connect)
        self.ssid_update.connect(self._on_ssid)
        lay.addWidget(self.connect_btn, 0, Qt.AlignHCenter)

    ssid_update = Signal(object)

    def refresh_ssid(self):
        """Query /status in a background thread; emit ssid_update on result."""
        import threading
        client = self.client
        def worker():
            self.ssid_update.emit(client.http_status(timeout=2.0))
        threading.Thread(target=worker, daemon=True).start()

    def _on_ssid(self, info):
        if info:
            self.ssid_lbl.setText(
                "SSID: %s   Password: %s   Channel: %s"
                % (info.get('ssid', '?'), info.get('password', '?'),
                   info.get('channel', '?')))
        else:
            self.ssid_lbl.setText('SSID: —   Password: —   Channel: —')

    def _on_connect(self):
        host = self.host_edit.text().strip() or P.DEFAULT_HOST
        try:
            port = int(self.port_edit.text().strip() or P.DEFAULT_PORT)
        except ValueError:
            port = P.DEFAULT_PORT
        if self.connect_btn.isEnabled():
            self.set_busy(True)
            self.status.set_text('Connecting to %s …' % host)
            import threading
            def worker():
                res = self.client.probe(host, port)
                if res['ok']:
                    if res.get('info'):
                        self.ssid_update.emit(res['info'])
                    self.connect_ready.emit(res)
                else:
                    self.connect_failed.emit(
                        res.get('detail') or ('no response from %s:%d' % (host, port)))
            threading.Thread(target=worker, daemon=True).start()

    def set_busy(self, on):
        """Disable/enable the Connect button while the probe is in flight."""
        self.connect_btn.setEnabled(not on)
        self.connect_btn.set_label('Connecting…' if on else 'Connect')
