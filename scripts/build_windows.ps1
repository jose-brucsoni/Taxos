# Genera dist/Taxos/ (onedir, GUI web) y Taxos-win64.zip.
# Requiere Node 20+ (para ui/) y Python 3.11+ / .venv.
# Ejecutar en PowerShell desde Win64.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

$Npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $Npm) {
    throw "npm no está en PATH. Instala Node.js LTS y vuelve a intentar."
}

Push-Location (Join-Path $Root "ui")
try {
    if (-not (Test-Path "node_modules")) {
        npm ci
        if ($LASTEXITCODE -ne 0) { npm install }
    } else {
        npm ci
        if ($LASTEXITCODE -ne 0) { npm install }
    }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Falló npm run build" }
}
finally {
    Pop-Location
}

& $Python -m pip install -e ".[build]"
& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --name Taxos `
  --paths src `
  --collect-data taxos `
  --add-data "ui/dist;ui/dist" `
  --hidden-import taxos.gui.webview_app `
  --hidden-import taxos.gui.api `
  src/taxos/run_gui.py

# Evitar bloqueos: proceso abierto, OneDrive o antivirus.
Get-Process -Name Taxos -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

$DistTaxos = Join-Path $Root "dist\Taxos"
$ZipPath = Join-Path $Root "dist\Taxos-win64.zip"
$Stage = Join-Path $env:TEMP "Taxos-win64-stage"

function Compress-DirectoryShared {
    param(
        [Parameter(Mandatory = $true)][string]$SourceDir,
        [Parameter(Mandatory = $true)][string]$DestinationZip
    )
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem

    if (Test-Path $DestinationZip) { Remove-Item $DestinationZip -Force }

    $sourceFull = (Resolve-Path $SourceDir).Path
    $parentName = Split-Path $sourceFull -Leaf
    $zip = [System.IO.Compression.ZipFile]::Open(
        $DestinationZip,
        [System.IO.Compression.ZipArchiveMode]::Create
    )
    try {
        Get-ChildItem -Path $sourceFull -Recurse -File | ForEach-Object {
            $relative = $_.FullName.Substring($sourceFull.Length).TrimStart("\")
            $entryName = ($parentName + "/" + $relative).Replace("\", "/")
            $fs = [System.IO.File]::Open(
                $_.FullName,
                [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::Read,
                [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
            )
            try {
                $entry = $zip.CreateEntry(
                    $entryName,
                    [System.IO.Compression.CompressionLevel]::Optimal
                )
                $entryStream = $entry.Open()
                try {
                    $fs.CopyTo($entryStream)
                }
                finally {
                    $entryStream.Dispose()
                }
            }
            finally {
                $fs.Dispose()
            }
        }
    }
    finally {
        $zip.Dispose()
    }
}

try {
    if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
    New-Item -ItemType Directory -Path $Stage | Out-Null
    Copy-Item -Path $DistTaxos -Destination (Join-Path $Stage "Taxos") -Recurse

    $maxAttempts = 5
    $zipOk = $false
    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        try {
            $TempZip = Join-Path $env:TEMP "Taxos-win64.zip"
            if (Test-Path $TempZip) { Remove-Item $TempZip -Force }
            Compress-DirectoryShared -SourceDir (Join-Path $Stage "Taxos") -DestinationZip $TempZip
            if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
            Copy-Item -Path $TempZip -Destination $ZipPath -Force
            Remove-Item $TempZip -Force -ErrorAction SilentlyContinue
            $zipOk = $true
            break
        }
        catch {
            if ($attempt -eq $maxAttempts) { throw }
            Write-Host "ZIP bloqueado (intento $attempt/$maxAttempts); reintentando en 2s..."
            Write-Host "  $($_.Exception.Message)"
            Start-Sleep -Seconds 2
        }
    }
    if (-not $zipOk) {
        throw "No se pudo crear $ZipPath tras $maxAttempts intentos."
    }
}
finally {
    if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force -ErrorAction SilentlyContinue }
}

Write-Host "Carpeta:  $Root\dist\Taxos\Taxos.exe"
Write-Host "ZIP:      $ZipPath"
