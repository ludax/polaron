"""Charger Link GUI widgets and screens (PySide6).

Faithfully reproduces the original Graupner "Charger Link" Android layout:
  * red titlebar (#FFCC0001) with app title + a memory/profile spinner
  * 60dip channel bar with Ch1 / Ch2 buttons
  * function icon buttons (glossy circular, from the APK assets)
  * charge / discharge / cycle / setting screens each show a GrPropertyView-like
    property list plus a big red Start / Stop button
  * intro screen with logo + Connect button + WiFi SSID/password/channel
"""
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QPalette, QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QFrame, QSizePolicy, QAbstractButton,
)
import assets as A

RED_TITLE = QColor('#FFCC0001')
TITLE_FG = QColor('#FFEAEAEA')
SUB_FG = QColor('#FFCCCCCC')
PANE = QColor('#FFFAFAFA')
GRID = QColor('#FFE8E8E8')

# function strip: (name, label, icon key)
FUNCTIONS = [
    ('charge',     'Charge',     'charge'),
    ('discharge',  'Discharge',  'discharge'),
    ('cycle',      'Cycle',      'cycle'),
    ('setting',    'Setting',    'setting'),
    ('profile',    'Profile',    'profile'),
    ('store',      'Store',      'store'),
    ('balance',    'Balance',    'balance'),
    ('data',       'Data',       'data'),
]


class IconButton(QPushButton):
    """A glossy icon button that swaps to its pressed image on press/hover."""

    def __init__(self, key, size=96, label=None, parent=None):
        super().__init__(parent)
        self._normal = A.pixmap(key, size, size)
        self._pressed = A.pressed_pixmap(key, size, size)
        self._key = key
        self._label = label
        self.setFlat(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(size, size)
        self.setStyleSheet(
            "QPushButton{border:none;background:transparent;}"
            "QPushButton:disabled{background:transparent;}"
        )
        self.setIcon(self._normal)
        self.setIconSize(self._normal.size())
        self.setIconSize(QSize(size - 8, size - 8))
        self.setToolTip(key)
        self._set_normal()

    def event(self, e):
        from PySide6.QtCore import QEvent
        t = e.type()
        if t == QEvent.Type.MouseButtonPress:
            self.setIcon(self._pressed)
        elif t in (QEvent.Type.MouseButtonRelease, QEvent.Type.Leave):
            if not self.pressed():
                self._set_normal()
        return super().event(e)

    def _set_normal(self):
        self.setIcon(self._normal)
        self.setIconSize(QSize(self._normal.width() - 8, self._normal.height() - 8))


class RoundImageButton(QPushButton):
    """Big circular action button (Start/Stop/connect) using the APK asset."""

    def __init__(self, key, label, size=120, parent=None):
        super().__init__(label, parent)
        self.setFlat(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._normal = A.pixmap(key, size, size)
        self._pressed = A.pressed_pixmap(key, size, size)
        self._base = size
        self.setIconSize(QSize(size - 16, size - 16))
        self.setIcon(self._normal)
        self.setStyleSheet("QPushButton{border:none;background:transparent;}")
        self.setFixedSize(size, int(size * 1.1))

    def set_label(self, text):
        """Change the tooltip/accessible text without touching the icon."""
        self.setText('')
        self.setToolTip(str(text))
        self.setAccessibleName(str(text))

    def event(self, e):
        from PySide6.QtCore import QEvent
        t = e.type()
        if t == QEvent.Type.MouseButtonPress:
            self.setIcon(self._pressed)
        elif t in (QEvent.Type.MouseButtonRelease, QEvent.Type.Leave):
            if not self.pressed():
                self.setIcon(self._normal)
        return super().event(e)


def _hline(color=GRID, h=1):
    line = QFrame()
    line.setFixedHeight(h)
    line.setStyleSheet(f"background:{color.name()};border:none;")
    line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return line


def _vline(color=GRID, w=1):
    line = QFrame()
    line.setFixedWidth(w)
    line.setStyleSheet(f"background:{color.name()};border:none;")
    line.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
    return line


class Titlebar(QWidget):
    """Red app titlebar: back button, title, subtitle, and memory/profile spinner."""

    back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName('titlebar')
        self.setFixedHeight(84)
        self.setStyleSheet(
            "#titlebar{background:#FFCC0001;border:none;}"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 0)

        self.back_btn = RoundImageButton('back', 'Back', size=56)
        self.back_btn.setFixedSize(64, 72)
        self.back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_btn.clicked.connect(lambda: self.back.emit())
        lay.addWidget(self.back_btn)

        col = QVBoxLayout()
        col.setContentsMargins(10, 0, 0, 0)
        self.title_lbl = QLabel('Charger Link')
        self.title_lbl.setStyleSheet(f"color:{TITLE_FG.name()};")
        self.title_lbl.setFont_title = True
        f = QFont()
        f.setPointSize(15); f.setBold(True)
        self.title_lbl.setFont(f)
        self.title_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.sub_lbl = QLabel('')
        self.sub_lbl.setStyleSheet(f"color:{SUB_FG.name()};font-size:9pt;")
        self.sub_lbl.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        col.addWidget(self.title_lbl)
        col.addWidget(self.sub_lbl)
        lay.addLayout(col, 1)

        self.mem_spin = QComboBox()
        self.mem_spin.setStyleSheet(
            "QComboBox{background:#FFFFFFFF;color:#222;border:1px solid #999;"
            "padding:4px;font-size:11pt;}"
            "QComboBox::drop-down{width:20px;border:none;}"
        )
        self.mem_spin.addItems(['USER SET 1', 'USER SET 2', 'USER SET 3', 'FACTORY 1'])
        self.mem_spin.setFixedWidth(150)
        lay.addWidget(_vline(), 0)
        lay.addWidget(self.mem_spin)

        sep = QLabel(); sep.setFixedHeight(2)
        sep.setStyleSheet(f"background:{GRID.name()};")
        sep.setGeometry(0, 82, 9999, 2)

    def set_title(self, title, subtitle=''):
        self.title_lbl.setText(str(title))
        self.sub_lbl.setText(str(subtitle))


class ChannelBar(QWidget):
    """60dip bar with Ch1 / Ch2 buttons + a small info/scan button row."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(60)
        self.setStyleSheet("background:#FFF1F1F1;border:none;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.ch1 = RoundImageButton('channel1', 'Channel 1', size=60)
        self.ch1.setFixedSize(80, 60)
        self.ch2 = RoundImageButton('channel2', 'Channel 2', size=60)
        self.ch2.setFixedSize(80, 60)
        self.scan = RoundImageButton('scanbarcode', 'Scan', size=56)
        self.scan.setFixedSize(56, 56)
        lay.addWidget(_vline(), 0)
        lay.addWidget(self.ch1, 1)
        lay.addWidget(_vline(), 0)
        lay.addWidget(self.ch2, 1)
        lay.addWidget(_vline(), 0)
        lay.addWidget(self.scan)


class PropertyList(QWidget):
    """GrPropertyView equivalent: a two-column label/value list with dividers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(30, 4, 30, 4)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(4)
        self._rows = {}
        self._row = 0
        self.setStyleSheet(f"background:{PANE.name()};")

    def set_title(self, r, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight:bold;color:#333;font-size:12pt;background:transparent;")
        self._grid.addWidget(lbl, r, 0, 1, 2)
        self._grid.setRowMinimumHeight(r, 24)
        self._row = r + 1

    def add(self, key, label, value=''):
        r = self._row
        keylbl = QLabel(label)
        keylbl.setStyleSheet(f"color:#555;background:transparent;")
        val = QLabel(value)
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val.setStyleSheet(f"color:#111;background:transparent;font-size:12pt;")
        self._grid.addWidget(keylbl, r, 0)
        self._grid.addWidget(val, r, 1)
        self._grid.setColumnStretch(1, 1)
        self._rows[key] = val
        sep = QLabel(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{GRID.name()};")
        self._grid.addWidget(sep, r, 0, 1, 2)
        self._grid.setRowMinimumHeight(r, 34)
        self._row += 1

    def set(self, key, value):
        if key in self._rows:
            self._rows[key].setText(value)

    # ---- richer API used by the function screens --------------------------
    def add_row(self, label, value=None):
        """Add a label/value row. `value` may be a QString or a QWidget
        (QComboBox / QLineEdit / QLabel) placed in the value column."""
        from PySide6.QtWidgets import QWidget as _W
        r = self._row
        keylbl = QLabel(label)
        keylbl.setStyleSheet("color:#555;background:transparent;font-size:11pt;")
        if isinstance(value, _W):
            val = value
            val.setStyleSheet(val.styleSheet() or "")
        else:
            val = QLabel(str(value) if value is not None else '—')
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val.setStyleSheet("color:#111;background:transparent;font-size:12pt;")
        self._grid.addWidget(keylbl, r, 0)
        self._grid.addWidget(val, r, 1)
        self._grid.setColumnStretch(1, 1)
        self._grid.setRowMinimumHeight(r, 34)
        self._rows[label] = val
        self._row += 1
        return val

    def set_value(self, label, text):
        """Set the value of a row by its label."""
        w = self._rows.get(label)
        if w is None:
            return
        from PySide6.QtWidgets import QLabel, QComboBox, QLineEdit
        if isinstance(w, QLabel):
            w.setText(str(text))
        elif isinstance(w, QComboBox):
            it = w.findText(str(text))
            if it >= 0:
                w.setCurrentIndex(it)
        elif isinstance(w, QLineEdit):
            w.setText(str(text))

    def value(self, label):
        """Read the current text value of a row by its label."""
        w = self._rows.get(label)
        if w is None:
            return ''
        from PySide6.QtWidgets import QComboBox, QLineEdit
        if isinstance(w, QComboBox):
            return w.currentText()
        if isinstance(w, QLineEdit):
            return w.text()
        if isinstance(w, QLabel):
            return w.text()
        return ''

    def rowcount(self):
        return self._row

    def sizeHint(self):
        return super().sizeHint()


def _scroll(widget):
    area = QScrollArea()
    area.setWidget(widget)
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setStyleSheet("QScrollArea{background:transparent;border:none;}")
    area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return area, widget


class FunctionStrip(QFrame):
    """The row of glossy circular function icons (charge/discharge/...)."""

    activated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background:{PANE.name()};border:none;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        self.buttons = {}
        for name, label, key in FUNCTIONS:
            b = IconButton(key, size=104, label=label)
            b.setToolTip(f'{label}')
            b.clicked.connect(lambda checked=False, n=name: self.activated.emit(n))
            self.buttons[name] = b
            lay.addWidget(b)
        lay.addStretch(1)

    def set_active(self, name):
        for n, b in self.buttons.items():
            pm = A.pressed_pixmap(n, 96, 96) if n == name else A.pixmap(n, 96, 96)
            b.setIcon(pm)
            b.setIconSize(QSize(88, 88))


def _base_screen():
    """Vertical scaffold: titlebar + channelbar + [content] + status line."""
    return None
