param(
    [string]$Workspace = ".watch-data",
    [string]$HostAddress = "127.0.0.1",
    [ValidateRange(1, 65535)]
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    & (Join-Path $Root "scripts\setup.ps1")
}

$ResolvedWorkspace = [System.IO.Path]::GetFullPath((Join-Path $Root $Workspace))
$env:WATCH_WORKSPACE = $ResolvedWorkspace

Write-Host "WATCH Operator API" -ForegroundColor Cyan
Write-Host "Workspace: $ResolvedWorkspace"
Write-Host "URL: http://${HostAddress}:$Port"
Write-Host "OpenAPI: http://${HostAddress}:$Port/docs"

& $Python -m uvicorn watch.api:app --host $HostAddress --port $Port
