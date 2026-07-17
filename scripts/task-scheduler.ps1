param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("plan", "install", "verify", "uninstall", "rollback")]
    [string]$Action,

    [string]$TaskName = "WATCH-DueRunner",

    [ValidateRange(5, 1440)]
    [int]$IntervalMinutes = 15,

    [ValidateRange(1, 10)]
    [int]$MaxWork = 1,

    [string]$Workspace,

    [string]$EvidenceDirectory,

    [string]$StatePath,

    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Resolve-WatchPath {
    param(
        [AllowEmptyString()]
        [string]$Value,
        [Parameter(Mandatory = $true)]
        [string]$DefaultValue
    )

    $Candidate = if ($Value) { $Value } else { $DefaultValue }
    if ($Candidate.Contains('"')) {
        throw "Paths containing double quotes are not supported: $Candidate"
    }
    return [System.IO.Path]::GetFullPath($Candidate)
}

function Quote-WatchArgument {
    param([Parameter(Mandatory = $true)][string]$Value)
    if ($Value.Contains('"')) {
        throw "Arguments containing double quotes are not supported: $Value"
    }
    return '"' + $Value + '"'
}

if ($TaskName -notmatch '^[A-Za-z0-9._-]{1,120}$') {
    throw "TaskName must use only letters, digits, dot, underscore, or hyphen."
}

$Workspace = Resolve-WatchPath -Value $Workspace -DefaultValue (Join-Path $Root ".watch-data")
$EvidenceDirectory = Resolve-WatchPath -Value $EvidenceDirectory -DefaultValue (Join-Path $Root "artifacts\runner")
$StatePath = Resolve-WatchPath -Value $StatePath -DefaultValue (Join-Path $Root ".watch-data\scheduler\task-state.json")
$InvocationScript = [System.IO.Path]::GetFullPath((Join-Path $Root "scripts\invoke-scheduled-run.ps1"))
$PowerShellPath = (Get-Command powershell.exe -ErrorAction Stop).Source
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$ActionArguments = @(
    "-NoProfile"
    "-NonInteractive"
    "-ExecutionPolicy Bypass"
    "-File $(Quote-WatchArgument $InvocationScript)"
    "-MaxWork $MaxWork"
    "-Workspace $(Quote-WatchArgument $Workspace)"
    "-EvidenceDirectory $(Quote-WatchArgument $EvidenceDirectory)"
) -join " "

$Manifest = [ordered]@{
    schema_version = 1
    task_name = $TaskName
    interval_minutes = $IntervalMinutes
    max_work = $MaxWork
    workspace = $Workspace
    evidence_directory = $EvidenceDirectory
    state_path = $StatePath
    powershell_path = $PowerShellPath
    invocation_script = $InvocationScript
    action_arguments = $ActionArguments
    working_directory = $Root
    principal_user = $CurrentUser
    principal_logon_type = "Interactive"
    run_level = "Limited"
    multiple_instances = "IgnoreNew"
    execution_time_limit_minutes = 30
    start_when_available = $true
    stores_credentials = $false
    scheduled_process = "foreground-one-shot"
}

function Write-Manifest {
    param([Parameter(Mandatory = $true)][object]$Value)
    $Json = $Value | ConvertTo-Json -Depth 8
    if ($OutputPath) {
        $ResolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
        $OutputDirectory = Split-Path -Parent $ResolvedOutput
        if ($OutputDirectory) {
            New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
        }
        $Json | Set-Content -Path $ResolvedOutput -Encoding utf8
        Write-Host "Evidence: $ResolvedOutput" -ForegroundColor Cyan
    }
    Write-Output $Json
}

if ($Action -eq "plan") {
    Write-Manifest -Value $Manifest
    exit 0
}

$RequiredCommands = @(
    "Get-ScheduledTask",
    "Export-ScheduledTask",
    "Register-ScheduledTask",
    "Unregister-ScheduledTask",
    "New-ScheduledTaskAction",
    "New-ScheduledTaskTrigger",
    "New-ScheduledTaskSettingsSet",
    "New-ScheduledTaskPrincipal",
    "New-ScheduledTask"
)
foreach ($CommandName in $RequiredCommands) {
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "Required ScheduledTasks command is unavailable: $CommandName"
    }
}

if ($Action -eq "install") {
    $StateDirectory = Split-Path -Parent $StatePath
    New-Item -ItemType Directory -Path $StateDirectory -Force | Out-Null
    New-Item -ItemType Directory -Path $EvidenceDirectory -Force | Out-Null

    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    $BackupPath = $null
    if ($ExistingTask) {
        $BackupDirectory = Join-Path $StateDirectory "backups"
        New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
        $BackupStamp = [DateTimeOffset]::UtcNow.ToString("yyyyMMdd-HHmmss-fff")
        $BackupPath = Join-Path $BackupDirectory "$TaskName-$BackupStamp.xml"
        Export-ScheduledTask -TaskName $TaskName | Set-Content -Path $BackupPath -Encoding Unicode
    }

    $TaskAction = New-ScheduledTaskAction `
        -Execute $PowerShellPath `
        -Argument $ActionArguments `
        -WorkingDirectory $Root
    $TaskTrigger = New-ScheduledTaskTrigger `
        -Once `
        -At ((Get-Date).AddMinutes(1)) `
        -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
        -RepetitionDuration (New-TimeSpan -Days 3650)
    $TaskSettings = New-ScheduledTaskSettingsSet `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
        -StartWhenAvailable
    $TaskPrincipal = New-ScheduledTaskPrincipal `
        -UserId $CurrentUser `
        -LogonType Interactive `
        -RunLevel Limited
    $TaskDefinition = New-ScheduledTask `
        -Action $TaskAction `
        -Trigger $TaskTrigger `
        -Settings $TaskSettings `
        -Principal $TaskPrincipal `
        -Description "WATCH bounded one-shot due runner"

    Register-ScheduledTask -TaskName $TaskName -InputObject $TaskDefinition -Force | Out-Null

    $State = [ordered]@{
        schema_version = 1
        installed_at = [DateTimeOffset]::UtcNow.ToString("o")
        task_name = $TaskName
        previous_task_backup = $BackupPath
        manifest = $Manifest
    }
    $State | ConvertTo-Json -Depth 8 | Set-Content -Path $StatePath -Encoding utf8
    Write-Manifest -Value ([ordered]@{
        result = "installed"
        task_name = $TaskName
        state_path = $StatePath
        previous_task_backup = $BackupPath
        manifest = $Manifest
    })
    exit 0
}

if ($Action -eq "verify") {
    $Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $Task) {
        Write-Manifest -Value ([ordered]@{
            result = "missing"
            task_name = $TaskName
            valid = $false
            mismatches = @("task-not-found")
        })
        exit 1
    }

    $Mismatches = @()
    $RegisteredAction = $Task.Actions | Select-Object -First 1
    if ($RegisteredAction.Execute -ne $PowerShellPath) {
        $Mismatches += "execute"
    }
    if ($RegisteredAction.Arguments -ne $ActionArguments) {
        $Mismatches += "arguments"
    }
    if ($RegisteredAction.WorkingDirectory -ne $Root) {
        $Mismatches += "working-directory"
    }
    if ([string]$Task.Settings.MultipleInstances -ne "IgnoreNew") {
        $Mismatches += "multiple-instances"
    }
    if ([string]$Task.Principal.RunLevel -notin @("Limited", "LeastPrivilege")) {
        $Mismatches += "run-level"
    }

    $Valid = $Mismatches.Count -eq 0
    Write-Manifest -Value ([ordered]@{
        result = $(if ($Valid) { "verified" } else { "mismatch" })
        task_name = $TaskName
        valid = $Valid
        mismatches = $Mismatches
        manifest = $Manifest
    })
    if (-not $Valid) { exit 1 }
    exit 0
}

if ($Action -eq "uninstall") {
    $Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($Task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    Write-Manifest -Value ([ordered]@{
        result = "uninstalled"
        task_name = $TaskName
        state_preserved = $(Test-Path $StatePath)
        operational_evidence_preserved = $true
    })
    exit 0
}

if ($Action -eq "rollback") {
    if (-not (Test-Path $StatePath)) {
        throw "Scheduler state was not found: $StatePath"
    }
    $State = Get-Content -Raw $StatePath | ConvertFrom-Json
    $BackupPath = [string]$State.previous_task_backup
    if (-not $BackupPath -or -not (Test-Path $BackupPath)) {
        throw "No previous task backup is available for rollback."
    }

    $CurrentTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($CurrentTask) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    $BackupXml = Get-Content -Raw $BackupPath
    Register-ScheduledTask -TaskName $TaskName -Xml $BackupXml | Out-Null
    Write-Manifest -Value ([ordered]@{
        result = "rolled-back"
        task_name = $TaskName
        restored_from = $BackupPath
    })
    exit 0
}
