# Strategic Planner automation — quick guide

This file documents how to run the enhanced strategic planner (standalone and as part of the full automation flow).

Files of interest
- `scripts/strategic_advanced_planner.py` — Python harness that calls `Core_Engines.Strategic_Thinking` and optionally `Core_Engines.External_InfoProvider`. Produces a JSON report in `artifacts/reports/`.
- `scripts/run_strategic_planner.ps1` — PowerShell wrapper to run the planner with convenient flags (stakeholders file, Monte Carlo iterations, mock/live RAG).
- `run_all.ps1` — top-level automation; now calls `scripts/run_strategic_planner.ps1` as part of the full workflow.
- `configs/sample_stakeholders.json` — example stakeholders weights file used for MCDA aggregation.

Environment and prerequisites
- Windows PowerShell (pwsh) or powershell.exe (the repository was developed on Windows).
- A Python virtual environment `.venv` with project dependencies installed (the `run_all.ps1` script will attempt to create/install if missing).

RAG (ExternalInfoProvider) modes
- Mock (recommended for CI/local testing): set the environment variable `AGL_EXTERNAL_INFO_MOCK=1` (or run the PS wrapper with `-UseMock`) — provider returns deterministic mock facts and will not require an API key.
- Live: set `OPENAI_API_KEY` in the session to a valid ASCII OpenAI key (e.g. PowerShell: `$env:OPENAI_API_KEY='sk-...'`). The provider will call the OpenAI client and fetch real facts; ensure network access and `openai` package availability.

How to run (examples)
- Standalone (mock RAG, 500 MC iterations, using sample stakeholders):
```powershell
$env:AGL_EXTERNAL_INFO_MOCK='1'
pwsh -ExecutionPolicy Bypass -File .\scripts\run_strategic_planner.ps1 -UseMock -Stakeholders configs/sample_stakeholders.json -MCIterations 500 -UseRag
```

- Standalone (live RAG — requires OPENAI_API_KEY):
```powershell
$env:OPENAI_API_KEY='sk-...'
pwsh -ExecutionPolicy Bypass -File .\scripts\run_strategic_planner.ps1 -Stakeholders configs/sample_stakeholders.json -MCIterations 100 -UseRag
```

- As part of full automation flow (invoked by `run_all.ps1`):
```powershell
# Dry run to see steps without executing long-running ops
pwsh -ExecutionPolicy Bypass -File .\run_all.ps1 -DryRun

# Full run (will run the strategic planner with defaults defined in run_all.ps1)
pwsh -ExecutionPolicy Bypass -File .\run_all.ps1
```

Notes & troubleshooting
- `run_all.ps1` performs an integration-test cohesion check before starting long-running ops; if your integration tests are missing or failing the runner may exit early with a non-zero code. Use `-DryRun` to inspect steps.
- If live RAG fails with `OPENAI_API_KEY` errors, verify the key is ASCII and starts with `sk-`.
- Generated reports are placed in `artifacts/reports/` with timestamped filenames. The PowerShell wrapper prints the invocation arguments and the Python script prints the written path.

If you want, I can:
- Make the PS wrapper print the exact generated report path (parse and return it),
- Add CI job snippets (GitHub Actions) to run the planner in mock mode nightly,
- Add an optional CSV exporter for `mitigation_struct` to integrate with issue trackers.

