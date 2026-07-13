$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    & (Join-Path $Root "scripts\setup.ps1")
}

& $Python -m watch.cli demo --workspace (Join-Path $Root ".watch-data")

Write-Host "WATCH demo PASS" -ForegroundColor Green
Write-Host "Generated evidence: $(Join-Path $Root '.watch-data')" -ForegroundColor Cyan
