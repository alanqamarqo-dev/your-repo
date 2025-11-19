Param(
    [string]$Model = "qwen2.5:7b-instruct",
    [string]$BaseUrl = "http://127.0.0.1:11434",
    [int]$ServerPort = 8000
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $repo '..')

# --- 1) بيئة التشغيل (لا تمسح الـregistry) ---
$env:AGL_FEATURE_ENABLE_RAG = '1'
$env:AGL_LLM_PROVIDER = 'ollama-http'
$env:AGL_LLM_BASEURL = $BaseUrl
$env:AGL_LLM_MODEL = $Model
# Recommended test-mode settings for hybrid reasoning and quantum simulation
$env:AGL_REASONER_MODE = 'hybrid'
$env:AGL_ANALYSIS_AUTO_PROMPT = '1'
$env:AGL_QUANTUM_MODE = 'simulate'
# LLM generation stability (low temperature) for evaluation runs
$env:AGL_LLM_TEMPERATURE = '0.05'
$env:AGL_LLM_TOP_P = '0.2'
$env:AGL_LLM_NUM_PREDICT = '900'
# اختياري: فعّل لوج RAG
# $env:AGL_RAG_DEBUG='1'

# --- 2) تأكد أن Ollama شغال والموديل موجود ---
try { Get-Process ollama -ErrorAction Stop | Out-Null } catch {
    Write-Host "[INFO] starting 'ollama serve'..." -ForegroundColor Cyan
    Start-Process -WindowStyle Minimized -FilePath "ollama" -ArgumentList "serve"
    Start-Sleep -Seconds 3
}

try {
    $models = ollama list 2>$null
}
catch {
    $models = ""
}

if ($models -notmatch [regex]::Escape($Model)) {
    Write-Host "[INFO] pulling model $Model ..." -ForegroundColor Cyan
    ollama pull $Model
}

# --- 3) تهيئة بايثون والتأكد من المتطلبات الأساسية ---
py -3 -c "import sys; print(sys.version)"
# (اختياري) ثبّت متطلباتك إن لزم:
# py -3 -m pip install -r requirements.txt

# --- 4) فحص bootstrap سريع (بدون مسح registry) ---
py -3 -c "import Core_Engines as engines; from Integration_Layer.integration_registry import registry; engines.bootstrap_register_all_engines(registry, allow_optional=True); print(sorted(registry.list_names()))"

# --- 5) شغّل السيرفر (FastAPI) إن لم يكن يعمل ---
$portUsed = (Test-NetConnection -ComputerName 127.0.0.1 -Port $ServerPort).TcpTestSucceeded
if (-not $portUsed) {
    Write-Host "[INFO] starting server.py on :$ServerPort ..." -ForegroundColor Green
    Start-Process -WindowStyle Minimized -FilePath "py.exe" -ArgumentList "-3", "-m", "server"
    Start-Sleep -Seconds 2
}

# --- 6) شغّل الـ Daemon (جدولة ذاتية داخل بايثون) ---
Write-Host "[INFO] starting AGL daemon (auto-cycles) ..." -ForegroundColor Green
Start-Process -WindowStyle Minimized -FilePath "py.exe" -ArgumentList "-3", "-m", "scripts.agl_daemon"
Write-Host "[READY] AGL is up. Health: http://127.0.0.1:$ServerPort/api/system/status" -ForegroundColor Yellow
