param(
    [Parameter(Mandatory = $true)]
    [string]$EvaluatedAt,

    [ValidateRange(1, 10)]
    [int]$MaxWork = 1,

    [string]$Workspace,

    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not $Workspace) {
    $Workspace = Join-Path $Root ".watch-data"
}
if (-not $OutputPath) {
    $OutputDirectory = Join-Path $Root "artifacts\runner"
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputPath = Join-Path $OutputDirectory "due-run-$Timestamp.json"
} else {
    $OutputDirectory = Split-Path -Parent $OutputPath
    if ($OutputDirectory) {
        New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    }
}

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

$Output = & $Python -m watch.cli run-due-once `
    --evaluated-at $EvaluatedAt `
    --max-work $MaxWork `
    --workspace $Workspace 2>&1
$ExitCode = $LASTEXITCODE

if ($ExitCode -ne 0) {
    $Output | ForEach-Object { Write-Error $_ }
    exit $ExitCode
}

$Json = ($Output -join [Environment]::NewLine)
$Json | Set-Content -Path $OutputPath -Encoding utf8
Write-Output $Json
Write-Host "WATCH one-shot due run PASS" -ForegroundColor Green
Write-Host "Evidence: $OutputPath" -ForegroundColor Cyan
