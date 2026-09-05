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
from sizing import (
    TITLEBAR_H, SPINNER_ROW_H, BACK_MARGIN, BACK_BTN,
    TITLE_SIZE, SUBTITLE_SIZE, GRID_MARGIN, GRID_HGAP, GRID_VGAP,
    ICON_PX, LABEL_PX, LABEL_SIZE, CHBAR_H, CHINFO_D, ACTION_BTN, ACTION_GAP,
    scale,
)

RED_TITLE = QColor('#FFCC0001')
TITLE_FG = QColor('#FFEAEAEA')
SUB_FG = QColor('#FFCCCCCC')
PANE = QColor('#FFFAFAFA')
GRID = QColor('#FFE8E8E8')

# function strip: (name, label, icon key)
# Order = original phone app (APK main.xml / home screenshot), 3x3 grid,
# last cell empty.
FUNCTIONS = [
    ('profile',    'Profile',    'profile'),
    ('charge',     'Charge',     'charge'),
    ('discharge',  'Discharge',  'discharge'),
    ('cycle',      'Cycle',      'cycle'),
    ('balance',    'Balance',    'balance'),
    ('data',       'Data',       'data'),
    ('setting',    'User Set',   'setting'),
    ('store',      'Store',      'store'),
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
    """Original app titlebar (APK common_titlebar.xml):

      row 1: red #FFCC0001 — back button (40dip, 7dip margins) + title 20dip
             bold #EAEAEA + subtitle 10dip #CCCCCC (right edge)
      row 2: white memory/profile spinner (47dip) above a 2px #999999 line

    Emits `back`.  Exposes `mem_spin` (QComboBox) and `set_title()`.
    """

    back = Signal()

    def __init__(self, parent=None, w=560):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName('titlebar')

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- row 1: red band -------------------------------------------
        band = QWidget()
        band.setObjectName('tband')
        band.setStyleSheet("#tband{background:#FFCC0001;border:none;}")
        lay = QHBoxLayout(band)
        lay.setContentsMargins(scale(BACK_MARGIN, w), scale(BACK_MARGIN, w),
                               scale(BACK_MARGIN, w), scale(BACK_MARGIN, w))

        self.back_btn = RoundImageButton('back', 'Back', size=scale(BACK_BTN, w))
        self.back_btn.clicked.connect(lambda: self.back.emit())
        lay.addWidget(self.back_btn)

        col = QVBoxLayout()
        col.setContentsMargins(scale(10, w), 0, 0, 0)
        col.setSpacing(0)
        self.title_lbl = QLabel('Charger Link')
        f = QFont(); f.setPixelSize(scale(TITLE_SIZE, w)); f.setBold(True)
        self.title_lbl.setFont(f)
        self.title_lbl.setStyleSheet("color:#FFEAEAEA;background:transparent;")
        self.subtitle_lbl = QLabel('')
        f2 = QFont(); f2.setPixelSize(scale(SUBTITLE_SIZE, w))
        self.subtitle_lbl.setFont(f2)
        self.subtitle_lbl.setStyleSheet("color:#FFCCCCCC;background:transparent;")
        self.subtitle_lbl.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        col.addWidget(self.title_lbl)
        col.addWidget(self.subtitle_lbl)
        lay.addLayout(col, 1)

        outer.addWidget(band)

        # ---- row 2: memory/profile spinner --------------------------------
        self.mem_spin = QComboBox()
        self.mem_spin.addItems(['USER SET 1', 'USER SET 2', 'USER SET 3', 'FACTORY 1'])
        self.mem_spin.setStyleSheet(
            "QComboBox{background:#FFFFFFFF;color:#222;border:none;"
            "padding:0 10px;font-size:12px;}"
            "QComboBox::drop-down{width:22px;border:none;}"
        )
        outer.addWidget(self.mem_spin)
        sep = QFrame()
        sep.setFixedHeight(2)
        sep.setStyleSheet("background:#FF999999;border:none;")
        outer.addWidget(sep)

        self.setFixedHeight(scale(TITLEBAR_H + SPINNER_ROW_H, w))

        self._w = w

    def recompute(self, w):
        """Resize after the window size changes (used by App on resize)."""
        if w == getattr(self, '_w', None):
            return
        self._w = w
        self.setFixedHeight(scale(TITLEBAR_H + SPINNER_ROW_H, w))

    def set_title(self, title, subtitle=''):
        self.title_lbl.setText(str(title))
        self.subtitle_lbl.setText(str(subtitle))


class ChannelBar(QWidget):
    """Bottom channel bar (APK common_channelbar.xml): two equal-weight
    CH1 / CH2 buttons (images have 'CH 1' / 'CH 2' baked in) plus a
    ~40dip circular info button on the right, with a 1px divider below.
    Emits `channel1` / `channel2` on press; exposes ch1/ch2/info_btn.
    """

    channel1 = Signal()
    channel2 = Signal()
    info_clicked = Signal()

    def __init__(self, parent=None, w=560):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._w = w
        self.setStyleSheet("background:#FFF5F5F5;border:none;")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self.ch1 = RoundImageButton('channel1', 'Channel 1', size=scale(CHBAR_H, w))
        self.ch1.clicked.connect(lambda: self.channel1.emit())
        self.ch2 = RoundImageButton('channel2', 'Channel 2', size=scale(CHBAR_H, w))
        self.ch2.clicked.connect(lambda: self.channel2.emit())
        self.info_btn = RoundImageButton('info', 'Info', size=scale(CHINFO_D, w))
        self.info_btn.clicked.connect(lambda: self.info_clicked.emit())

        # CH tiles: full-height, stretchy width (images are wide baked-in
        # 'CH 1' / 'CH 2' graphics with the active red underline).
        h = scale(CHBAR_H, w)
        for b in (self.ch1, self.ch2):
            b.setMaximumWidth(16777215)
            b.setMinimumWidth(10)
            b.setFixedHeight(h)
            b.setIconSize(QSize(10000, max(h - 6, 10)))
        self.info_btn.setFixedSize(scale(CHINFO_D, w), scale(CHINFO_D, w))
        self._info_sz = scale(CHINFO_D, w)

        rl.addWidget(self.ch1, 1)
        rl.addWidget(self.ch2, 1)
        rl.addWidget(self.info_btn)
        outer.addWidget(row)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background:#FFD0D0D0;border:none;")
        outer.addWidget(div)

        self.setFixedHeight(scale(CHBAR_H, w) + 1)

    def set_active(self, n):
        """n = 1|2 — show pressed state on the active channel tile."""
        self.ch1.setIcon(A.pressed_pixmap('channel1', scale(CHBAR_H, self._w), scale(CHBAR_H, self._w)) if n == 1
                         else A.pixmap('channel1', scale(CHBAR_H, self._w), scale(CHBAR_H, self._w)))
        self.ch2.setIcon(A.pressed_pixmap('channel2', scale(CHBAR_H, self._w), scale(CHBAR_H, self._w)) if n == 2
                         else A.pixmap('channel2', scale(CHBAR_H, self._w), scale(CHBAR_H, self._w)))


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


class FunctionStrip(QWidget):
    """Original app function menu (APK main.xml): a centered 3x3 grid of
    circular icons (90dip) with a text label (120dip wide) under each,
    ~20dip padding around the grid and 30dip gap between rows.
    The 9th cell is empty in the original layout.

    Emits `activated(name)` when an icon is pressed.
    """

    activated = Signal(str)

    COLS = 3

    def __init__(self, parent=None, w=560):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._w = w
        self.setStyleSheet(f"background:{PANE.name()};border:none;")
        grid = QGridLayout(self)
        grid.setContentsMargins(scale(GRID_MARGIN, w), scale(GRID_MARGIN, w),
                                scale(GRID_MARGIN, w), scale(GRID_MARGIN, w))
        grid.setHorizontalSpacing(scale(GRID_HGAP, w))
        grid.setVerticalSpacing(scale(GRID_VGAP, w))
        grid.setAlignment(Qt.AlignCenter)

        self.buttons = {}
        icon_sz = scale(ICON_PX, w)
        for idx, (name, label, key) in enumerate(FUNCTIONS):
            r, c = divmod(idx, self.cols)
            cell = QWidget()
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(scale(4, w))
            cl.setAlignment(Qt.AlignCenter)

            b = IconButton(key, size=icon_sz, label=label)
            b.setToolTip(label)
            b.clicked.connect(lambda checked=False, n=name: self.activated.emit(n))
            cl.addWidget(b, 0, Qt.AlignCenter)

            lbl = QLabel(label, cell)
            f = QFont(); f.setPixelSize(scale(LABEL_SIZE, w))
            lbl.setFont(f)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color:#FF555555;background:transparent;")
            cl.addWidget(lbl, 0, Qt.AlignCenter)

            self.buttons[name] = b
            grid.addWidget(cell, r, c)

        # sizeHint: icon + label + gaps, scaled — lets the strip take its
        # natural height instead of squashing into the remaining space.
        cell_h = icon_sz + scale(LABEL_PX, w) + scale(10, w)
        self._natural_h = (scale(GRID_MARGIN, w) * 2
                           + cell_h * 3 + scale(GRID_VGAP, w) * 2)

    @property
    def cols(self):
        return self.COLS

    def sizeHint(self):
        from PySide6.QtCore import QSize as _QS
        return _QS(super().sizeHint().width(), self._natural_h)

    def minimumSizeHint(self):
        from PySide6.QtCore import QSize as _QS
        return _QS(super().minimumSizeHint().width(), self._natural_h)

    def set_active(self, name):
        icon_sz = scale(ICON_PX, self._w)
        for n, b in self.buttons.items():
            pm = A.pressed_pixmap(n, icon_sz, icon_sz) if n == name else A.pixmap(n, icon_sz, icon_sz)
            b.setIcon(pm)
            b.setIconSize(QSize(icon_sz - 8, icon_sz - 8))


def _base_screen():
    """Vertical scaffold: titlebar + channelbar + [content] + status line."""
    return None
