External Info Provider

This project includes an optional External Info Provider (facts-only) used by `General_Knowledge` when no local evidence is found.

Configuration (configs/agl_config.json)

external_info_provider:
  enabled: true|false    # when true, GK may call the external provider
  model: gpt-4o-mini     # default model to call
  daily_limit: 200       # per-day request limit
  cache_dir: artifacts/external_info_cache

Environment variable overrides (take precedence):

AGL_EXTERNAL_INFO_ENABLED=1
AGL_EXTERNAL_INFO_IMPL=ollama_engine
AGL_EXTERNAL_INFO_MODEL=qwen2.5:7b-instruct
AGL_EXTERNAL_INFO_DAILY_LIMIT=200
AGL_EXTERNAL_INFO_CACHE_DIR=artifacts/external_info_cache
OPENAI_API_KEY=sk-...

Quick test (PowerShell)

Set env vars then run server and send a probe:

$env:OPENAI_API_KEY = 'sk-...'
$env:AGL_EXTERNAL_INFO_ENABLED = '1'
$env:AGL_EXTERNAL_INFO_MODEL = 'gpt-4o-mini'
$env:AGL_EXTERNAL_INFO_DAILY_LIMIT = '200'
$env:AGL_EXTERNAL_INFO_CACHE_DIR = 'artifacts/external_info_cache'

# Run server (adjust path to your venv/python)
$env:PYTHONPATH=(Get-Location).Path
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000

# Then probe (example):
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat `
  -Method POST `
  -ContentType 'application/json' `
  -Body (@{ session_id='ext_probe_1'; text='ما الفرق بين الاندماج النووي والانشطار النووي؟' } | ConvertTo-Json) `
| ConvertTo-Json -Depth 10

# Check admin status:
Invoke-RestMethod -Uri http://127.0.0.1:8000/admin/external-info
