#!/usr/bin/env python3
"""
Hot patch: upgrade referenced engine names in mission_control_enhanced
- Makes a backup of the original file
- Replaces a small set of common names to their preferred advanced names
- Injects an import fallback for `get_preferred_engine` (defensive)

Use: python activate_super_engines.py
"""
import shutil
import os
from pathlib import Path

TARGET = Path("dynamic_modules/mission_control_enhanced.py")
BACKUP = TARGET.with_suffix(".py.bak")

REPLACEMENTS = {
    "'QuantumCore'": "'AdvancedQuantumEngine'",
    "'CreativeInnovation'": "'CreativeInnovationEngine'",
    "'StrategicThinking'": "'AdvancedMetaReasonerEngine'",
    "'CodeGenerator'": "'AdvancedCodeGenerator'",
    "'SimulationEngine'": "'IntegratedSimulationEngine'",
}

IMPORT_LINE = "from config.engine_preference import get_preferred_engine"

if not TARGET.exists():
    print(f"❌ Target file not found: {TARGET}")
    raise SystemExit(1)

print(f"🔌 Backing up {TARGET} -> {BACKUP}")
shutil.copy2(TARGET, BACKUP)

text = TARGET.read_text(encoding='utf-8')

# Inject defensive import near other imports (after 'import sys' if present)
if IMPORT_LINE not in text:
    if "import sys" in text:
        text = text.replace(
            "import sys",
            "import sys\ntry:\n    from config.engine_preference import get_preferred_engine\nexcept Exception:\n    # fallback: identity mapper if config missing\n    def get_preferred_engine(x):\n        return x\n",
        )
        print("✅ Injected defensive import for get_preferred_engine")
    else:
        # Prepend import at top
        text = IMPORT_LINE + "\n" + text
        print("✅ Prepended import for get_preferred_engine")

# Apply replacements (hot-swap names in cluster definitions)
changed = False
for old, new in REPLACEMENTS.items():
    if old in text:
        text = text.replace(old, new)
        print(f"✅ Replaced {old} -> {new}")
        changed = True

# As an extra safety: replace common bare tokens in cluster lists (without quotes)
# only if simple pattern matches to reduce accidental replacements
for plain_old, plain_new in [("QuantumCore", "AdvancedQuantumEngine"), ("CreativeInnovation", "CreativeInnovationEngine")]:
    text = text.replace(plain_old, plain_new)

if changed:
    TARGET.write_text(text, encoding='utf-8')
    print("🚀 Hot-patch applied and file updated.")
    print(f"   Backup saved at: {BACKUP}")
else:
    print("ℹ️ No direct matches found; no changes applied.")
    print(f"   Backup is still available at: {BACKUP}")

print("🔎 Done. You may restart the server or run a local execute_mission test.")
