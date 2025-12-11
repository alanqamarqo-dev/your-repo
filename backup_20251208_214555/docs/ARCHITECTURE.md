# AGL Medical QA — Architecture & Integration (Arabic)

الملف هذا يصف كيف تتصل مكونات خطّ أنابيب FAST medical QA وفقًَا للخطوات المطروحة، ويرطِب كلّ خطوة بالمكان (الملف/السكريبت) الموجود الآن في المستودع.

الملخّص (خطوات التنفيذ):

1) استقبال الاستعلام (Input)

- الوصف: المستخدم يرسل سؤالًا نصيًّا. هذا السؤال يمرّ مباشرة إلى `HostedLLMAdapter`.
- ملف/نقطة دخول: `scripts/agl_master_entry.py` ➜ يستدعي adapter.

2) إدراج المعرفة المكتسبة (learned_facts)

- الوصف: قبل إرسال البرومبت إلى الـLLM، يتم استدعاء `load_learned_facts_as_context()` وإدراج النص الناتج داخل البرومبت (يساعد الاستمرارية المعرفية دون تعديل معلمات النموذج).
- ملف/دالة: `Self_Improvement/continual_learning.py::load_learned_facts_as_context`
- موضع الاستدعاء: `Self_Improvement/hosted_llm_adapter.py` (الـadapter الآن يَـقدم learned-facts إلى تجميعة الـprompt).

3) طبقة التحكم C-Layer

- الوصف: توليد `Intent` من المدخل، تمريرها إلى `Planner` لتحديد خطوات العمل، وتسجيل الحالة في `AGLState`/`MetaLogger` وحفظ snapshots.
- ملفات/مكونات:
  - `Integration_Layer/agl_state.py` — حالة الجلسة، لوجات، لقطات (snapshots).
  - `Self_Improvement/meta_logger.py` — سجلّ الجلسة JSONL.
  - `scripts/agl_master_entry.py` — نقطة إدخال تجريبية تربط C-Layer.

4) وكلاء داخليون + القائد التنفيذي

- الوصف: `ExecutiveAgent` يوزع المهام على وكيل داخليّ مستقلّ لكل جزء من الخطة، وكل وكيل يحدث `learned_facts.jsonl` عند اكتمال المهام.
- ملفات مرجعيّة: مجلد `Integration_Layer/` وملفات `Self_Improvement/` (إن وُجدت). (إن لم تكن جميع الوكلاء موجودين كملفات منفصلة بعد، هذه نقطة تنفيذ لاحقة.)

5) حلقة التخطيط / Deliberation

- الوصف: `PlannerAdapter` / `DeliberationAdapter` تُستخدم لتوليد خطط تنفيذية متقدمة وتوجيه حلقات العمل.
- وضع التنفيذ: يتم تمثيل هذا جزئيًا عبر الـPlanner في `Integration_Layer` ونداءات في `scripts/`، ويمكن ترقية `Self_Improvement` لاحقًا.

6) نظام التعلم (Learning System)

- الوصف: حفظ الخبرات في `ExperienceMemory`/`TemporalMemory`، تشغيل Generalizer لاستخراج أنماط، وخلق بيانات تدريب باستخدام `scripts/make_train_from_learned.py` لإعادة تدريب LoRA/Fine-tune لاحقًا.
- ملفات: `scripts/make_train_from_learned.py`, `artifacts/learned_facts.jsonl`, `1762911536282/infra/adaptive/train_input.jsonl` (مثال مخرجات ETL).

7) RAG / Grounding

- الوصف: استرجاع مقتطفات داعمة من الفهرس (`rag_index.jsonl`) وإرفاقها بالإجابة؛ ربطها بالـ`learned_facts` لتحسين الدقّة؛ إعادة فهرسة دورية بعد كل تعلم.
- ملفات/أدوات:
  - `Self_Improvement/rag_index` (module / index files)
  - `scripts/extract_medical_grounding.py` — يستخرج المقتطفات ويولد `artifacts/medical_grounding_report.txt` مع مطابقة حرفيّة.

8) المخرجات

- الوصف: إجابة نهائية منظمة بالعربية الفصحى، مدعومة بمقتطفات RAG ومذكورة provenance مفصّلة (بما في ذلك حالة إعادة الكتابة `rewriter`).
- ملفات الإخراج:
  - `artifacts/medical_grounding_report.txt` — تقرير grounding مع `start/end/match_len`.
  - `artifacts/medical_queries.jsonl` — سجلات الأسئلة والأجوبة مع الحقول `rag_used`, `provenance`.

التدفق الكلي (pipeline):

Input → `HostedLLMAdapter` (prepends learned_facts) → C-Layer (Intent → Planner → StateLogger) → ExecutiveAgent/Internal Agents → Learning System (update `learned_facts.jsonl`) → RAG (retrieve snippets) → Rewriter (hosted + deterministic local fallback) → Output + grounding report + snapshots/logs

ملاحظات تشغيلية وخطوات استرداد عند فشل الدفع (push 403):

- سبب شائع: بيانات الاعتماد (credentials) المستخدمة في هذه البيئة لا تملك صلاحية الكتابة على الريموت (`Permission denied to myykl33-dot`).
- حلول مقترحة:
  1) استخدم GitHub CLI و`gh auth login` على جهازك المحلي ثم ادفع:

     ```powershell
     $env:PYTHONPATH='.'; git push --set-upstream origin agl-v1-integration
     gh pr create --base main --head agl-v1-integration --title "integration: prepend learned-facts context" --body "Includes `artifacts/medical_grounding_report.txt`."
     ```

  2) أو إعداد SSH وتهيئة الريموت للـSSH:

     ```powershell
     git remote set-url origin git@github.com:alanqamarqo-dev/your-repo.git
     $env:PYTHONPATH='.'; git push --set-upstream origin agl-v1-integration
     gh pr create --base main --head agl-v1-integration --title "integration: prepend learned-facts context" --body "Includes `artifacts/medical_grounding_report.txt`."
     ```

  3) أو استخدم Personal Access Token (PAT) مع `git remote set-url` للـHTTPS إذا لا تريد SSH.

قائمة فحوصات Smoke-run (لتشغيل محلي أو في CI):

1. تأكّد من بيئة Python و`PYTHONPATH='.'` وأن الاعتمادات محلية مفعّلة.
2. تشغيل ETL من الحقائق المكتسبة:

```powershell
$env:PYTHONPATH='.'; py -3 scripts/make_train_from_learned.py
```

3. تشغيل ثلاثة استعلامات عربية عبر نقطة الدخول:

```powershell
$env:PYTHONPATH='.'; py -3 scripts/agl_master_entry.py -q "ما هي أعراض الإنفلونزا؟"
$env:PYTHONPATH='.'; py -3 scripts/agl_master_entry.py -q "ما أسباب ارتفاع ضغط الدم؟"
$env:PYTHONPATH='.'; py -3 scripts/agl_master_entry.py -q "ما هو الفشل الكلوي المزمن؟"
```

4. إعادة توليد تقرير الـgrounding (بدون اقتطاع إن رغبت بذلك — عدّل الاستخراج لعدم القصّ):

```powershell
$env:PYTHONPATH='.'; py -3 scripts/extract_medical_grounding.py --no-trim --out artifacts/medical_grounding_report_full.txt
```

(إن لم يدعم السكريبت الخيار `--no-trim`، يمكن تعديل `scripts/extract_medical_grounding.py` لتمرير قيمة `max_chars=None` أو مماثلة.)

خطوات مقترحة لاحقة (إن رغبت بها الآن):

- إضافة فلتر/تثمين لنتائج `load_learned_facts_as_context()` (recency/score/source-weighting).
- جعل الـrewriter يسجّل نسخة نصّية قبل/بعد التعديل لمراجعة التغييرات (useful for audits).
- CI job لتشغيل smoke-run وإرفاق `artifacts/medical_grounding_report.txt` إلى الـPR.

إذا رغبت، أستطيع الآن:

- تحديث `scripts/extract_medical_grounding.py` ليدعم `--no-trim` وإعادة تشغيل الاستخراج محليًا، أو
- إضافة ملف PR template أو نص `gh` لإنشاء PR تلقائيًا فور إصلاح صلاحيات الدفع، أو
- تنفيذ فلتر بسيط للـlearned-facts وكتابة اختبار صغير.

---
إصدار: 1.0 — تم الإنشاء: 2025-11-20
