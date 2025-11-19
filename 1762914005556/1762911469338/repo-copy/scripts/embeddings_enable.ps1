param(
    [string]$VenvName = ".venv_embed",
    [string]$ArtifactsDir = "data",
    [string]$Alpha = "0.60",
    [switch]$GPU
)

$ErrorActionPreference = "Stop"
function Log($m) { Write-Host "[EMB]" $m }

# تحضير venv
if (-not (Test-Path $VenvName)) { python -m venv $VenvName }
& ".\$VenvName\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools

# اختيار باكTorch
if ($GPU) {
    Log "GPU mode requested: رجاء تأكد من CUDA/cuDNN مُثبتَين."
    & ".\$VenvName\Scripts\python.exe" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
}
else {
    & ".\$VenvName\Scripts\python.exe" -m pip install torch --index-url https://download.pytorch.org/whl/cpu
}

# حزم الـ embeddings
& ".\$VenvName\Scripts\python.exe" -m pip install -r requirements-embeddings.txt

# إعداد بيئة التشغيل
$repo = (Resolve-Path .).Path
$art = Join-Path $repo $ArtifactsDir
if (-not (Test-Path $art)) { New-Item -Type Directory $art | Out-Null }

$env:PYTHONPATH = $repo
$env:AGL_ARTIFACTS_DIR = $art
$env:AGL_EMBEDDINGS_ENABLE = "1"
$env:AGL_RETRIEVER_BLEND_ALPHA = $Alpha
$env:PYTHONIOENCODING = "utf-8"

Log "Reindex (clean) with embeddings ON"
& ".\$VenvName\Scripts\python.exe" "scripts/run_clean_reindex.py"

Log "Quick smoke of semantic search (optional)"
if (Test-Path "scripts/test_search_quality.py") {
    & ".\$VenvName\Scripts\python.exe" "scripts/test_search_quality.py" | Tee-Object -FilePath (Join-Path $art "semantic_quality_stdout.txt")
}
else {
    Log "scripts/test_search_quality.py غير موجود — سأتجاوز الاختبار."
}

Log "Done. Env vars summary:" 
"AGL_EMBEDDINGS_ENABLE=$env:AGL_EMBEDDINGS_ENABLE"
"AGL_RETRIEVER_BLEND_ALPHA=$env:AGL_RETRIEVER_BLEND_ALPHA"
"AGL_ARTIFACTS_DIR=$env:AGL_ARTIFACTS_DIR"
