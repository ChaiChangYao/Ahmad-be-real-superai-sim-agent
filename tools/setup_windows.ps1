Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Setting up Buildables Sim Sandbox on Windows..."
Copy-Item .env.example .env -Force

if (!(Test-Path node_modules)) {
  npm install
}

& ".\\tools\\setup_python_env.ps1"

Write-Host "Setup complete."
Write-Host "Start API: .\\.venv\\Scripts\\Activate.ps1; uvicorn main:app --reload --app-dir apps/api"
Write-Host "Start Web: npm run dev:web"
