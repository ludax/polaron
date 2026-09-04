# Polaron / Charger Link — Windows GUI rebuild

Rebuild of Graupner "Charger Link" (com.graupner.chargerm v1.1) as a cross-OS
PySide6 desktop app; target deliverable includes a Windows build (PyInstaller).

## Repo state (2026-09-04)
- First import commit: 79454ce "Import current ChargerLink working copy" (from /opt/data/chargerlink)
- Remote: https://github.com/ludax/polaron.git (branch main)
- Auth: fine-grained PAT via askpass (~/.gitconfig credential.https://github.com.askpass -> /opt/data/home/gh-askpass.sh). Works with username=ludax + token. Do NOT use x-access-token user (GitHub 401s); do NOT use ~/.git-credentials (write pipeline on this host redacts secrets to literal ***).

## Code map
- protocol.py — TCP binary protocol client (byte-sum checksum, retry=5) + HTTP status. GROUND TRUTH: skill `polaron-charger-controller` -> references/protocol-details.md (byte-verified from APK /opt/data/Graupner_Charger_Link_1.1.apk, sha256 f6953e7e....cc)
- assets.py — asset dir resolution (assets/*.png from APK res/drawable)
- widgets.py — shared Qt widgets (titlebar, channel bar, icons strip)
- screens_base.py — BaseScreen (property list + ActionRow)
- screens.py — 8 function screens (Charge/Discharge/Cycle/Setting/Profile/Store/Balance/Data)
- main_intro.py — intro/connect screen + StatusBar
- main_window.py — MainView: titlebar + channel bar + icon strip + screen stack
- main.py — app wiring, logging to chargerlink.log, --screenshot mode (imports `screenshots` module — NOT YET IN REPO, see known-issues)
- screens/*.png — reference screenshots of each screen (original app)

## Known issues / next tasks (in suggested order)
1. MESSY: main.py imports `screenshots` module for --screenshot but it was never committed. Either create screenshots.py (render intro + 8 screens offscreen to PNGs) or drop the flag.
2. main_intro.py may be a stale duplicate of the intro path used by main.py (it defines IntroScreen+StatusBar; verify no dead code).
3. protocol.py: add byte-level unit tests against protocol-details.md vectors (build/checksum/retry/result codes). Currently untested.
4. HTTP path: /status (read) and /settingssave (write) on 192.168.4.1 — verify payloads match original GrHttpConnection; SettingScreen._save currently sends raw SSID bytes, needs the real frame/payload shape.
5. PyInstaller spec + requirements.txt (PySide6) for the Windows build. No build config in repo yet.
6. README.md with run instructions.

## Workflow
- Max 3 subagents parallel; never 2 on the same file.
- Subagent pattern: implementer -> spec-compliance review -> quality review; orchestrator (main session) runs pytest itself and commits per task.
- TDD for protocol work; screenshots for UI fidelity vs screens/*.png references.
