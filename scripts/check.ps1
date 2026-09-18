$ErrorActionPreference = "Stop"

& .\.venv\Scripts\python.exe -m ruff check backend
& .\.venv\Scripts\python.exe -m ruff format --check backend
& .\.venv\Scripts\python.exe -m mypy backend/app
& .\.venv\Scripts\python.exe -m pytest --cov --cov-report=term
Push-Location frontend
try {
    npm.cmd run typecheck
    npm.cmd test
    npm.cmd run build
    npm.cmd audit --omit=dev
} finally {
    Pop-Location
}

