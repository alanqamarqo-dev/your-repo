# Using the local Ollama model in this repo

This project can call a locally installed Ollama model (the `ollama` CLI) via the `Core_Engines.Ollama_Adapter`.

Quick steps to run a live example (PowerShell):

1. Ensure `ollama` is installed and the model is pulled locally, e.g.:

```powershell
& 'C:\Users\<you>\AppData\Local\Programs\Ollama\ollama.exe' pull qwen2.5:7b-instruct
ollama ls
```

2. Run the example script (from repo root):

```powershell
$env:PYTHONPATH='D:\AGL'
$env:AGL_OLLAMA_KB_CACHE_ENABLE='0'
$env:AGL_EXTERNAL_INFO_MODEL='qwen2.5:7b-instruct'
py -3 tools\ollama_example.py "ما هو قانون نيوتن الثاني؟"
```

3. To make the project use Ollama as the default ExternalInfoProvider set the environment variable:

```powershell
$env:AGL_EXTERNAL_INFO_IMPL='ollama_engine'
$env:AGL_EXTERNAL_INFO_MODEL='qwen2.5:7b-instruct'
```

Notes
- The repository now ships an `Ollama_Adapter` and `Ollama_KnowledgeEngine` which call `ollama run <MODEL> <PROMPT> --format json`.
- Exporting raw model files into the repo is not recommended; keeping the model in Ollama's local registry and invoking it by name is simpler and less error-prone.

If you want me to try exporting the model files into `D:\AGL\models\.ollama`, say so and I'll estimate time/space and attempt a controlled export.
