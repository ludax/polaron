# Build ChargerLink on Windows (PyInstaller cannot cross-compile — run ON Windows).
#
# Prereqs: Python 3.10+ on PATH, and:
#     pip install -r requirements.txt pyinstaller
#
# Output: dist\ChargerLink\ChargerLink.exe  (a self-contained folder you can zip & ship)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "==> First run: installing build deps"
    python -m pip install -r requirements.txt pyinstaller
}

Write-Host "==> Building ChargerLink (Windows, onedir, windowed)"
python -m PyInstaller --noconfirm --clean chargerlink.spec

Write-Host "==> Done"
Write-Host "    App dir : $PSScriptRoot\dist\ChargerLink"
Write-Host "    Binary  : dist\ChargerLink\ChargerLink.exe"
Write-Host "    Run     : dist\ChargerLink\ChargerLink.exe"
