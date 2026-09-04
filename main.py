"""Charger Link — main entry point.

Reproduces the original Graupner "Charger Link" (com.graupner.chargerm v1.1):
  * Intro/Connect screen (WiFi info + host/port + big Connect button)
  * Main view: red titlebar + Ch1/Ch2 channel bar + glossy icon strip +
    screen stack (Charge / Discharge / Cycle / Setting / Profile / Store /
    Balance / Data), each a property list with Start/Stop
  * Verified protocol client: TCP to the charger AP (192.168.4.1),
    checksum = sum(bytes) & 0xFF, retry = 5, HTTP GET /status discovery

Run (any OS — build a Windows exe with PyInstaller):
    python main.py
Render headless screenshots for verification (Linux):
    QT_QPA_PLATFORM=offscreen python main.py --screenshot
"""
import os
import sys

os.environ.setdefault('MESA_GL_VERSION_OVERRIDE', '4.5')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QStackedWidget,
)
import assets as A                 # noqa: ensure assets dir resolves early
import protocol as P
import widgets as W
from main_intro import IntroScreen, StatusBar
from main_window import MainView, FUNC_TITLE


class App(QWidget):
    """Owns: status bar, protocol client, intro + main view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Charger Link')
        self.setFixedSize(560, 880)
        self.setStyleSheet('background:#FAFAFA;')

        logf = os.path.join(HERE, 'chargerlink.log')
        with open(logf, 'a', encoding='utf-8') as fh:
            fh.write('\n--- session ---\n')
        self._logfh = open(logf, 'a', encoding='utf-8')

        def _log(s):
            self._logfh.write('[CL] %s\n' % s)
            self._logfh.flush()

        self.client = P.ChargerClient(
            log=_log,
            status_cb=self._on_status,
            error_cb=lambda e: self.flash(e, 'error'),
        )

        self.statusbar = StatusBar()
        self.intro = IntroScreen(self.client, self.statusbar)
        self.intro.connect_ready.connect(self._go_main)

        self.main = MainView(self.client, self)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.intro)
        self.stack.addWidget(self.main)

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self.stack, 1)
        v.addWidget(self.statusbar)

        # poll WiFi info a few seconds in (fails quietly if no charger on net)
        QTimer.singleShot(400, self.intro.refresh_ssid)
        self.stack.setCurrentWidget(self.intro)

    # ---- plumbing used by screens/main view --------------------------------
    def flash(self, msg, level='info'):
        self.statusbar.flash(msg, level)

    def update_status(self, msg):
        self.statusbar.set_text(msg)

    def on_chan_change(self, n):
        pass

    def on_screen_change(self, name, chan):
        main_view = getattr(self, 'main', None)
        if main_view is None:
            return
        tb = getattr(main_view, 'titlebar', None)
        if tb is not None:
            tb.set_title(FUNC_TITLE.get(name, 'Charger Link'), f'Channel {chan}')
        self.update_status('%s — Channel %d' % (FUNC_TITLE.get(name, name), chan))

    def _on_status(self, st):
        # device status callback may arrive from a worker thread; hop GUI-safe
        try:
            self.statusbar.set_connected(bool(st.connected), st.host)
        except Exception:
            pass

    def _go_main(self):
        self.client.start()
        self.stack.setCurrentWidget(self.main)
        self.statusbar.set_connected(True, self.client.host)

    def closeEvent(self, e):
        try:
            self.client.stop()
            self._logfh.close()
        except Exception:
            pass
        super().closeEvent(e)


def main():
    if '--screenshot' in sys.argv:
        import screenshots
        sys.exit(screenshots.run())
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    w = App()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
