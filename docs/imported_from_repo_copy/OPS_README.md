
AGL Operational Quick Run

# AGL Operational Quick Run

This folder contains short operational scripts to run a full pipeline: data refinement, retraining, KB promotion, report generation, safety checks and PDF export.

## PowerShell (Windows)

Run as administrator or regular user from repo root.

```powershell
# Quick run (make sure virtualenv is active or use full path to python)
powershell -ExecutionPolicy Bypass -File scripts\ops_full_run.ps1
```

## Bash (Linux/macOS)

```bash
chmod +x scripts/ops_full_run.sh
./scripts/ops_full_run.sh
```

### Notes

- Set `PYTHONIOENCODING=utf-8` to avoid terminal encoding issues.
- `tools/normalize_kb.py` should only be run if KB JSON is corrupted or you explicitly want to canonicalize the KB.
- The script uses headless Chrome to export PDF; ensure Chrome is installed and on the expected path.
- The scripts provide commented lines for optional promotion of refined artifacts.
Notes
