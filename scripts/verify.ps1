$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        throw "Python was not found. Run .\WATCH.ps1 setup after installing Python 3.11 or later."
    }
    $Python = $PythonCommand.Source
}

& $Python -m ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m mypy src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "WATCH verification PASS" -ForegroundColor Green
