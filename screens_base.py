"""Shared screen base for Charger Link: property list + Start/Stop action row."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
)
import assets as A
import widgets as W


class ActionRow(QWidget):
    """The big Start / Stop round button pair shown on control screens."""

    started = Signal()
    stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;border:none;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 6)
        self.start_btn = W.RoundImageButton('start', 'Start', size=110)
        self.stop_btn = W.RoundImageButton('stop', 'Stop', size=110)
        self.start_btn.clicked.connect(self.started.emit)
        self.stop_btn.clicked.connect(self.stopped.emit)
        lay.addStretch(1)
        lay.addWidget(self.start_btn)
        lay.addSpacing(30)
        lay.addWidget(self.stop_btn)
        lay.addStretch(1)


class BaseScreen(QWidget):
    """A function screen: scrolling GrPropertyView + optional action row."""

    def __init__(self, title, client=None, app=None, chan=1,
                 action_row=True, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.client = client
        self.app = app
        self.chan = chan
        self.setWindowTitle(title)
        self.setStyleSheet("background:#FAFAFA;border:none;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        head = QLabel(f'{title} — Channel {chan}')
        f = QFont(); f.setPointSize(13); f.setBold(True)
        head.setFont(f)
        head.setStyleSheet("color:#333;background:#F5F5F5;padding:8px 16px;border-bottom:1px solid #DDD;")
        head.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        lay.addWidget(head)

        self.props = W.PropertyList()
        area, _ = W._scroll(self.props)
        lay.addWidget(area, 1)

        if action_row:
            self.actions = ActionRow()
            lay.addWidget(self.actions)
        else:
            self.actions = None

    def _combo(self, options):
        cb = QComboBox()
        for o in options:
            cb.addItem(str(o))
        return cb

    def _edit(self, text):
        from PySide6.QtWidgets import QLineEdit
        e = QLineEdit(str(text))
        return e

    def add_actions(self, row):
        """Attach an ActionRow to this screen's bottom (for action_row=False)."""
        self.actions = row
        self.layout().addWidget(row)

    def flash(self, msg, level='info'):
        """Show a transient status message (no-op sink in standalone screens)."""
        if self.app and hasattr(self.app, 'flash'):
            self.app.flash(msg, level)

    def _run(self, fn, *args, **kwargs):
        """Run a protocol call off the GUI thread; surface note on completion."""
        import threading
        def worker():
            try:
                fn(*args, **kwargs)
            except Exception as e:
                self.on_error(str(e))
        threading.Thread(target=worker, daemon=True).start()

    def set_chan(self, n):
        """Called when the active channel (Ch1/Ch2) changes."""
        try:
            self.p = self.props
        except Exception:
            return
        self.on_connected(None)

    def on_connected(self, status):
        """Refresh values from a live status object (GUI thread)."""
        pass

    def on_error(self, msg):
        pass
