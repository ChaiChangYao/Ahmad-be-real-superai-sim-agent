# Start Buildables Sim — backend + frontend in separate processes
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Stopping stale processes on ports 8000 and 3000..."
foreach ($port in @(8000, 3000)) {
    $lines = netstat -ano | Select-String ":$port\s"
    foreach ($line in $lines) {
        if ($line -match '\s(\d+)\s*$') {
            $procId = $Matches[1]
            if ($procId -ne "0") {
                Write-Host "  Killing PID $procId on port $port"
                taskkill /PID $procId /F 2>$null | Out-Null
            }
        }
    }
}

Start-Sleep -Seconds 1

$NextCache = Join-Path $Root "apps\web\.next"
if (Test-Path $NextCache) {
    Write-Host "Clearing stale Next.js cache (.next)..."
    Remove-Item -Recurse -Force $NextCache -ErrorAction SilentlyContinue
}

Write-Host "Starting API on http://127.0.0.1:8000 ..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$Root'; uvicorn main:app --reload --app-dir apps/api --host 127.0.0.1 --port 8000"
)

Start-Sleep -Seconds 2

Write-Host "Starting web UI on http://localhost:3000 ..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$Root'; npm run dev:web"
)

Write-Host ""
Write-Host "Open: http://localhost:3000"
Write-Host "API:  http://127.0.0.1:8000/health"
