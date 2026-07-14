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

& $Python -m watch.cli demo --workspace (Join-Path $Root ".watch-data")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "WATCH demo PASS" -ForegroundColor Green
Write-Host "Generated evidence: $(Join-Path $Root '.watch-data')" -ForegroundColor Cyan
