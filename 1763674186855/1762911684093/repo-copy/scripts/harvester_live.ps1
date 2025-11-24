# Live harvester loop: fetch external facts repeatedly and append to a live log
$env:AGL_EXTERNAL_INFO_ENABLED='1'
$env:AGL_EXTERNAL_INFO_MOCK=''

$log = Join-Path $PSScriptRoot '..\artifacts\harvester_live.log'
if (-not (Test-Path (Split-Path $log))) { New-Item -ItemType Directory (Split-Path $log) -Force | Out-Null }

while ($true) {
    try {
        py workers\knowledge_harvester.py 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
    } catch {
        $_ | Out-File -FilePath $log -Append -Encoding utf8
    }
    Start-Sleep -Seconds 30
}
