تشغيل القياس (Bench)

- الهدف: تحويل الأدوات المتناثرة إلى مسار واحد ينتج أرقام (دقة/استقرار/زمن).

تشغيل:
- من مجلد AGL_NextGen:
  - `python AGL_BENCH_RUN.py`

إعدادات:
- `AGL_BENCH_REPEATS` عدد التكرارات لكل مهمة (للاستقرار)
- `AGL_BENCH_USE_CORE` 1 لاستخدام Core_Consciousness_Module إن كان متاحاً (الافتراضي الآن: 0)
- `AGL_BENCH_SUITE` اختيار نوع القياس:
  - `deterministic` (افتراضي): مهام حتمية Offline
  - `causal`: استخراج علاقات سبب→نتيجة بواسطة Causal_Graph
  - `planning`: قياس “أهداف فرعية/خطوات” عبر خطوات حل معادلات في Mathematical_Brain
  - `planner`: قياس خطة نصية (3 خطوات مرقمة) عبر MicroPlanner
  - `deterministic_holdout`: نفس الفكرة لكن بأسئلة غير موجودة في السويت الأساسية
  - `causal_holdout`
  - `planning_holdout`
  - `planner_holdout`
  - `planner_strict_holdout`: Holdout صارم (الكلمات المطلوبة يجب أن تظهر داخل نص الخطوات، ليس فقط العنوان)

أمثلة:
- تشغيل causal:
  - في CMD:
    - `set AGL_BENCH_SUITE=causal && python AGL_BENCH_RUN.py`
- تشغيل planning:
  - في CMD:
    - `set AGL_BENCH_SUITE=planning && python AGL_BENCH_RUN.py`

النتائج:
- تُكتب في `AGL_NextGen/artifacts/bench_runs.jsonl`

مقارنة ضد Baseline (تفوق قابل للقياس):
- تشغيل (Holdout فقط):
  - من مجلد AGL_NextGen:
    - `python AGL_BENCH_COMPARE.py`
- إعدادات:
  - `AGL_BENCH_SUITE` أحد: `deterministic_holdout|causal_holdout|planning_holdout|planner_holdout`
  - `AGL_BENCH_REPEATS` تكرار لكل مهمة
- النتائج:
  - تُكتب في `AGL_NextGen/artifacts/bench_compare.jsonl`

حلقة تحسين ذاتي (مقاسة):
- تشغيل:
  - من مجلد AGL_NextGen:
    - `python AGL_SELF_IMPROVE.py`
- إعدادات:
  - `AGL_SELF_IMPROVE_SUITES` قائمة السويتات مفصولة بفواصل (افتراضي: deterministic,causal,planning,planner)
  - `AGL_SELF_IMPROVE_ITERS` عدد الدورات (افتراضي: 1)
  - `AGL_SELF_IMPROVE_TARGET` الهدف (accuracy) لإيقاف الدورة مبكرًا (افتراضي: 1.0)
- النتائج:
  - تُكتب في `AGL_NextGen/artifacts/self_improve_runs.jsonl`

بوابة تعديل ذاتي داخل Sandbox (قبول/رفض بناءً على Holdout):
- تفعيل:
  - `AGL_SELF_IMPROVE_GATE=1`
- إعدادات:
  - `AGL_SELF_IMPROVE_GATE_SUITE` (افتراضي: `planner_strict_holdout`)
  - `AGL_SELF_IMPROVE_REGRESSION_SUITES` (افتراضي: `planner,deterministic`)
- السجل:
  - `AGL_NextGen/artifacts/self_improve_gate.jsonl`
