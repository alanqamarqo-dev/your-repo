# Start background jobs: Harvester and Cron (calibrate/reports)
param()

$Root = 'D:\AGL'
$PyExe = Join-Path $Root '.venv\Scripts\python.exe'
$Logs = Join-Path $Root 'artifacts\logs'
if (-not (Test-Path $Logs)) { New-Item -ItemType Directory -Force -Path $Logs | Out-Null }

# Harvester job
if (-not (Get-Job -Name 'AGL_Harvester' -ErrorAction SilentlyContinue)) {
    Start-Job -Name AGL_Harvester -ScriptBlock {
        param($Root,$PyExe,$LogFile,$Interval)
        Set-Location $Root
        $env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
        while ($true) {
            try {
                & $PyExe "workers\knowledge_harvester.py" | Out-File -FilePath $LogFile -Append -Encoding utf8
            } catch {
                "HARVESTER_ERROR: $($_)" | Out-File -FilePath $LogFile -Append -Encoding utf8
            }
            Start-Sleep -Seconds $Interval
        }
    } -ArgumentList $Root,$PyExe,(Join-Path $Logs 'harvester.log'),300 | Out-Null
    Write-Output "Started job AGL_Harvester"
} else { Write-Output "AGL_Harvester already exists" }

# Cron job (simple periodic tasks)
if (-not (Get-Job -Name 'AGL_Cron' -ErrorAction SilentlyContinue)) {
    Start-Job -Name AGL_Cron -ScriptBlock {
        param($Root,$PyExe,$LogFile,$CalMin,$RepMin,$SnapMin)
        Set-Location $Root
        $env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
        $t0 = Get-Date
        while ($true) {
            $now = Get-Date
            if ( ($now - $t0).TotalMinutes -ge $CalMin ) {
                try { & $PyExe "scripts\calibrate_fusion_weights.py" | Out-File -FilePath $LogFile -Append -Encoding utf8 } catch {}
                $t0 = Get-Date
            }
            if ($RepMin -and ((Get-Random -Minimum 0 -Maximum 100) -lt 15)) {
                try { & $PyExe "scripts\generate_all_reports.py" | Out-File -FilePath $LogFile -Append -Encoding utf8 } catch {}
                try { & $PyExe "scripts\generate_system_report.py" | Out-File -FilePath $LogFile -Append -Encoding utf8 } catch {}
            }
            if ($SnapMin -and ((Get-Random -Minimum 0 -Maximum 100) -lt 10)) {
                try { & $PyExe "scripts\save_rc_to_kb.py" | Out-File -FilePath $LogFile -Append -Encoding utf8 } catch {}
            }
            Start-Sleep -Seconds 60
        }
    } -ArgumentList $Root,$PyExe,(Join-Path $Logs 'cron.log'),45,60,180 | Out-Null
    Write-Output "Started job AGL_Cron"
} else { Write-Output "AGL_Cron already exists" }
