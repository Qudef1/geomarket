$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Push-Location frontend
try {
    npm.cmd ci
} finally {
    Pop-Location
}

Write-Host "Ready. Activate with: .\.venv\Scripts\Activate.ps1"

