$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    & (Join-Path $Root "scripts\setup.ps1")
}

& $Python -m ruff check .
& $Python -m mypy src
& $Python -m pytest

Write-Host "WATCH verification PASS" -ForegroundColor Green
