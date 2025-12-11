param(
  [Parameter(Mandatory=$true)][ValidateSet('register','unregister','start','stop','status')][string]$action
)

$taskName = 'AGL Harvester'
$repo = (Resolve-Path "$PSScriptRoot\..").Path
$harvestScript = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Set-Location ''{0}''; .\scripts\harvest_run.ps1"' -f $repo

function Register-Task {
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -Command \"Set-Location '$repo'; .\\scripts\\harvest_run.ps1 *>> $repo\\artifacts\\harvester.log\""
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration ([TimeSpan]::MaxValue)
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Description 'Run AGL Harvester every 15 minutes' -Force
    Write-Output "Registered scheduled task: $taskName"
}

function Unregister-Task {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output "Unregistered scheduled task: $taskName"
}

function Start-TaskNow { Start-ScheduledTask -TaskName $taskName; Write-Output 'Started scheduled task' }
function Stop-TaskNow { Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue; Write-Output 'Stopped scheduled task' }
function Status-Task { Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State | Format-List }

switch ($action) {
    'register' { Register-Task }
    'unregister' { Unregister-Task }
    'start' { Start-TaskNow }
    'stop' { Stop-TaskNow }
    'status' { Status-Task }
}
