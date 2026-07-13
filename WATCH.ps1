param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "verify", "demo", "export", "api")]
    [string]$Command = "verify"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

switch ($Command) {
    "setup"  { & (Join-Path $Root "scripts\setup.ps1") }
    "verify" { & (Join-Path $Root "scripts\verify.ps1") }
    "demo"   { & (Join-Path $Root "scripts\run-demo.ps1") }
    "export" { & (Join-Path $Root "scripts\export-review.ps1") }
    "api"    { & (Join-Path $Root "scripts\run-api.ps1") }
}
