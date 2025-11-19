# your-repo

## Quick CI (Local)

**Prereqs:** Python 3.13 + venv

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -U pip setuptools wheel pytest
$env:PYTHONPATH='D:\AGL\repo-copy'
$env:AGL_TEST_SCAFFOLD_FORCE='1'
$env:AGL_LLM_PROVIDER='offline'
$env:MPLBACKEND='Agg'
Remove-Item Env:AGL_SUT -ErrorAction SilentlyContinue
D:\AGL\.venv\Scripts\python.exe -m pytest -q -r a
```

Markers:

-m smoke لتجارب سريعة.

-m integration لتشغيل تكامل بدون مزوّد خارجي (يستخدم mock RAG).

### `pytest.ini`

```ini
[pytest]
markers =
 smoke: smoke tests
 integration: integration tests
```
