# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — Charger Link (PySide6)
#
# Builds a one-directory, windowed app:
#   Linux:   dist/ChargerLink/ChargerLink
#   Windows: dist/ChargerLink/ChargerLink.exe
#
# Usage: pyinstaller --noconfirm chargerlink.spec
#
# Note: run this spec ON the OS you want to build for (PyInstaller does not
# cross-compile). The spec itself is portable / OS-agnostic.

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # (source, dest) — assets dir lands next to the executable (Linux)
        # or in <appdir>/_internal (Windows, PyInstaller 6+). assets.py
        # resolves both locations at runtime.
        ('assets', 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChargerLink',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # windowed: no console window on Windows
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='ChargerLink',
)
