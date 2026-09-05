"""Headless offscreen screenshot renderer for Charger Link.

Renders the intro screen and every function screen (per channel) to PNGs
under <repo>/screens/ so the layout can be checked side-by-side against
the original phone reference.  Uses an offscreen QPA platform and a
faulthandler watchdog so a hung paint loop aborts instead of hanging.

Usage:
    QT_QPA_PLATFORM=offscreen python main.py --screenshot [--size 560x880]
"""
import os
import sys
import faulthandler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import widgets as W
from main_window import HOME, FUNC_TITLE


def _dump(fn):
    """Capture the current on-screen pixels of `fn` to a temp path, print it."""
    img = fn.grab()
    return img


def render_app(size, outdir, channels=(1,)):
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    from main import App
    a = App(size=size)
    a.show()

    outdir = outdir or os.path.join(HERE, 'screens')
    os.makedirs(outdir, exist_ok=True)

    def pump(n=300):
        for _ in range(n):
            app.processEvents()

    def save(w, name):
        path = os.path.join(outdir, name)
        pm = w.grab()
        ok = pm.save(path)
        saved.append(path)
        print('SAVED  %-42s %dx%d %s' % (
            os.path.relpath(path, HERE), pm.width(), pm.height(),
            'OK' if ok else 'FAIL'))
        return ok

    saved = []

    # ---- intro / connect screen ---------------------------------
    a.stack.setCurrentWidget(a.intro)
    pump()
    save(a, 'intro_connect_%dx%d.png' % size)

    # ---- main view: home grid (the tile menu) --------------------
    a.stack.setCurrentWidget(a.main)
    a.main.set_home()
    pump()
    save(a, 'home_full_%dx%d.png' % size)
    save(a.main, 'home_view_%dx%d.png' % size)

    # ---- each function screen, each channel ---------------------
    order = [f for f, _, _ in W.FUNCTIONS]
    for name in order:
        for ch in channels:
            a.main._chan(ch)
            a.main.show_function(name)
            pump()
            save(a.main, '%s_ch%d_%dx%d.png' % (name, ch, *size))

    # ---- charge screen specifically (has the Start/Stop action row)
    if 'charge' in a.main._screens:
        a.main._chan(1)
        a.main.show_function('charge')
        pump()
        save(a.main, 'charge_actionrow_%dx%d.png' % size)

    print('DONE: %d screenshots in %s' % (len(saved), outdir))
    return True


def run(argv=None):
    argv = argv or sys.argv[1:]
    size = (560, 880)
    if '--size' in argv:
        try:
            w, h = argv[argv.index('--size') + 1].split('x')
            size = (int(w), int(h))
        except (ValueError, IndexError):
            print('bad --size, expected WxH e.g. 392x696')
            return 2
    outdir = None
    if '--out' in argv:
        outdir = argv[argv.index('--out') + 1]

    faulthandler.dump_traceback_later(40, exit=True)  # hard watchdog
    return 0 if render_app(size, outdir) else 1


if __name__ == '__main__':
    sys.exit(run())
