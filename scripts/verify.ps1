$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    & (Join-Path $Root "scripts\setup.ps1")
}

$Artifacts = Join-Path $Root "artifacts\windows-verification"
New-Item -ItemType Directory -Path $Artifacts -Force | Out-Null

function Invoke-CheckedPython {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$LogName
    )

    $LogPath = Join-Path $Artifacts $LogName
    $ErrorPath = Join-Path $Artifacts "$LogName.stderr"
    $Process = Start-Process `
        -FilePath $Python `
        -ArgumentList $Arguments `
        -NoNewWindow `
        -Wait `
        -PassThru `
        -RedirectStandardOutput $LogPath `
        -RedirectStandardError $ErrorPath

    if (Test-Path $LogPath) { Get-Content $LogPath | Write-Host }
    if (Test-Path $ErrorPath) { Get-Content $ErrorPath | Write-Host }
    if ($Process.ExitCode -ne 0) {
        throw "Command failed with exit code $($Process.ExitCode). See $LogPath and $ErrorPath"
    }
}

Invoke-CheckedPython -Arguments @("-m", "ruff", "check", ".") -LogName "ruff.txt"
Invoke-CheckedPython -Arguments @("-m", "mypy", "src") -LogName "mypy.txt"
Invoke-CheckedPython -Arguments @(
    "-m", "pytest", "--junitxml=$Artifacts\test-results.xml"
) -LogName "pytest.txt"

Write-Host "WATCH verification PASS" -ForegroundColor Green
