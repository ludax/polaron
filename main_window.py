"""Charger Link main view (APK-faithful navigation).

The original app's home screen (res/layout/main.xml) is a 3x3 grid:
titlebar + icon grid + channel bar.  Each function screen
(charge.xml, ...) is titlebar + property list + Start/Stop + channel
bar — the grid is NOT present there.  So in our shared-titlebar
equivalent the grid is a page of the screen stack ("home"), tapping a
grid tile switches to that function's page, and the back button returns
to the grid.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
import screens as S
import widgets as W

FUNC_TITLE = {
    'charge': 'Charge', 'discharge': 'Discharge', 'cycle': 'Cycle test',
    'setting': 'User set', 'profile': 'Profile', 'store': 'Store',
    'balance': 'Balance', 'data': 'Data',
}

HOME = 'home'


def _top_w(widget, default=560):
    """Window width to anchor proportional sizing on.

    MainView is created *before* it is added to the app's layout (no
    parent yet), so its own width() is the top-level default — measure
    the fixed-size App window instead.
    """
    app = getattr(widget, 'app', None)
    if app is not None:
        w = app.width()
        if w >= 100:
            return w
    top = widget
    while top.parent() is not None:
        top = top.parent()
    w = top.width()
    return w if w >= 100 else default


class MainView(QWidget):
    """Titlebar (top) + [home grid | function screens] + channel bar (bottom)."""

    def __init__(self, client, app, parent=None):
        super().__init__(parent)
        self.client = client
        self.app = app
        self.setStyleSheet('background:#FAFAFA;border:none;')
        self.current_chan = 1
        self.current_func = HOME

        w = _top_w(self)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.titlebar = W.Titlebar(w=w)
        self.titlebar.set_title('Charger Link', 'Channel 1')
        self.titlebar.back.connect(self._on_back)

        self.stack = QStackedWidget()
        self.strip = W.FunctionStrip(w=w)
        self.strip.activated.connect(self.show_function)
        self.stack.addWidget(self.strip)          # home page = the grid

        self._screens = self._build_screens()
        for s in self._screens.values():
            self.stack.addWidget(s)

        self.channelbar = W.ChannelBar(w=w)
        self.channelbar.channel1.connect(lambda: self._chan(1))
        self.channelbar.channel2.connect(lambda: self._chan(2))
        self.channelbar.info_clicked.connect(
            lambda: self.app.flash('Info — battery/charger details coming soon', 'info'))

        outer.addWidget(self.titlebar)
        outer.addWidget(self.stack, 1)
        outer.addWidget(self.channelbar)

        self.set_home()

    def _build_screens(self):
        c, a = self.client, self.app
        screens = {
            'charge': S.ChargeScreen(c, a),
            'discharge': S.DischargeScreen(c, a),
            'cycle': S.CycleScreen(c, a),
            'setting': S.SettingScreen(c, a),
            'profile': S.ProfileScreen(c, a),
            'store': S.StoreScreen(c, a),
            'balance': S.BalanceScreen(c, a),
            'data': S.DataScreen(c, a),
        }
        for name, s in screens.items():
            s.set_chan(self.current_chan)
        return screens

    # ---- navigation ---------------------------------------------------------
    def set_home(self):
        """Show the home grid; it displays the last-used function as active."""
        self.current_func = HOME
        last = getattr(self, '_last_func', 'profile')
        self.strip.set_active(last)
        self.stack.setCurrentWidget(self.strip)
        self.titlebar.set_title('Charger Link', 'Channel %d' % self.current_chan)

    def _on_back(self):
        if self.current_func != HOME:
            self.set_home()
            return
        a = getattr(self, '_cl_app_back', None)
        if a is not None and hasattr(a, 'stack') and hasattr(a, 'intro'):
            a.stack.setCurrentWidget(a.intro)

    def _chan(self, n):
        self.current_chan = n
        self.channelbar.set_active(n)
        if self.current_func in self._screens:
            self._screens[self.current_func].set_chan(n)
        self.app.on_chan_change(n)
        self.app.update_status('Channel %d' % n)

    def show_function(self, name):
        if name not in self._screens:
            return
        self._last_func = name
        self.current_func = name
        self.strip.set_active(name)
        self.stack.setCurrentWidget(self._screens[name])
        self._screens[name].set_chan(self.current_chan)
        self.titlebar.set_title(FUNC_TITLE.get(name, name),
                                'Channel %d' % self.current_chan)
        self.app.on_screen_change(name, self.current_chan)
