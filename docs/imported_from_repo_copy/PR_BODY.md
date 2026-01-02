### Summary

- أضفت اختبار وحدة `tests/unit/test_rag_wrapper_composer.py` الذي يثبت أن
  `Integration_Layer.Hybrid_Composer.build_prompt_context(...)` يُستدعى عند استدعاء
  `rag_wrapper.rag_answer(...)` (باستخدام monkeypatch).
- حدّثت `AGENT.md` بإرشاد سريع عربي-أول يشرح متغيرات البيئة الأساسية لمسار RAG،
  خيارات الموفر، وطرق تفعيل المحاكاة (mocks).

### Why

- ضمان أن جميع دعوات RAG تمر عبر `Hybrid_Composer` المركزي (يمنع تجاوز المسار
  ويُحافظ على توحيد بناء الـprompt).
- توفير دليل عربي سريع للمساهمين الجدد لتشغيل وفحص إعدادات الـLLM/RAG محلياً.

### How to run

- لتشغيل اختبار الوحدة المفرد (لا حاجة لخادم LLM):

```powershell
py -3 -m pytest -q tests/unit/test_rag_wrapper_composer.py::test_rag_answer_uses_hybrid_composer -q -s
```

- إذا أردت أن ترى سلوك `rag_wrapper` مع إخراج غير فارغ أثناء الاختبارات، فعّل المحاكاة:

```powershell
$env:AGL_OLLAMA_KB_MOCK='1'; $env:AGL_EXTERNAL_INFO_MOCK='1'
```

### Notes

- الاختبار لا يحتاج إلى خادم Ollama أو OpenAI. فهو يحقن نسخة وهمية من
  `Integration_Layer.Hybrid_Composer` ولا يعتمد على الشبكة.
- لمعرفة لماذا انتقل CI إلى وضع المحاكاة (إن حدث)، راجع سجلات خطوة الـping في
  workflow CI (`.github/workflows/llm_smoke.yml`).

### Checklist

- [x] Unit test passes locally
- [x] Docs updated (`AGENT.md`)
- [x] No external network required for the new test

### Git commands (إذا اخترت الآن فتح الـPR)

```powershell
git checkout -b feat/rag-composer-test-and-docs
git add tests/unit/test_rag_wrapper_composer.py AGENT.md
# إن اخترت الخيار 1: أضف هذا الملف ليُستخدم كنص الـPR
git add PR_BODY.md
git commit -m "tests: ensure rag_wrapper uses Hybrid_Composer; docs: Arabic RAG quickstart; add PR_BODY"
git push -u origin feat/rag-composer-test-and-docs
# افتح PR من GitHub UI (استخدم محتوى هذا الملف كـ PR body)
```

---

قابل للتعديل: إن رغبت، أستطيع تعديل نص الملخص أو إضافة مزيد تفاصيل التشغيل أو
إضافة اختبار smoke ثانٍ الذي يتحقق من حقل `engine` في ثلاث حالات (real/mock/disabled).
Title: feat(core): IntegrationRegistry + RAG/ModelZoo fallbacks, meta-cognition & safety smoke tests

---

الملخّص (Arabic summary):
هذا الـ PR يضيف طبقة مركزية `IntegrationRegistry` لتجميع وتوجيه المحرّكات (RAG، ModelZoo، المسترجع، والبدائل الطارئة)، مع بدائل (fallbacks) آمنة وتحسينات meta-cognition وsafety gating. كما يضيف اختبارات smoke خفيفة تغطي التهيئة والتكامل: RAG, Safety, Self-Improvement, Meta-Cognition. تم تحديث التقرير: `reports/module_reference_report.json`.

النطاق (Scope):

- `Integration_Layer/integration_registry.py` — نقطة تجمع/تسجيل الخدمات (instances + lazy factories).
- `Integration_Layer/rag_wrapper.py` — تغليف RAG (اختبار/طوارئ بدون موفّرين خارجيين).
- `Learning_System/ModelZoo_Fallback.py` — بدائل ModelZoo.
- `Core_Engines/domain_router.py`, `Core_Engines/experience_memory.py` — شيم/توافق مع Legacy.
- `tests/*` — اختبارات smoke خفيفة: `test_smoke_config_and_registry.py`, `test_safety_smoke.py`, `test_self_improvement_smoke.py`, `test_meta_cognition_smoke.py`.
- تحديثات: `config.yaml`, `README.md`, `reports/module_reference_report.json`.

التحقق (Validation):

- تشغيل اختبارات smoke محليًا ونجاحها.
- التأكد أن الإقلاع لا يتطلب مكتبات ثقيلة في CI (Torch/Numpy غير مطلوبين للاختبارات المذكورة).

المخاطر والتخفيف (Risks & Mitigations):

- إمكانية تضمين ملفات تشغيلية مؤقتة (JSONL، تقارير) — استُبعدت عبر `.gitignore` أو لم تُضمّن في الالتزام.
- استيرادات قديمة/شيمات مؤقتة — خطة متابعة لاستبدال الاستيرادات repo-wide بعد الدمج، والشيمات تغطي الانتقال.

قائمة التحقق (Checklist):

- [x] تقرير `reports/module_reference_report.json` محدث ومضمن.
- [x] README و`config.yaml` محدثان لشرح مفاتيح الريجستري والأعلام (flags).
- [x] اختبارات smoke محلية تمر بنجاح.
- [x] لا تضمّن ملفات تشغيلية أو ملفات بيئة محلية.

---

English summary (short):
Adds a centralized `IntegrationRegistry` to orchestrate engines (RAG/ModelZoo fallbacks, retriever, emergency experts), plus lightweight smoke tests for RAG, Safety, Self-Improvement, and Meta-Cognition. Updated `reports/module_reference_report.json` and README/config entries. Temporary/local artifacts are ignored via `.gitignore`.

Suggested CI checks (to include in PR):

- Python matrix: 3.10 / 3.11
- Lint (ruff/flake8) + format (black)
- Run smoke: `pytest -q -k "smoke or meta or safety"`
- Generate artifact: `reports/module_reference_report.json`
- Run `audit_registration.py` and fail CI if suspect > baseline

How to open the PR (recommended flow if you don’t have write permission):

1) Fork + push + create PR (with GitHub CLI):
   gh auth login
   gh repo fork your-org/your-repo --remote=true
   git push -u fork feat/new-engines
   gh pr create --base main --head <YOUR_USERNAME>:feat/new-engines --title "feat(core): IntegrationRegistry + fallbacks and safety smoke tests" --body-file PR_BODY.md

2) If you have push access to the org repo, use:
   gh auth login
   git push -u origin feat/new-engines
   gh pr create --base main --head feat/new-engines --title "feat(core): IntegrationRegistry + fallbacks and safety smoke tests" --body-file PR_BODY.md

Notes:

- If you prefer HTTPS+PAT, generate a PAT with `repo` scope and use it when prompted for password.
- If you prefer SSH, add your key and set origin to `git@github.com:<your-org>/<your-repo>.git`.

---

(End of PR body)
