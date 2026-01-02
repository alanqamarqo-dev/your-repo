# AGL — Environment Switches (Defaults are conservative)

| Variable                  | Default | Affects                          | Notes |
|--------------------------|---------|----------------------------------|-------|
| AGL_RETRIEVER_K          | 5       | RAG top-k retrieval              | Larger = more recall, slower |
| AGL_RETRIEVER_BLEND_ALPHA| 0.60    | retriever blending (tfidf+emb)   | 0.0-1.0 blend between TF-IDF and embeddings |
| AGL_EVIDENCE_LIMIT       | 3       | Max facts/sources per step       | Keeps outputs concise |
| AGL_VERIFIER_EVIDENCE_LIMIT | 5 | GK_verifier: أقصى عدد أدلة/حقائق يعتمدها المُتحقِّق | ارفع/اخفض حسب الحاجة للدقة مقابل السرعة |
| AGL_ROUTER_RESULT_LIMIT  | 8       | Router returned branches/results | Wider exploration |
| AGL_REASONING_MAX_STEPS  | 16      | Planning depth                    | Safety caps loops |
| AGL_META_MAX_ITERS       | 3       | Meta-cycle iterations            | Budget/latency control |
| AGL_TIMEOUT_S            | 30      | Per-call timeout (seconds)       | Graceful fail |
| SAFETY_ENABLE            | 1       | Enable infra/safety guards       | 0 to disable (not recommended) |
| SAFETY_ALLOW_NETWORK     | 0       | Network access gate              | Set 1 for online runs |
| SAFETY_ALLOW_DISK_WRITE  | 1       | File writes gate                 | Flip to 0 in strict CI |

| AGL_GENERAL_KNOWLEDGE_CTX_CHARS     | 120     | طول معاينة السياق في General_Knowledge                 | |
| AGL_GENERAL_KNOWLEDGE_MAX_CHARS     | 1000    | حد أقصى للنص الطويل (extra/long snippet)               | |
| AGL_GENERAL_KNOWLEDGE_TOPK          | 3       | عدد العناصر/الأدلة المعروضة                            | |
| AGL_HYPOTHESIS_TOP_N                | 3       | عدد الفرضيات المولدة/المختارة                          | |
| AGL_ORCHESTRATOR_LIMIT              | 20      | حد عناصر نتائج الموجّه/الأوركستريتور                   | |
| AGL_GK_SUBJECT_PREVIEW_CHARS        | 20      | قصّ عناوين/موضوعات في GK_reasoner                      | |
| AGL_META_EXTRA_CHARS                | 1200    | طول معاينة extra في meta_orchestrator                  | |
| AGL_PERCEPTION_EVENTS_LIMIT         | 20      | عدد أحداث الإدراك التي تتم معاينتها في حلقة الإدراك    | |
| AGL_VISUAL_SPATIAL_OBJECTS_LIMIT    | 2       | حد معاينة قائمة الكائنات في Visual_Spatial            | |
| AGL_VISUAL_SPATIAL_DEFAULT_DIM      | 5       | البعد الافتراضي عند توليد مصفوفات 3D في Visual_Spatial | |
| AGL_INTENT_TOP_N                    | 3       | Core_Consciousness/Intent_Generator                    | حد أعلى لعدد النوايا المقترحة
| AGL_SOCIAL_CTX_CHARS                | 200     | Core_Engines/Social_Interaction                        | طول معاينة سياق العرض/النص الاجتماعي
| AGL_PLANNER_MAX_STEPS               | 8       | Core_Engines/Reasoning_Planner                         | الحد الأقصى لخطوات التخطيط/المحاولات

| AGL_HOSTED_LLM_TOP_K       | 3   | Core_Engines/Hosted_LLM             | الحد الأقصى لعدد النتائج من المزود المستضاف |
| AGL_HOSTED_LLM_MAX_TOKENS  | 512 | Core_Engines/Hosted_LLM             | حد الرموز الافتراضي عند عدم تحديده         |
| AGL_OPENAI_TOP_K           | 3   | Core_Engines/OpenAI_KnowledgeEngine | حد النتائج المسترجعة من OpenAI              |
| AGL_OPENAI_MAX_TOKENS      | 512 | Core_Engines/OpenAI_KnowledgeEngine | حد الرموز الممرّر للعميل إن أمكن            |
| AGL_OLLAMA_TOP_K           | 3   | Core_Engines/Ollama_KnowledgeEngine | حد النتائج المسترجعة من Ollama              |
| AGL_GK_GRAPH_MAX_NODES     | 500 | Core_Engines/GK_graph               | سقف عدد العُقد عند الإدخال/التحديث         |
| AGL_GK_GRAPH_MAX_EDGES     | 2000| Core_Engines/GK_graph               | سقف عدد الحواف عند الإدخال/التحديث         |

## Usage

```powershell
$env:AGL_RETRIEVER_K='11'; `
$env:AGL_EVIDENCE_LIMIT='5'; `
pytest -q
```

---

# لقطة CI جاهزة (Workflow مختصر)

ضع هذا في `.github/workflows/agl-env-check.yml`:

```yaml
name: agl-env-check
on: [push, pull_request]
jobs:
  env-switches:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install
        run: |
          python -m pip install -U pip
          pip install -e ".[test]"
      - name: Default behavior (no env)
---

## New AGL knobs (added by mass-parametrize)

| Variable         | Default | Scope                       | Purpose                         |
|------------------|---------|-----------------------------|---------------------------------|
| AGL_PREVIEW_20   | 20      | various                     | Tiny preview cap                |
| AGL_PREVIEW_120  | 120     | various                     | Small preview cap               |
| AGL_PREVIEW_500  | 500     | various                     | Medium preview cap              |
| AGL_PREVIEW_1000 | 1000    | various                     | Large preview cap               |
| AGL_PREVIEW_1200 | 1200    | various                     | XL preview cap                  |
| AGL_TOP_K        | 5       | retrievers/planners         | Default top-k                   |
| AGL_LIMIT        | 20      | orchestrators/routers       | Default result limit            |
| AGL_MAX_STEPS    | 8       | planners                    | Max planning steps              |
| AGL_MAX_TOKENS   | 512     | hosted/openai/ollama        | Generation token cap            |

### Retriever blending (TF-IDF + embeddings)

- `AGL_RETRIEVER_BLEND_ALPHA` (float, 0.0–1.0)
  - Default: **0.60**
  - Recommended (Arabic/semantic corpora): **0.65**  ← golden
  - Tuning range: **0.50–0.75** (e.g., 0.50, 0.60, 0.65, 0.75)
  - Guidance: Higher favors semantic matches (synonyms/context); lower favors literal TF-IDF.


        run: pytest -q tests/test_agl_env_switches.py -q
      - name: With env overrides
        env:
          AGL_RETRIEVER_K: "11"
          AGL_EVIDENCE_LIMIT: "5"
          AGL_ROUTER_RESULT_LIMIT: "12"
          SAFETY_ENABLE: "1"
          SAFETY_ALLOW_NETWORK: "0"
        run: pytest -q tests/test_agl_env_switches.py -q
```

---

المخاطر/الرجوع السريع

مخاطر: تضارب أسماء/إعادات import قد تُجمّد قيمة قديمة.
حل: اقرأ المتغيرات في أعلى الملف فقط، وضمن الاختبارات استخدم إعادة تحميل importlib.reload.

رجوع: كل تغيير محاط بقيم افتراضية مطابقة للسلوك السابق؛ إرجاع الوضع القديم = إزالة المتغير البيئي من الجلسة.

## New small Integration Blueprints knobs

These toggles are intentionally OFF by default. They enable small, in-place
adapters that are registered with the IntegrationRegistry. Use them for local
experimentation; they are safe and best-effort.

| Variable                    | Default | Purpose |
|---------------------------:|:-------:|--------|
| AGL_SELF_LEARNING_ENABLE   | 0       | Enable SelfLearningManager adapter (Self_Improvement) |
| AGL_DELIBERATION_ENABLE    | 0       | Enable DeliberationProtocol (Integration_Layer.network_orchestrator) |
| AGL_EMOTION_CONTEXT_ENABLE | 0       | Enable EmotionContextAdapter (Core_Consciousness.Self_Model) |
| AGL_PLANNER_ENABLE         | 0       | Enable PlannerHFSM wrapper (Core_Engines.Reasoning_Planner) |
| AGL_EXTERNAL_HOOKS_ENABLE  | 0       | Enable external hooks API (Integration_Layer.Domain_Router) |
| AGL_ASSOC_GRAPH_ENABLE     | 0       | Enable in-memory AssociativeGraph (Self_Improvement.Knowledge_Graph) |

Usage example (PowerShell):

```powershell
$env:AGL_SELF_LEARNING_ENABLE='1'; $env:AGL_PLANNER_ENABLE='1'; pytest -q
```

Note: these adapters are lightweight and are registered idempotently via the
IntegrationRegistry to avoid import-time side-effects. If you enable them in
CI, ensure test isolation or unset the variables after tests.
