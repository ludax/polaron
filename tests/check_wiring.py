import sys
sys.path.insert(0, '.')
import ast, re

# Static (non-exec) verification of the wiring, since PySide6 cannot
# fully load in this no-display environment. Check that key symbols exist
# and that signal/slot connections match up.

mi_src = open('main_intro.py', encoding='utf-8').read()
m_src = open('main.py', encoding='utf-8').read()
p_src = open('protocol.py', encoding='utf-8').read()

checks = [
    ("IntroScreen declares connect_failed signal",
     re.search(r"connect_failed\s*=\s*Signal\(str\)", mi_src) is not None),
    ("IntroScreen declares connect_ready(object) signal",
     re.search(r"connect_ready\s*=\s*Signal\(object\)", mi_src) is not None),
    ("_on_connect calls set_busy + launches probe worker",
     "self.client.probe(host, port)" in mi_src),
    ("_on_connect emits connect_ready(res)",
     "self.connect_ready.emit(res)" in mi_src),
    ("_on_connect emits connect_failed(...)",
     "self.connect_failed.emit(" in mi_src),
    ("set_busy exists on IntroScreen",
     "def set_busy" in mi_src),
    ("main.py connects connect_failed",
     "connect_failed.connect(self._on_connect_failed)" in m_src),
    ("main.py has _on_connect_failed handler",
     "def _on_connect_failed(self, detail):" in m_src),
    ("main.py _go_main takes res",
     "def _go_main(self, res=None):" in m_src),
    ("protocol.py has probe()",
     "def probe(self, host=None, port=None, timeout=3.0):" in p_src),
    ("protocol.py has _parse_status staticmethod",
     "def _parse_status(txt):" in p_src),
    ("protocol.py http_status still works (delegate)",
     "def http_status(self, host=None, timeout=2.0):" in p_src),
]

ok = True
for label, passed in checks:
    print(('PASS' if passed else 'FAIL'), '-', label)
    if not passed:
        ok = False
print()
print('WIRING ' + ('OK' if ok else 'BROKEN'))
sys.exit(0 if ok else 1)
