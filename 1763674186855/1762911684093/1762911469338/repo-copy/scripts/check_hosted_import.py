import importlib, traceback

try:
    m = importlib.import_module("Core_Engines.Hosted_LLM")
    print("Loaded module:", m.__name__)
    print("Has QwenHostedLLM:", hasattr(m, "QwenHostedLLM"))
    print("Has PipelineHostedLLM:", hasattr(m, "PipelineHostedLLM"))
except Exception as e:
    print("Import failed:", e)
    traceback.print_exc()
