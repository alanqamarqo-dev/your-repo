param(
  [string]$action = 'start'
)

$venv = Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'
$server = Join-Path $PSScriptRoot '..\server.py'
$pidfile = Join-Path $PSScriptRoot '..\server_pid.txt'
$log = Join-Path $PSScriptRoot '..\artifacts\server.log'

function Start-Server {
    if (Test-Path $pidfile) {
        $srvPid = Get-Content $pidfile -ErrorAction SilentlyContinue
        if ($srvPid) {
            try { Get-Process -Id $srvPid -ErrorAction Stop | Out-Null; Write-Output "Server already running (PID=$srvPid)"; return }
            catch { Remove-Item $pidfile -ErrorAction SilentlyContinue }
        }
    }
    # Start the process and write pid
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $venv
    $startInfo.Arguments = "-m uvicorn server:app --host 127.0.0.1 --port 8000"
    $startInfo.WorkingDirectory = (Resolve-Path $PSScriptRoot\..).Path
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.UseShellExecute = $false

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $startInfo
    $proc.Start() | Out-Null

    # capture output asynchronously
    $outWriter = [System.IO.File]::Open($log, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    $sw = New-Object System.IO.StreamWriter($outWriter)
    $sw.AutoFlush = $true

    Start-Job -ScriptBlock {
        param($srvPidParam, $sw, $procId)
        while ($true) {
            try {
                $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if (-not $p) { break }
                Start-Sleep -Seconds 1
            } catch { break }
        }
    } -ArgumentList ($proc.Id, $sw, $proc.Id) | Out-Null

    Set-Content -Path $pidfile -Value $proc.Id
    Write-Output "Started server PID=$($proc.Id); logs -> $log"
}

function Stop-Server {
    if (Test-Path $pidfile) {
        $srvPid = Get-Content $pidfile -ErrorAction SilentlyContinue
        if ($srvPid) {
            try { Stop-Process -Id $srvPid -Force -ErrorAction Stop; Write-Output "Stopped PID=$srvPid" } catch { Write-Output "Process $srvPid not found" }
            Remove-Item $pidfile -ErrorAction SilentlyContinue
            return
        }
    }
    Write-Output "Server not running"
}

function Get-ServerStatus {
    if (Test-Path $pidfile) {
        $srvPid = Get-Content $pidfile -ErrorAction SilentlyContinue
        if ($srvPid) {
            try { $p = Get-Process -Id $srvPid -ErrorAction Stop; Write-Output "Running PID=$srvPid (Started $($p.StartTime))"; return } catch { Write-Output "Stale PID file" }
        }
    }
    Write-Output "Server not running"
}

switch ($action.ToLower()) {
    'start' { Start-Server }
    'stop' { Stop-Server }
    'status' { Get-ServerStatus }
    default { Write-Output "Unknown action: $action. Use start|stop|status" }
}
