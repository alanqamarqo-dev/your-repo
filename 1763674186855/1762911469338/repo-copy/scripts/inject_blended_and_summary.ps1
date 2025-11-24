# scripts/inject_blended_and_summary.ps1
param()

Write-Host "Injecting Blended badge into HTML reports and generating ensemble summary..."

$badge = @'
<div style="position:sticky;top:0;z-index:9999;font-family:ui-sans-serif,system-ui,-apple-system;
background:linear-gradient(90deg,#0ea5e9,#8b5cf6);color:white;padding:10px 14px;margin:0 0 12px 0;
box-shadow:0 2px 10px rgba(0,0,0,.15);border-bottom-left-radius:10px;border-bottom-right-radius:10px">
  <strong>Meta-Ensembler</strong> — <span style="opacity:.9">Blended results enabled</span>
</div>
'@

# 1) Inject badge into all HTML under reports
$targets = @(Get-ChildItem -Path reports -Recurse -Filter *.html -File | Select-Object -ExpandProperty FullName)
foreach ($f in $targets) {
    $t = Get-Content $f -Raw -Encoding UTF8
    if ($t -notmatch 'Meta-Ensembler') {
        $t = $t -replace '<body([^>]*)>', '<body$1>' + [System.Environment]::NewLine + $badge
        Set-Content -Encoding utf8 -Path $f -Value $t
    }
}
Write-Host "✅ Injected 'Blended' badge into $($targets.Count) HTML files."

# 2) Generate ensemble_summary.html from self_optimization + config/fusion_weights.json
$soPath = 'reports\self_optimization\self_optimization.json'
$fwPath = 'config\fusion_weights.json'
if (-not (Test-Path $soPath)) {
    Write-Warning "Self-optimization JSON not found at $soPath — skipping ensemble summary generation"
}
else {
    $so = Get-Content $soPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $fw = @{}
    if (Test-Path $fwPath) { $fw = Get-Content $fwPath -Raw -Encoding UTF8 | ConvertFrom-Json }

    $rowsList = @()
    foreach ($entry in $so.model_signals.GetEnumerator()) {
        $name = $entry.Key
        $rmse = [math]::Round($entry.Value.rmse, 6)
        $conf = [math]::Round($entry.Value.confidence, 3)
        $rowsList += ('<tr><td style="padding:.5rem .75rem;border-bottom:1px solid #eee">' + $name + '</td><td style="padding:.5rem .75rem;border-bottom:1px solid #eee">' + $rmse + '</td><td style="padding:.5rem .75rem;border-bottom:1px solid #eee">' + $conf + '</td></tr>')
    }
    $rows = $rowsList -join "`n"

    $wList = @()
    if ($fw) {
        foreach ($p in $fw.PSObject.Properties) {
            $wList += ('<li><code>' + $p.Name + '</code>: <b>' + $p.Value + '</b></li>')
        }
    }
    $w = $wList -join "`n"

    $htmlLines = @()
    $htmlLines += '<!doctype html>'
    $htmlLines += '<html lang="ar" dir="rtl">'
    $htmlLines += '<head>'
    $htmlLines += '<meta charset="utf-8"/>'
    $htmlLines += '<title>AGL — ملخّص المزج (Meta-Ensembler)</title>'
    $htmlLines += '<meta name="viewport" content="width=device-width, initial-scale=1"/>'
    $htmlLines += '<style>'
    $htmlLines += 'body{font-family:ui-sans-serif,system-ui,-apple-system;background:#0b1220;color:#e5e7eb;margin:0;padding:24px}'
    $htmlLines += '.card{background:rgba(255,255,255,.05);backdrop-filter:blur(6px);border:1px solid rgba(255,255,255,.09);border-radius:14px;padding:16px;margin:12px 0}'
    $htmlLines += 'h1{margin:.2rem 0 1rem 0} h2{margin:.5rem 0}'
    $htmlLines += 'table{width:100%;border-collapse:collapse;background:rgba(255,255,255,.02);border-radius:12px;overflow:hidden}'
    $htmlLines += 'a{color:#7dd3fc}'
    $htmlLines += '.badge{display:inline-block;background:linear-gradient(90deg,#0ea5e9,#8b5cf6);color:#fff;padding:.35rem .6rem;border-radius:999px;font-size:.85rem}'
    $htmlLines += '</style>'
    $htmlLines += '</head>'
    $htmlLines += '<body>'
    $htmlLines += '<div class="badge">Meta-Ensembler — Blended</div>'
    $htmlLines += '<h1>ملخّص المزج (Meta-Ensembler)</h1>'
    $htmlLines += '<div class="card">'
    $htmlLines += '  <h2>أوزان القنوات (Fusion Weights)</h2>'
    $htmlLines += '  <ul>'
    $htmlLines += $w
    $htmlLines += '  </ul>'
    $htmlLines += '</div>'
    $htmlLines += '<div class="card">'
    $htmlLines += '  <h2>إشارات النماذج (Self-Optimization)</h2>'
    $htmlLines += '  <table>'
    $htmlLines += '    <thead>'
    $htmlLines += '      <tr><th style="text-align:right;padding:.5rem .75rem;border-bottom:1px solid #eee">النموذج</th>'
    $htmlLines += '          <th style="text-align:right;padding:.5rem .75rem;border-bottom:1px solid #eee">RMSE</th>'
    $htmlLines += '          <th style="text-align:right;padding:.5rem .75rem;border-bottom:1px solid #eee">Confidence</th></tr>'
    $htmlLines += '    </thead>'
    $htmlLines += '    <tbody>'
    $htmlLines += $rows
    $htmlLines += '    </tbody>'
    $htmlLines += '  </table>'
    $htmlLines += '  <p style="opacity:.85;margin-top:.75rem">البيانات مأخوذة من reports/self_optimization/self_optimization.json</p>'
    $htmlLines += '</div>'
    $htmlLines += '<div class="card">'
    $htmlLines += '  <h2>روابط سريعة</h2>'
    $htmlLines += '  <p><a href="models_report.html">models_report.html</a> — <a href="models_visual.html">models_visual.html</a> — <a href="safety_suite/safety_report.html">safety report</a></p>'
    $htmlLines += '</div>'
    $htmlLines += '</body>'
    $htmlLines += '</html>'

    New-Item -ItemType Directory -Force -Path reports | Out-Null
    $mix = $htmlLines -join "`n"
    Set-Content -Encoding utf8 -Path reports\ensemble_summary.html -Value $mix
    Write-Host "✅ wrote reports\ensemble_summary.html"
}

# 3) Update manifest
$mfPath = "reports\report_manifest.json"
if (Test-Path $mfPath) {
    $m = Get-Content $mfPath -Raw -Encoding UTF8 | ConvertFrom-Json
}
else {
    $m = [pscustomobject]@{ html = @(); json = @() }
}
if (-not ($m.html -contains "ensemble_summary.html")) {
    $m.html = , "ensemble_summary.html" + $m.html
}
$m | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 $mfPath
Write-Host "✅ manifest updated → reports\report_manifest.json"

# 4) Commit changes
git add reports\ reports\report_manifest.json config\fusion_weights.json 2>$null
try { git commit -m "UX: Inject Blended badge + add ensemble_summary.html (Meta-Ensembler)" } catch { Write-Host "No changes to commit or git not configured." }
Write-Host "Done."
