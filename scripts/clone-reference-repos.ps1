$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$refs = Join-Path $root "external/references"
New-Item -ItemType Directory -Force -Path $refs | Out-Null

function Clone-Or-Update($url, $path) {
    if (Test-Path $path) {
        Write-Host "Updating $path"
        git -C $path pull --ff-only
    } else {
        Write-Host "Cloning $url -> $path"
        git clone --depth 1 $url $path
    }
}

Clone-Or-Update "https://github.com/copilotkit/copilotkit" (Join-Path $refs "copilotkit")
Clone-Or-Update "https://github.com/vercel/ai-chatbot" (Join-Path $refs "vercel-ai-chatbot")
Clone-Or-Update "https://github.com/mmatl/urdfpy" (Join-Path $refs "urdfpy")
Clone-Or-Update "https://github.com/mikedh/trimesh" (Join-Path $refs "trimesh")
Clone-Or-Update "https://github.com/cadquery/cadquery" (Join-Path $refs "cadquery")
Clone-Or-Update "https://github.com/pydantic/pydantic-ai" (Join-Path $refs "pydantic-ai")
Clone-Or-Update "https://github.com/crewAIInc/crewAI" (Join-Path $refs "crewai")
Clone-Or-Update "https://github.com/e2b-dev/E2B" (Join-Path $refs "e2b")
# Official repo: Genesis-Embodied-AI/Genesis (pip: genesis-world). Alias path for audit docs.
Clone-Or-Update "https://github.com/Genesis-Embodied-AI/Genesis" (Join-Path $refs "genesis-world")

Write-Host "Reference repos ready under $refs"
