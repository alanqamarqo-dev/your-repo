<# ====================  AGL — Full Ops Runner  ====================
   ملف: ops_full_run.ps1
   الهدف: تشغيل خدمة الدردشة + حصاد خفيف بالخلفية + معايرة دورية + تقارير + أرشفة
   الاستخدام:
     pwsh -ExecutionPolicy Bypass -File .\ops_full_run.ps1 -Mode start
     pwsh -ExecutionPolicy Bypass -File .\ops_full_run.ps1 -Mode stop
     pwsh -ExecutionPolicy Bypass -File .\ops_full_run.ps1 -Mode status
#>

param(
  [ValidateSet('start','stop','status')]
  [string]$Mode = 'start',

  # إعدادات عامة
  [string]$Root = 'D:\AGL',
  [string]$PyExe = '',                                       # يُكتشف تلقائياً إن تُرك فارغاً
  [int]$HarvesterIntervalSec = 300,                          # بين كل تشغيل حصاد
  [int]$CalibrationEveryMin = 45,                            # معايرة كل X دقيقة
  [int]$ReportsEveryMin = 60,                                # تقارير كل X دقيقة
  [int]$SnapshotEveryMin = 180,                              # أرشفة كل X دقيقة
  [int]$HarvestTargetPerDomain = 80,                         # هدف الحصاد الخفيف أثناء الخدمة
  [string]$Model = 'gpt-4o-mini'                             # موديل الاستعلام الخارجي
)

# Ensure PowerShell session uses UTF-8 to avoid Arabic garbling in console output/files
try {
  chcp 65001 | Out-Null
  $OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
  # best-effort; continue even if setting encoding fails
}

#------------------------- أدوات مساعدة -------------------------#
function Resolve-Python {
  param([string]$Hint)
  if ($Hint -and (Test-Path $Hint)) { return $Hint }
  $candidates = @(
    Join-Path $Root ".venv\Scripts\python.exe",
    "python.exe",
    "py.exe"
  )
  foreach ($p in $candidates) {
    try { $v = & $p -V 2>$null; if ($LASTEXITCODE -eq 0 -or $v) { return $p } } catch {}
  }
  throw "تعذّر العثور على Python. عيّن -PyExe يدوياً."
}

function New-Log {
  param([string]$Path)
  New-Item -ItemType Directory -Force -Path (Split-Path $Path) | Out-Null
  if (-not (Test-Path $Path)) { New-Item -ItemType File -Path $Path | Out-Null }
}

function New-DirectoryIfMissing([string]$p){ if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }

# مسارات
$Artifacts = Join-Path $Root "artifacts"
$Reports   = Join-Path $Root "reports"
$LogsDir   = Join-Path $Root "logs"
New-DirectoryIfMissing $Artifacts; New-DirectoryIfMissing $Reports; New-DirectoryIfMissing $LogsDir

$LogMain   = Join-Path $LogsDir "ops_main.log"
$LogSrv    = Join-Path $LogsDir "server.log"
$LogHarv   = Join-Path $LogsDir "harvester.log"
$LogCron   = Join-Path $LogsDir "cron.log"
New-Log $LogMain; New-Log $LogSrv; New-Log $LogHarv; New-Log $LogCron

# اكتشاف بايثون
if (-not $PyExe) { $PyExe = Resolve-Python $PyExe }

#-------------------- دوال التشغيل/الإيقاف ---------------------#
function Start-Server {
  param()
  Set-Location $Root
  # متغيرات البيئة للإنتاج
  $env:AGL_EXTERNAL_INFO_ENABLED = '1'
  $env:AGL_EXTERNAL_INFO_MOCK    = ''       # فارغ = حقيقي
  $env:AGL_EXTERNAL_INFO_MODEL   = $Model
  $env:AGL_MEMORY_PERSIST        = '1'
  $env:AGL_AUTO_TUNE             = '0'
  $env:PYTHONUTF8                = '1'
  $env:PYTHONIOENCODING          = 'utf-8'
  # شغّل الخادم (عدّل السكربت إذا كان خادمك مختلف: infer.py/orchestrate.py --serve)
  # تجنّب إنشاء وظيفة مكررة
  if (Get-Job -Name 'AGL_Server' -ErrorAction SilentlyContinue) {
    "Server job already exists; skipping start." | Out-File -FilePath $LogSrv -Append -Encoding utf8
  } else {
    Start-Job -Name AGL_Server -ScriptBlock {
    param($Root,$PyExe,$LogFile)
    Set-Location $Root
    $env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
    try {
      & $PyExe "scripts\infer.py" *>> $LogFile
    } catch {
      "SERVER_ERROR: $($_.Exception.Message)" | Out-File -FilePath $LogFile -Append -Encoding utf8
    }
    } -ArgumentList $Root,$PyExe,$LogSrv | Out-Null
  }
}

function Start-HarvesterLoop {
  param()
  if (Get-Job -Name 'AGL_Harvester' -ErrorAction SilentlyContinue) {
    "Harvester job already exists; skipping start." | Out-File -FilePath $LogHarv -Append -Encoding utf8
  } else {
    Start-Job -Name AGL_Harvester -ScriptBlock {
    param($Root,$PyExe,$Interval,$LogFile,$TargetPerDomain,$Model)
    Set-Location $Root
    $env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
    $env:AGL_EXTERNAL_INFO_ENABLED='1'
    $env:AGL_EXTERNAL_INFO_MOCK=''
    $env:AGL_EXTERNAL_INFO_MODEL=$Model
    $env:AGL_HARVEST_TARGET_PER_DOMAIN=$TargetPerDomain
    while ($true) {
      try { & $PyExe "workers\knowledge_harvester.py" *>> $LogFile } catch {}
      Start-Sleep -Seconds $Interval
    }
    } -ArgumentList $Root,$PyExe,$HarvesterIntervalSec,$LogHarv,$HarvestTargetPerDomain,$Model | Out-Null
  }
}

function Start-CronLoop {
  param()
  if (Get-Job -Name 'AGL_Cron' -ErrorAction SilentlyContinue) {
    "Cron job already exists; skipping start." | Out-File -FilePath $LogCron -Append -Encoding utf8
  } else {
    Start-Job -Name AGL_Cron -ScriptBlock {
    param($Root,$PyExe,$CalMin,$RepMin,$SnapMin,$LogFile)
    Set-Location $Root
    $env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
    $t0 = Get-Date
    while ($true) {
      $now = Get-Date

      # معايرة دورية
      if ( ($now - $t0).TotalMinutes -ge $CalMin ) {
        try { & $PyExe "scripts\calibrate_fusion_weights.py" *>> $LogFile } catch {}
        $t0 = Get-Date  # إعادة ضبط المؤقت للمعايرة
      }

      # تقارير دورية
      if ($RepMin -and ((Get-Random -Minimum 0 -Maximum 100) -lt 15)) {
        try {
          & $PyExe "scripts\generate_all_reports.py" *>> $LogFile
          & $PyExe "scripts\generate_system_report.py" *>> $LogFile
        } catch {}
      }

      # لقطة معرفة (أرشفة) دورية
      if ($SnapMin -and ((Get-Random -Minimum 0 -Maximum 100) -lt 10)) {
        try {
          & $PyExe "scripts\save_rc_to_kb.py" *>> $LogFile
          $zip = Join-Path $Root ("artifacts\kb_snapshot_{0:yyyyMMdd_HHmmss}.zip" -f (Get-Date))
          Compress-Archive -Force -ErrorAction SilentlyContinue `
            -Path "artifacts\protected","artifacts\for_learning","artifacts\harvested_facts.jsonl" `
            -DestinationPath $zip
          "SNAPSHOT: $zip" | Out-File -FilePath $LogFile -Append -Encoding utf8
        } catch {}
      }

      Start-Sleep -Seconds 60
    }
  } -ArgumentList $Root,$PyExe,$CalibrationEveryMin,$ReportsEveryMin,$SnapshotEveryMin,$LogCron | Out-Null
  }
}

function Stop-All {
  Get-Job | Where-Object { $_.Name -like 'AGL_*' } | Remove-Job -Force -ErrorAction SilentlyContinue
}

function Status {
  $jobs = Get-Job | Where-Object { $_.Name -like 'AGL_*' }
  if (-not $jobs) { "لا توجد وظائف قيد التشغيل." ; return }
  $jobs | Select-Object Id,Name,State,HasMoreData | Format-Table -AutoSize
}

#---------------------- تنفيذ بحسب الوضع ----------------------#
switch ($Mode) {
  'start' {
    "==> بدء التشغيل (خادم + حصّاد + كرون) | $(Get-Date)" | Out-File -FilePath $LogMain -Append -Encoding utf8
    Start-Server
    Start-HarvesterLoop
    Start-CronLoop
    "تم الإطلاق. أوامر مفيدة:" | Tee-Object -FilePath $LogMain -Append
    "  • عرض الحالة  :  pwsh -File .\ops_full_run.ps1 -Mode status"
    "  • متابعة لوج   :  Get-Content $LogSrv  -Tail 80 -Wait"
    "                    Get-Content $LogHarv -Tail 80 -Wait"
    "                    Get-Content $LogCron -Tail 80 -Wait"
    "  • الإيقاف      :  pwsh -File .\ops_full_run.ps1 -Mode stop"
  }
  'stop' {
    "==> إيقاف كل الوظائف | $(Get-Date)" | Out-File -FilePath $LogMain -Append -Encoding utf8
    Stop-All
    "تم الإيقاف."
  }
  'status' {
    Status
  }
}

# كيف تستخدمه بسرعة
# 1. احفظ الملف كـ D:\AGL\ops_full_run.ps1 ثم شغّله:
#    pwsh -ExecutionPolicy Bypass -File .\ops_full_run.ps1 -Mode start
