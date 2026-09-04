"""Charger Link main window: titlebar + channelbar + function strip + screen.

Reproduces the original app's main layout (main_activity = one Activity with a
QStackedWidget of screens; each screen = GrPropertyView + Start/Stop buttons,
navigated from the glossy icon button row).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel
import screens as S
import widgets as W


FUNC_TITLE = {
    'charge': 'Charge', 'discharge': 'Discharge', 'cycle': 'Cycle test',
    'setting': 'Setting', 'profile': 'Profile', 'store': 'Store',
    'balance': 'Balance', 'data': 'Data',
}


class MainView(QWidget):
    """Content below the titlebar: channelbar + function strip + screen stack."""

    def __init__(self, client, app, parent=None):
        super().__init__(parent)
        self.client = client
        self.app = app
        self.setStyleSheet('background:#FAFAFA;border:none;')
        self.current_chan = 1
        self.current_func = 'charge'

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.titlebar = W.Titlebar()
        self.titlebar.set_title('Charger Link', 'Channel 1')
        self.titlebar.back.connect(self._on_back)

        self.channelbar = W.ChannelBar()
        self.channelbar.ch1.clicked.connect(lambda: self._chan(1))
        self.channelbar.ch2.clicked.connect(lambda: self._chan(2))

        self.strip = W.FunctionStrip()
        self.strip.activated.connect(self.show_function)

        self.stack = QStackedWidget()
        self._screens = {}
        self._build_screens()

        outer.addWidget(self.titlebar)
        outer.addWidget(self.channelbar)
        outer.addWidget(self.strip)
        outer.addWidget(self.stack, 1)
        self.show_function('charge')

    def _on_back(self):
        from PySide6.QtWidgets import QApplication
        a = QApplication.instance()
        if a and hasattr(a, '_cl_app'):
            a._cl_app.stack.setCurrentWidget(a._cl_app.intro)
        # last resort: hide main view
        self.setVisible(False)

    def _build_screens(self):
        c, a = self.client, self.app
        self._screens = {
            'charge': S.ChargeScreen(c, a),
            'discharge': S.DischargeScreen(c, a),
            'cycle': S.CycleScreen(c, a),
            'setting': S.SettingScreen(c, a),
            'profile': S.ProfileScreen(c, a),
            'store': S.StoreScreen(c, a),
            'balance': S.BalanceScreen(c, a),
            'data': S.DataScreen(c, a),
        }
        for i, (name, w) in enumerate(self._screens.items()):
            self.stack.addWidget(w)
            w.set_chan(self.current_chan)

    def _chan(self, n):
        self.current_chan = n
        self.strip.set_active(self.current_func)
        w = self._screens[self.current_func]
        w.set_chan(n)
        self.app.on_chan_change(n)
        self.app.update_status('Channel %d' % n)

    def show_function(self, name):
        if name not in self._screens:
            return
        self.current_func = name
        self.strip.set_active(name)
        self.stack.setCurrentWidget(self._screens[name])
        self._screens[name].set_chan(self.current_chan)
        self.app.on_screen_change(name, self.current_chan)
