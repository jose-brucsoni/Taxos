# Genera dist/Taxos.exe (Win64, GUI, sin consola).
# Ejecutar en PowerShell desde la raíz del repo, con Python 3.11+ en PATH.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

python -m pip install -e ".[build]"
python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name Taxos `
  --paths src `
  --collect-data taxos `
  --hidden-import taxos.gui.wizard `
  src/taxos/run_gui.py

Write-Host "Ejecutable: $Root\dist\Taxos.exe"
