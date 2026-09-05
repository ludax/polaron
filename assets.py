"""Asset manager for Charger Link (PySide6).

Reuses the extracted PNG/JPG button assets from the original Graupner APK
for maximum visual fidelity. Falls back to a drawn placeholder if an image
is missing so the app still runs.
"""
import os
import sys
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QBrush
from PySide6.QtCore import Qt

HERE = os.path.dirname(os.path.abspath(__file__))


def _resolve_assets_dir():
    """Locate assets/ both in dev and in a frozen PyInstaller onedir bundle.

    Non-frozen:  <repo>/assets  (next to this module).
    Frozen: PyInstaller places --add-data('assets', 'assets') payload
            next to the executable (Linux) or inside <appdir>/_internal
            (Windows, PyInstaller 6+).
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
        for cand in (os.path.join(base, 'assets'),
                     os.path.join(base, '_internal', 'assets')):
            if os.path.isdir(cand):
                return cand
        return os.path.join(base, 'assets')
    return os.path.join(HERE, 'assets')


ASSETS = _resolve_assets_dir()

# Map logical button names to the real APK image files.
PAIRS = {
    'back':        ('btn_back.png', 'btn_back_pressed.png'),
    'blutmodi':    ('btn_blutmodi.png', 'btn_blutmodi_pressed.png'),
    'scanbarcode': ('btn_scanbarcode.png', 'btn_scanbarcode_pressed.png'),
    'start':       ('btn_start.png', 'btn_start_pressed.png'),
    'stop':        ('btn_stop.png', 'btn_stop_pressed.png'),
    'channel1':    ('button_channel1_normal.png', 'button_channel1_pressed.png'),
    'channel2':    ('button_channel2_normal.png', 'button_channel2_pressed.png'),
    'editable':    ('btn_editable_icon.png', 'btn_editable_icon_pressed.png'),
    'arrow_left':  ('icon_arrow_movablel.png', 'icon_arrow_movablel_pressed.png'),
    'arrow_right': ('icon_arrow_movabler.png', 'icon_arrow_movabler_pressed.png'),
    'info':        ('icon_info.png', 'icon_info.png'),
    # functional icon buttons (single image each)
    'charge':        ('icon_onload_charge.png', 'icon_press_charge.png'),
    'discharge':     ('icon_onload_discharge.png', 'icon_press_discharge.png'),
    'cycle':         ('icon_onload_cycle.png', 'icon_press_cycle.png'),
    'setting':       ('icon_onload_setting.png', 'icon_press_setting.png'),
    'profile':       ('icon_onload_profile.png', 'icon_press_profile.png'),
    'store':         ('icon_onload_store.png', 'icon_press_store.png'),
    'balance':       ('icon_onload_balance.png', 'icon_press_balance.png'),
    'data':          ('icon_onload_data.png', 'icon_press_data.png'),
    'dot_selected':  ('dot_pageslide_selected.png', 'dot_pageslide_selected.png'),
    'dot_unselected':('dot_pageslide_unselected.png', 'dot_pageslide_unselected.png'),
    'folder':        ('folder.png', 'folder.png'),
    'logo':          ('icon_logo.png', 'icon_logo.png'),
    'connect':       ('intro_btn_connect.png', 'intro_btn_connect_p.png'),
    'cinfo':         ('intro_cinfo.png', 'intro_cinfo.png'),
    'clogo':         ('intro_clogo.png', 'intro_clogo.png'),
    'launcher':      ('ic_launcher.png', 'ic_launcher.png'),
    'bg_channel':    ('bg_channel.jpg', 'bg_channel.jpg'),
}

_cache = {}


def _path(name):
    normal, pressed = PAIRS.get(name, (name, name))
    p = os.path.join(ASSETS, normal)
    return (p if os.path.exists(p) else None), (
        os.path.join(ASSETS, pressed) if os.path.exists(os.path.join(ASSETS, pressed)) else None)


def pixmap(name, w=None, h=None):
    p, _ = _path(name)
    if p:
        pm = QPixmap(p)
        if w or h:
            pm = pm.scaled(w or pm.width(), h or pm.height(),
                           Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pm
    # fallback: neutral placeholder
    pm = QPixmap((w or 64), (h or 64))
    pm.fill(QColor(180, 180, 180))
    return pm


def pressed_pixmap(name, w=None, h=None):
    _, p = _path(name)
    if p:
        pm = QPixmap(p)
        if w or h:
            pm = pm.scaled(w or pm.width(), h or pm.height(),
                           Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pm
    return pixmap(name, w, h)


def has(name):
    p, _ = _path(name)
    return p is not None
