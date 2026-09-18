$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

if (-not (Test-Path ".venv")) {
    Invoke-Checked { python -m venv .venv }
}

Invoke-Checked { & .\.venv\Scripts\python.exe -m pip install --upgrade pip }
Invoke-Checked { & .\.venv\Scripts\python.exe -m pip install -e ".[dev]" }
Push-Location frontend
try {
    Invoke-Checked { npm.cmd ci }
} finally {
    Pop-Location
}

Write-Host "Ready. Activate with: .\.venv\Scripts\Activate.ps1"
