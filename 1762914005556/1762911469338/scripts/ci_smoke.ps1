#!/usr/bin/env pwsh
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

# ضمان تشغيل من جذر المستودع
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location .. | Out-Null

# بيئة هادئة وثابتة
$env:MPLBACKEND = "Agg"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:AGL_TEST_SKIP_MATPLOTLIB = "1"   # تخطّي اختبارات الرسم افتراضياً
$env:AGL_EXTERNAL_INFO_MOCK = "1"   # لا شبكات في CI
$env:AGL_LLM_PROVIDER = "ollama"
$env:AGL_LLM_BASEURL = "http://localhost:11434"  # أو اتركه كما هو إن لم يُستخدم فعلياً
# تفعيل الشيمات/الدُمّي إن لزم
$env:AGL_TEST_SCAFFOLD_FORCE = "1"

# تنظيف مخلفات تقارير قديمة
if (Test-Path ".pytest_cache") { Remove-Item ".pytest_cache" -Recurse -Force }
if (Test-Path "reports\self_optimization") { Remove-Item "reports\self_optimization" -Recurse -Force }

# اختيار مجموعة دخّانية سريعة
$pytestArgs = @(
    "-q",
    "-k", "smoke or quick or basic"
)

Write-Host "Running smoke tests: pytest $($pytestArgs -join ' ')" -ForegroundColor Cyan
$py = (Get-Command py -ErrorAction SilentlyContinue)
if ($null -ne $py) {
    py -3 -m pip install -U pip setuptools wheel pytest
    py -3 -m pytest @pytestArgs
}
else {
    python -m pip install -U pip setuptools wheel pytest
    python -m pytest @pytestArgs
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Smoke tests failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Smoke tests succeeded." -ForegroundColor Green
exit 0
