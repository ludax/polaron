"""Shared screen base for Charger Link: property list + Start/Stop action row."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
)
import assets as A
import widgets as W
from sizing import scale, ACTION_BTN, ACTION_GAP


def _screen_w(widget, default=560):
    """Top-level window width (screens are parentless at construction,
    so prefer the app window, which is setFixedSize'd)."""
    app = getattr(widget, 'app', None)
    if app is not None:
        w = app.width()
        if w >= 100:
            return w
    top = widget
    while top.parent() is not None:
        top = top.parent()
    return max(top.width(), default if top.width() < 100 else top.width())


class ActionRow(QWidget):
    """Start / Stop round button pair (APK charge.xml: 45dip buttons,
    3dip margins, in a bottom bar under the property list)."""

    started = Signal()
    stopped = Signal()

    def __init__(self, parent=None, w=560):
        super().__init__(parent)
        self._w = w
        self.setStyleSheet("background:transparent;border:none;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, scale(8, w), 0, scale(8, w))
        sz = scale(ACTION_BTN, w)
        self.start_btn = W.RoundImageButton('start', 'Start', size=sz)
        self.stop_btn = W.RoundImageButton('stop', 'Stop', size=sz)
        self.start_btn.clicked.connect(self.started.emit)
        self.stop_btn.clicked.connect(self.stopped.emit)
        lay.addStretch(1)
        lay.addWidget(self.start_btn)
        lay.addSpacing(scale(ACTION_GAP, w))
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
        w = _screen_w(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # GrPropertyView header: red bold 16dip title (common_sub_titlebar)
        head = QLabel(f'{title} — Channel {chan}')
        f = QFont(); f.setPixelSize(scale(20, w)); f.setBold(True)
        head.setFont(f)
        head.setStyleSheet(
            "color:#FF330000;background:#FFE0E0E0;"
            f"padding:{scale(6, w)}px {scale(20, w)}px;")
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
