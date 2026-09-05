# Polaron / Charger Link — cross-OS GUI rebuild

Rebuild of Graupner "Charger Link" (`com.graupner.chargerm` v1.1) as a
cross-platform **PySide6** desktop app for Polaron / Graupner smart chargers.
Faithful to the original: intro/Connect (WiFi info + host/port), red titlebar,
Ch1 / Ch2 channel bar, glossy function strip, and the 8 function screens
(Charge / Discharge / Cycle / Setting / Profile / Store / Balance / Data),
driven by the byte-verified charger protocol.

Protocol ground truth is byte-verified against the original APK
(`com/graupner/chargerm/model/Operator`), including the frame layout,
byte-sum checksum, and command codes. See `protocol.py` docstring and
`tests/test_protocol.py`.

## Layout
- `main.py` — entry point: `python main.py` (GUI) or `python main.py --screenshot`
- `protocol.py` — thread-safe TCP/HTTP BLE-less client of the charger
- `screens.py` / `screens_base.py` / `widgets.py` / `assets.py` — UI
- `screenshots.py` — headless renderer (intro + all screens → PNG)
- `chargerlink.spec` + `build_linux.sh` / `build_windows.ps1` — packaging
- `tests/` — byte-level protocol tests (pytest)

## Install (dev)
```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt   # PySide6
.venv/bin/pip install pytest pytest-qt      # for tests
```

## Run
```bash
python main.py                  # GUI (needs a charger on the network)
python main.py --screenshot     # render all screens to ./screenshots_out/
```

## Tests
```bash
.venv/bin/pytest -q
```

## Build
PyInstaller does **not** cross-compile — build on the OS you ship.

### Linux
```bash
./build_linux.sh          # uses /opt/data/chargerview-env by default (VENV=... to override)
# -> dist/ChargerLink/ChargerLink
```

### Windows (target deliverable)
On the Windows machine, in the repo root:
```powershell
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
# -> dist\ChargerLink\ChargerLink.exe
```
The result is a self-contained `dist\ChargerLink\` folder — zip it and it runs
on any Windows box with no Python installed.

## Notes
- The asset bundle (`assets/`) is resolved both in dev and in a frozen bundle
  (`assets.py` handles `sys.frozen` + PyInstaller `_internal`).
- The app talks to the charger's own WiFi AP (default `192.168.4.1`, TCP 23)
  and via HTTP discovery on `http://192.168.4.1`.
