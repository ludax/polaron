"""Function screens for Charger Link.

Each screen reproduces the original app's layout for one icon-button
function: Charge, Discharge, Cycle, Setting, Profile, Store, Balance, Data.
Property lists mirror the original GrPropertyView field rows.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QLabel
import protocol as P
from screens_base import BaseScreen, ActionRow


def _row(widget):
    return widget


class ChargeScreen(BaseScreen):
    def __init__(self, client, app, chan=1, parent=None):
        super().__init__('Charge', client, app, chan, action_row=True, parent=parent)
        p = self.props
        p.add_row('Cell count', self._combo([3, 4, 5, 6]))
        self.v_charge_time = p.add_row('Charge time (min)', self._edit('0'))
        self.v_charge_cur  = p.add_row('Charge current (A)', self._edit('1.0'))
        self.v_temp        = p.add_row('Max temperature (°C)', self._edit('45'))
        self.v_mode        = p.add_row('Charge mode', self._combo(['Normal', 'Fast', 'Trickle']))
        self.v_end_reason = p.add_row('End reason', QLabel('—'))
        self.props.set_value('End reason', '—')
        self.actions.started.connect(lambda: self._cmd(P.ACTION_START, P.CMD_CHARGE, 'Charge started'))
        self.actions.stopped.connect(lambda: self._cmd(P.ACTION_STOP, P.CMD_STOP, 'Stop requested'))

    def on_connected(self, st):
        if getattr(st, 'channel', None):
            for row, val in [('Cell count', 4), ('Charge time (min)', 0)]:
                self.props.set_value(row, str(val))
        self.props.set_value('End reason', 'Ready')

    def _cmd(self, action, command, note):
        if self.client:
            frame = self.client.build_info_request(action=action, command=command)
            self._run(self.client.request, frame, note)


class DischargeScreen(BaseScreen):
    def __init__(self, client, app, chan=1, parent=None):
        super().__init__('Discharge', client, app, chan, action_row=True, parent=parent)
        p = self.props
        p.add_row('Cell count', self._combo([3, 4, 5, 6]))
        p.add_row('Discharge current (A)', self._edit('0.5'))
        self.v_cutoff = p.add_row('Cutoff voltage (V/cell)', self._edit('2.80'))
        p.add_row('Capacity end (mAh)', self._edit('0'))
        self.v_end_reason = p.add_row('End reason', QLabel('—'))
        self.actions.started.connect(lambda: self._cmd(P.ACTION_START, P.CMD_DISCHARGE, 'Discharge started'))
        self.actions.stopped.connect(lambda: self._cmd(P.ACTION_STOP, P.CMD_STOP, 'Stop requested'))


class CycleScreen(BaseScreen):
    def __init__(self, client, app, chan=1, parent=None):
        super().__init__('Cycle test', client, app, chan, action_row=True, parent=parent)
        p = self.props
        p.add_row('Cycle count', self._edit('10'))
        p.add_row('Charge current (A)', self._edit('1.0'))
        p.add_row('Discharge current (A)', self._edit('0.5'))
        p.add_row('Cutoff voltage (V/cell)', self._edit('2.80'))
        self.v_cycle_no = p.add_row('Current cycle', QLabel('—'))
        p.add_row('Accumulated Ah (charged)', self._edit('0'))
        p.add_row('Accumulated Ah (discharged)', self._edit('0'))
        self.actions.started.connect(lambda: self._cmd(P.ACTION_START, P.CMD_CYCLE, 'Cycle started'))
        self.actions.stopped.connect(lambda: self._cmd(P.ACTION_STOP, P.CMD_STOP, 'Stop requested'))


class SettingScreen(BaseScreen):
    """Charger settings (mirrors the app's Setting screen + /settingssave)."""
    def __init__(self, client, app, chan=1, parent=None):
        super().__init__('Setting', client, app, chan, action_row=False, parent=parent)
        self.ssid = self.props.add_row('WiFi SSID', self._edit(''))
        self.pw   = self.props.add_row('WiFi password', self._edit(''))
        self.ch   = self.props.add_row('WiFi channel', self._combo(list(range(1, 14))))
        self.props.add_row('Buzzer', self._combo(['On', 'Off']))
        self.props.add_row('Screen dim (min)', self._edit('5'))
        self.props.add_row('LED brightness', self._edit('100'))
        bar = ActionRow()
        bar.started.connect(lambda: self._save('Settings saved'))
        bar.stopped.connect(lambda: self.app.flash('Settings restored to defaults', 'info'))
        bar.start_btn.set_label('Save')
        bar.stop_btn.set_label('Defaults')
        self.add_actions(bar)

    def on_connected(self, st):
        if getattr(st, 'ssid', None):
            self.props.set_value('WiFi SSID', st.ssid)
            self.props.set_value('WiFi channel', str(getattr(st, 'channel_no', '') or ''))

    def _save(self, note):
        if self.client:
            payload = (self.props.value('WiFi SSID') or '').encode()
            frame = self.client.build_write(P.ACTION_WRITE, P.CMD_SETTINGS, payload)
            self._run(self.client.request, frame, note)


class ProfileScreen(BaseScreen):
    def __init__(self, client, app, parent=None):
        super().__init__('Profile', client, app, chan=0, action_row=False, parent=parent)
        self.mem = self.props.add_row('Memory slot', self._combo(['Memory 1', 'Memory 2', 'Memory 3', 'Memory 4']))
        self.props.add_row('Slot contents', QLabel('—'))
        bar = ActionRow()
        bar.started.connect(lambda: self._cmd(P.ACTION_READ, P.CMD_PROFILE, 'Profile loaded'))
        bar.stopped.connect(lambda: self._cmd(P.ACTION_WRITE, P.CMD_PROFILE, 'Profile stored'))
        bar.start_btn.set_label('Load')
        bar.stop_btn.set_label('Store')
        self.add_actions(bar)

    def _cmd(self, action, command, note):
        if self.client:
            frame = self.client.build_info_request(action=action, command=command)
            self._run(self.client.request, frame, note)


class StoreScreen(BaseScreen):
    """Battery profile 'Store' sub-screen (list of saved profiles)."""
    def __init__(self, client, app, parent=None):
        super().__init__('Profile Store', client, app, chan=0, action_row=False, parent=parent)
        self.props.add_row('Saved profiles', QLabel('— no data —'))
        self.props.add_row('Selected', QLabel('—'))
        bar = ActionRow()
        bar.started.connect(lambda: self._cmd(P.ACTION_WRITE, P.CMD_PROFILE, 'Stored'))
        bar.stopped.connect(lambda: client and None)
        bar.start_btn.set_label('Save')
        bar.stop_btn.set_label('Delete')
        self.add_actions(bar)

    def _cmd(self, action, command, note):
        if self.client:
            frame = self.client.build_info_request(action=action, command=command)
            self._run(self.client.request, frame, note)


class BalanceScreen(BaseScreen):
    def __init__(self, client, app, chan=1, parent=None):
        super().__init__('Balance', client, app, chan, action_row=True, parent=parent)
        self.v_state = self.props.add_row('Balance state', QLabel('—'))
        self.v_cells = self.props.add_row('Cell voltages (V)', QLabel('—'))
        self.v_delta = self.props.add_row('Max − Min (mV)', QLabel('—'))
        self.v_temp  = self.props.add_row('Pack temperature (°C)', QLabel('—'))
        self.actions.started.connect(lambda: self._cmd(P.ACTION_START, P.CMD_CHARGE, 'Balance on'))
        self.actions.stopped.connect(lambda: self._cmd(P.ACTION_STOP, P.CMD_STOP, 'Balance off'))

    def on_connected(self, st):
        chs = getattr(st, 'channel', None) or []
        vals = [getattr(c, 'voltage', None) for c in chs][:6]
        if vals:
            self.props.set_value('Cell voltages (V)', ' | '.join(f'{v:.3f}' for v in vals))
            if all(v is not None for v in vals):
                self.props.set_value('Max − Min (mV)', f'{round((max(vals)-min(vals))*1000)}')


class DataScreen(BaseScreen):
    def __init__(self, client, app, parent=None):
        super().__init__('Data', client, app, chan=0, action_row=False, parent=parent)
        self.props.add_row('Firmware', QLabel('—'))
        self.props.add_row('Serial number', QLabel('—'))
        self.props.add_row('Total charge time (h)', self._edit('0'))
        self.props.add_row('Total cycles', self._edit('0'))
        self.props.add_row('Export to file', QLabel('—'))
        bar = ActionRow()
        bar.started.connect(lambda: self.app.flash('Data export queued — wire to file dialog', 'info'))
        bar.stop_btn.setVisible(False)
        bar.start_btn.set_label('Export')
        self.add_actions(bar)
