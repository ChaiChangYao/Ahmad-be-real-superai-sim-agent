# Start Buildables API from repo root (auto-detects genesis-world / genesis-nyx clones).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$world = Join-Path $Root "genesis-world"
$nyx = Join-Path $Root "genesis-nyx"
if (Test-Path $world) { $env:GENESIS_WORLD_ROOT = $world }
if (Test-Path $nyx) { $env:GENESIS_NYX_ROOT = $nyx }

# Genesis banner uses Unicode box-drawing; Windows cp1252 consoles log encoding errors without this.
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "GENESIS_WORLD_ROOT=$env:GENESIS_WORLD_ROOT"
Write-Host "GENESIS_NYX_ROOT=$env:GENESIS_NYX_ROOT"
Write-Host "Starting API on http://127.0.0.1:8000 (no --reload for Genesis on Windows)..."

uvicorn main:app --app-dir apps/api --host 127.0.0.1 --port 8000
