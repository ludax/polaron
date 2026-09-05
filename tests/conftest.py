"""Test setup for Charger Link protocol tests.

Puts the repo root on sys.path (tests import modules as top-level packages —
`protocol`, `assets`, …) so `pytest tests/` works without an editable install.
Qt is NOT required for the protocol tests; importing `protocol` is side-effect
free (no QApplication).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# NOTE: the protocol tests are pure-Python (no Qt, no GUI, no sockets).
# `pytest tests/` works wherever a Qt binding loads (a typical Windows box,
# or any shell with the Qt system libs on the loader path). On a shell where
# Qt can't import (e.g. libEGL missing), disable the auto-loaded pytest-qt
# plugin with:  pytest tests/ -p no:pytest-qt
# The tests themselves never import Qt, so they pass on a fresh Windows box.
