$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

Invoke-Checked { & .\.venv\Scripts\python.exe -m ruff check backend }
Invoke-Checked { & .\.venv\Scripts\python.exe -m ruff format --check backend }
Invoke-Checked { & .\.venv\Scripts\python.exe -m mypy backend/app }
Invoke-Checked { & .\.venv\Scripts\python.exe -m pytest --cov --cov-report=term }
Push-Location frontend
try {
    Invoke-Checked { npm.cmd run typecheck }
    Invoke-Checked { npm.cmd test }
    Invoke-Checked { npm.cmd run build }
    Invoke-Checked { npm.cmd audit --omit=dev }
} finally {
    Pop-Location
}
