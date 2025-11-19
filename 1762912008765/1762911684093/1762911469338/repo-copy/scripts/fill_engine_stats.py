"""Call a couple of lightweight engines to populate monitoring stats."""
from Integration_Layer.integration_registry import registry

names = ["General_Knowledge", "NLP_Advanced"]
for name in names:
    eng = None
    try:
        eng = registry.get(name)
    except Exception:
        try:
            eng = registry.resolve(name)
        except Exception:
            eng = None

    if not eng:
        print(name, "NOT FOUND")
        continue

    try:
        if hasattr(eng, 'process_task'):
            out = eng.process_task({"text": "ما عاصمة فرنسا؟"})
            print(name, out)
        else:
            print(name, "NO process_task attribute; type=", type(eng))
    except Exception as e:
        print(name, "ERR:", e)
