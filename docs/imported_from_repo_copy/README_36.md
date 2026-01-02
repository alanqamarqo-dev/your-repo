# AGL – Advanced General Law/Logic Learner

[![CI](https://github.com/<user>/<repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/<user>/<repo>/actions/workflows/ci.yml)

AGL: منصة تعلم/تحقق/توليد قوانين ومعادلات مع طبقات أمان وتكامل واجهة رسومية.

Quickstart
---------

1. Create venv and install deps:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install -r requirements.txt
```

2. Run tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v tests
```

3. Run Law Studio UI (example):

```powershell
python AGL_UI/main.py
```

Quick Start — Train demo
------------------------

This section shows how to run the small training demo (Hooke's law) from the repository root.

1. Ensure your virtualenv is active and dependencies are installed:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install -r requirements.txt
```

2. Run the training demo (uses the included sample CSV):

```powershell
D:\AGL\.venv\Scripts\python.exe .\AGL.py --task "train-laws" --data "data\hooke_sample.csv"
```

3. The run will write a report to `reports/last_run.json` and the learned artifact to `Knowledge_Base/Learned_Patterns.json`.

4. For an interactive dev helper, run the PowerShell helper script:

```powershell
.\scripts\dev.ps1
```

Packaging & Release
-------------------

To create a release (commit, tag and push):

```bash
./release.sh
```

To build a wheel and sdist locally:

```powershell
pip install build
python -m build
# artifacts appear under dist/ (wheel + sdist)
```

Continuous Integration (GitHub Actions)
-------------------------------------

CI workflow (added at `.github/workflows/ci.yml`) will:

- pip install -r requirements.txt
- run unit tests
- generate `reports/full_report.html` by aggregating `reports/auto_reports` and upload it as an artifact
- (optional) run coverage and upload `htmlcov` as an artifact

CLI examples

Train phase D candidate models and write a results artifact:

Runtime Feature Flags

- `AGL_SELF_LEARNING_ENABLE=1`  
    يفعّل جولة تعلّم ذاتي تلقائيًا بعد الاختبارات/الرنر.

- `AGL_SELF_LEARNING_LOGDIR=artifacts\learning_runs\<run_id>`  
    مسار `events.jsonl` لأحداث التعلّم.

- `AGL_SELF_LEARNING_ETA=0.3`  
    معدل التحديث (moving-average).

- `AGL_COGNITIVE_INTEGRATION=1`  
    يفعّل تكامل المحرّكات (Stage-2).

- `AGL_COLLECTIVE_INTELLIGENCE=1`  
    يفعّل السمفونية المعرفية (Stage-3). **عطّل في CI**:
  - في CI استخدم `AGL_COLLECTIVE_INTELLIGENCE=0`
  - السبب: يعتمد على اكتشاف محرّكات/مسارات قد لا تتوفّر في بيئة CI.

- `AGL_HOOKS_ENABLE=1`  
    يفعّل ربط الـ hooks (router-first).

#### تشغيل محلي سريع (PowerShell)

```powershell
pushd d:\AGL\repo-copy
$env:PYTHONPATH=(Resolve-Path .).Path
$env:AGL_SELF_LEARNING_ENABLE='1'
$env:AGL_SELF_LEARNING_LOGDIR='artifacts\learning_runs\alpha065_run01'
$env:AGL_SELF_LEARNING_ETA='0.3'
$env:AGL_ENGINES='planner,deliberation,emotion,associative,retriever,self_learning'
$env:AGL_COGNITIVE_INTEGRATION='1'
$env:AGL_COLLECTIVE_INTELLIGENCE='1'
$env:AGL_HOOKS_ENABLE='1'
$env:AGL_TEST_SCAFFOLD_FORCE='0'
& '.\.venv\Scripts\python.exe' .\tests\agi_test_runner.py
popd
```

```powershell
python -m scripts.train_phaseD --data data/phaseD/poly2_iv.csv --x I --y V --candidates poly2 "a*x**2" "k*x" "k*x + b" --out artifacts/models/poly2_D
```

Generate all HTML reports from the current KB:

```powershell
python scripts/generate_all_reports.py
```

Registry canonical names (short)
--------------------------------

The IntegrationRegistry exposes canonical service names that callers/tests should rely on.

Core services:

- `communication_bus`
- `task_orchestrator`
- `domain_router`
- `planner_agent`
- `output_formatter`

Retrieval / RAG:

- `retriever` (must provide `retrieve(query) -> list`)
- `rag` (module/object with `answer` or `answer_with_rag` returning a dict `{'answer':..., 'sources':[...]}`)

Learning / Self-Improvement:

- `experience_memory`
- `self_learning`
- `model_zoo` (fallback provided if heavy models missing)
- `feedback_analyzer`, `improvement_generator`, `knowledge_integrator`

Meta-cognition:

- `meta_cognition` (provides `evaluate(plan) -> {'score': float, 'notes': str}`)

Safety:

- `control_layers`, `rollback_mechanism`, `emergency_protocols`,
  optional: `emergency_doctor`, `emergency_integration`

Note: each service has a lightweight fallback registered when the heavyweight implementation
or runtime dependency is missing. This allows the system to bootstrap and smoke-test without
installing the full ML stack.

SelfModel, ReflectiveCortex and PerceptionLoop docs
--------------------------------------------------

See the developer-focused notes about the self-model and reflection components in
`docs/selfmodel.md`. The doc explains the new opt-in hooks, environment flags, where to
find the code, and how to run the bridge/embeddings tests locally or in CI.

## CI & Autoruns

- Autoruns are **gated** by env flags. In CI keep them **off**:
  - `AGL_COGNITIVE_INTEGRATION=0`
  - `AGL_COLLECTIVE_INTELLIGENCE=0`
  - `AGL_GENERATIVE_CREATIVITY=0`
- Dynamic engine overrides:
  - `AGL_ENGINE_IMPLS` accepts JSON or `name=module:Class` pairs.
  - External adapters must implement `.name`, `.domains`, and `infer(...)`.
- Governance/tuning:
  - `AGL_ENGINE_ORDER`, `AGL_ENGINE_MAX`
  - `AGL_TIE_EPS`, `AGL_TIE_DIVERSITY_BONUS`
