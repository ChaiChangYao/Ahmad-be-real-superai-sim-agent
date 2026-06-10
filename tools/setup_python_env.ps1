param(
  [string]$VenvName = ".venv"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

python -m venv $VenvName
& ".\\$VenvName\\Scripts\\Activate.ps1"
python -m pip install --upgrade pip
pip install -r apps/api/requirements.txt

Write-Host "Python environment ready. Activate with .\\$VenvName\\Scripts\\Activate.ps1"
