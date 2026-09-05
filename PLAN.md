# Polaron / Charger Link — cross-OS PySide6 rebuild

Rebuild of Graupner "Charger Link" (com.graupner.chargerm v1.1) as a cross-OS
PySide6 desktop app. Target deliverable: a faithful desktop clone + a Windows
build (PyInstaller). Reference app is the iPhone (iOS) screenshots at
/opt/data/apkx/store/{home,startup}_screen.webp (392x696) and the APK's
res/layout + res/drawable assets.

## Repo state (2026-09-05)
- Branch: main. Remote: https://github.com/ludax/polaron.git
- History: 79454ce import -> 50507e3 PLAN.md -> (this commit) UI-fidelity rewrite + build scaffolding.
- Venv: /opt/data/chargerview-env (Py 3.13.5, PySide6 6.11.2, pytest, pytest-qt, Pillow, numpy, PyInstaller).
- Run:  /opt/data/chargerview-env/bin/python main.py            (live window)
-      /opt/data/chargerview-env/bin/python main.py --screenshot WxH ...
- Render offscreen (CI/verify, no display):
      export LD_LIBRARY_PATH=/opt/data/qtlibs:$LD_LIBRARY_PATH QT_QPA_PLATFORM=offscreen
      /opt/data/chargerview-env/bin/python screenshots.py --size 392x696
  (offscreen needs the faulthandler watchdog inside screenshots.py, or it hangs)
- Auth for push: fine-grained PAT via git askpass (~/.gitconfig credential.https://github.com.askpass -> /opt/data/home/gh-askpass.sh); username=ludax + token.
  GOTCHA: do NOT use x-access-token user (GitHub 401s); do NOT use ~/.git-credentials
  (this host's write pipeline redacts secrets to literal ***). Pass the token via the askpass/env path only.

## Code map
- protocol.py        — TCP binary protocol client (byte-sum checksum, REQUEST_RETRY_COUNT=5) + HTTP status.
                       GROUND TRUTH: skill `polaron-charger-controller` -> references/protocol-details.md
                       (byte-verified from APK /opt/data/Graupner_Charger_Link_1.1.apk, sha256 f6953e7e...cc).
- sizing.py          — PROPORTIONAL SIZING. Anchor = window WIDTH. base px constants (TITLEBAR_H=78,
                       SPINNER_ROW_H=60, ICON_PX=85, LABEL_PX=32, CHBAR_H=68, CHINFO_D=40, ACTION_BTN=45,
                       BACK_BTN=40, TITLE_SIZE=24, ...) + scale(base_px, window_width) helper.
                       All widths/heights flow through scale() so the UI scales with window size.
- assets.py          — asset dir resolution (assets/*.png copied from APK res/drawable).
- widgets.py         — shared Qt widgets. Titlebar (red band #CC0001: back + title + right text, then a white
                       spinner/control row). FunctionStrip = 3x3 icon grid (icon + label per cell; 9th cell empty,
                       like the original) — this is the HOME screen, emitted via `activated(name)`. ChannelBar =
                       bottom CH1/CH2 segments + info circle. FUNCTIONS list = phone order:
                       profile, charge, discharge, cycle, balance, data, setting(user_set), store.
- screens_base.py    — BaseScreen (property list + ActionRow Start/Stop). ActionRow buttons sized via sizing.scale().
- screens.py         — 8 function screens (Charge/Discharge/Cycle/Balance/Data/UserSet/Profile/Store).
- main_intro.py      — IntroScreen + StatusBar (welcome/connect screen shown before the app).
- main_window.py     — MainView: titlebar(top) + QStackedWidget(center) + channelbar(bottom).
                       The 3x3 FunctionStrip is the HOME PAGE of the stack; each function screen is another page.
                       set_home() / show_function(name) / back button navigates. HOME is the default page
                       (matches reference home_screen.webp which is the grid, NOT a function screen).
- main.py            — app wiring, logging to chargerlink.log. --screenshot WxH delegates to screenshots.py.
                       --size WxH sets the desktop window. --screenshot mode is headless-safe.
- screenshots.py     — OFFSCREEN renderer: builds App, pumps events, saves intro + home + every function
                       screen (CH1/CH2) as PNG to screens/. Use this for CI/verify (no display needed).
- chargerlink.spec, build_linux.sh, build_windows.ps1 — PyInstaller packaging (one window, bundle assets/ + qml if any).
- requirements.txt, pyproject.toml, README.md — deps / project meta / run+build instructions.
- screens/*.png      — REGENERATED reference renders (home_full, home_view, intro_connect, and per-screen ch1/ch2),
                       at the reference 392x696. Older 01_*/02_* PNGs were superseded (removed).

## UI reference geometry (measured, 392x696 target; keep proportional)
- Titlebar: red band ~y0-78 (back circle left, title center, version/info right), then a white control/spinner row ~y78-136.
- 3x3 icon grid: circles ~73-86px, centered, labels under each; 9th slot empty. Rows at y~186/322/454 (3x3).
- Bottom channel bar: ~y613-695, CH1 (active=red) + CH2 (inactive=gray) + info (i) circle on the right.
- Back button: btn_back.png is a CIRCLE with a left chevron (NOT a brand logo).
- Order (left-to-right, top-to-bottom): Profile, Charge, Discharge / Cycle, Balance, Data / User Set, Store, (empty).
- Start/Stop: two circular buttons (red play / darker stop) under the property list on each function screen.

## KNOWN ISSUES / next tasks (in suggested order)
1. protocol.py: ADD byte-level unit tests against protocol-details.md vectors (frame build, checksum,
   retry, result codes). Currently untested. NO tests/ dir in repo yet.
   ⚠ NUANCE (do NOT "fix" without a live capture): the APK declares TWO separate code families:
     RESPONSE_ACK=6, RESPONSE_DENY=-18(238), RESPONSE_NACK=21   <- what protocol.py currently has (RSP_*)
     RESULT_FAIL=0, RESULT_ACK=1, RESULT_DENY=254, RESULT_NACK=255
   protocol.py matches the REAL, documented RESPONSE_* set, so it is NOT simply wrong. The old "protocol.py
   wrong" note conflated the two. Before changing anything, confirm which family the wire actually emits
   (best: a live capture, or a second read of Operator in the dex). Do not guess.
2. HTTP path: /status (read) and /settingssave (write) on 192.168.4.1 — verify frames/payloads match original
   GrHttpConnection. SettingScreen save currently sends raw SSID bytes; needs the real payload shape.
3. Verify main_intro.py vs the intro path in main.py — make sure there is no dead/duplicated IntroScreen,
   and that the welcome screen's "connect" flow feeds the main view correctly.
4. Windows build: build_windows.ps1 + chargerlink.spec should be validated on a real Windows box — the
   cross-compile here only produces the Linux artifact. Confirm PySide6 + Qt plugins are bundled.
5. (Optional) Add `pytest` CI: run protocol tests + a smoke screenshot render to screens/ on every push.

## Workflow (for the next session)
- MAX 3 subagents in parallel; NEVER two on the same file.
- Subagent pattern: implementer -> spec-compliance review -> quality review; ORCHESTRATOR (main session)
  runs pytest itself and commits per task. Do NOT let subagents commit.
- TDD for protocol work (write the failing test first against protocol-details.md vectors).
- Screenshots for UI fidelity, compared against the 392x696 references; render with screenshots.py offscreen.
- Commit per logical task. Do NOT commit secrets. Do NOT touch unrelated files.
- If a task needs a live charger (192.168.4.1) and it's not reachable, STOP and report — do not fabricate
  protocol results.

## Handoff summary (what a fresh prompt should know)
- The UI "way off / icons too big" bug is FIXED: it was (a) the 3x3 grid being a permanent strip stacked ABOVE
  the function screens (so grid + property list fought for vertical space and circles clipped to ~33px slivers)
  and (b) sizing anchored to a stale 640px width. Fixed by making the grid a PAGE of the stack (APK-faithful:
  main.xml IS the home grid; charge.xml etc. have no grid) and anchoring all width/height to the fixed app
  window via sizing.scale(). Verified: all 12 screens render clean at 392x696 (full 3x3 circles, labels, CH bar,
  property lists, Start/Stop) — see screens/*.png.
- Phase 2 (UI fidelity) is essentially DONE and verified. Phases: 1 protocol hardening, 2 UI, 3 theme/assets,
  4 HTTP status/save, 5 Windows build. Scaffolding for phase 5 exists; phase 1 (protocol tests) and phase 4
  (HTTP) remain the meaty open work.
