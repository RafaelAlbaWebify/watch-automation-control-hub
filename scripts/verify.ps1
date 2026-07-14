$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    & (Join-Path $Root "scripts\setup.ps1")
}

$Artifacts = Join-Path $Root "artifacts\windows-verification"
New-Item -ItemType Directory -Path $Artifacts -Force | Out-Null

$RuffLog = Join-Path $Artifacts "ruff.txt"
& $Python -m ruff check . *> $RuffLog
$RuffExit = $LASTEXITCODE
Get-Content $RuffLog | Write-Host
if ($RuffExit -ne 0) { throw "Ruff failed with exit code $RuffExit. See $RuffLog" }

$MypyLog = Join-Path $Artifacts "mypy.txt"
& $Python -m mypy src *> $MypyLog
$MypyExit = $LASTEXITCODE
Get-Content $MypyLog | Write-Host
if ($MypyExit -ne 0) { throw "Mypy failed with exit code $MypyExit. See $MypyLog" }

$PytestLog = Join-Path $Artifacts "pytest.txt"
$JunitPath = Join-Path $Artifacts "test-results.xml"
& $Python -m pytest "--junitxml=$JunitPath" *> $PytestLog
$PytestExit = $LASTEXITCODE
Get-Content $PytestLog | Write-Host
if ($PytestExit -ne 0) { throw "Pytest failed with exit code $PytestExit. See $PytestLog" }

Write-Host "WATCH verification PASS" -ForegroundColor Green
