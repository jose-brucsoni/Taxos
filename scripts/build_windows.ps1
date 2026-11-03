# Genera dist/Taxos/ (onedir, GUI + splash) y Taxos-win64.zip.
# Ejecutar en PowerShell desde Win64, con Python 3.11+ en PATH.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

python -m pip install -e ".[build]"
python -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --name Taxos `
  --splash assets/splash.png `
  --paths src `
  --collect-data taxos `
  --collect-all customtkinter `
  --hidden-import taxos.gui.wizard `
  src/taxos/run_gui.py

$ZipPath = Join-Path $Root "dist\Taxos-win64.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path (Join-Path $Root "dist\Taxos") -DestinationPath $ZipPath

Write-Host "Carpeta:  $Root\dist\Taxos\Taxos.exe"
Write-Host "ZIP:      $ZipPath"
