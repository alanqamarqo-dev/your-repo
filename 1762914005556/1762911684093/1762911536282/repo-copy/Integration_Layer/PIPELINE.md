# خط الأنابيب (Pipeline) — ملخّص تقني

وصف مُدمج لخط معالجة رسالة المستخدم داخل النظام. هذا المستند يطابق التسلسل المطلوب: واجهة → استرجاع سياق → تفسير → استرجاع معرفة اختياري → تخطيط → تنفيذ محركات → دمج → تنسيق/حراسة → إرجاع JSON.

1) الواجهة → السيرفر
- نقطة الدخول: POST /api/ask
- مدخل JSON: {"session_id": "...", "text": "...", "meta": { /* flags, tools enabled */ }}

2) استخلاص السياق
- يرشد `Conversation_Manager` بجمع: تاريخ الجلسة، السجل الأخير (N turns)، الأدوات المفعّلة، قيود الأمان، سياسات الخصوصية.

3) التفسير (Intent + NLU)
- استدعاء `Intent_Recognizer`:
  - ناتج: { "intent": "ask_info|command|summarize|code|translate", "entities": {"topic":..., "units":..., "language":...}, "confidence": 0.0 }

4) استرجاع المعرفة (اختياري)
- إذا كان العلم/البحث مفعّلًا، استدعِ `retriever` ليبحث في KB/ملفات/ويب.
- ناتج: قائمة من الأدلة/مقتطفات مع مصادر وscore.

5) التخطيط (Planner)
- `Pipeline_Orchestrator` يقرّر مسار التنفيذ استنادًا إلى النية والكيانات والسياق:
  - مثال: ask_info(physics) -> [Math_Brain, General_Knowledge, Strategic_Thinking]
  - يعين ترتيب/توازي وتشغيل المحركات، مع حدود زمنية لكل محرك.

6) التنفيذ متعدد المحركات
- تنفيذ المحركات المحددة بالتوازي أو بالتتابع.
- كل محرك يعيد: {"engine": "name", "text": "...", "confidence": 0.0, "evidence": [...], "latency_ms": 0}

7) الدمج والتقييم
- `Meta_Ensembler` يجمع مخرجات المحركات، يقيس التوافق، ويحسب ثقة إجمالية.
- قواعد الاختيار: prefer higher confidence + supporting evidence; إذا التعرُّض للاختلاف الكبير، اطلب توضيح/ن موثّق.

8) التنسيق والحراسة
- `Output_Formatter` ينسّق النص النهائي.
- `Dialogue_Safety` يطبق قواعد الحماية: حذف معلومات حسّاسة، الحد من الافتراضات، إزالت/استبدال العبارات المضلّلة، وسياسة الاستشهاد بالمصادر.

9) العودة للواجهة
- المخرجات (JSON):
{
  "ok": true,
  "text": "...",
  "confidence": 0.87,
  "engine_trace": [ {"engine":"General_Knowledge","confidence":0.5,"latency_ms":120}, ... ],
  "sources": ["kb://...","web://..."],
  "elapsed_ms": 432,
  "mini_log": ["intent=ask_info","used_retriever","nlp_fallback"]
}

عقدة قصيرة (Contract)
- Inputs: JSON مع `session_id`, `text`, و`meta`.
- Success: `ok: true` و`text` غير فارغ، و`confidence` بين 0 و1.
- Failure modes: `ok:false` و`error` يشرح السبب (validation, engine_error, no_knowledge, safety_block).

حالات الحافة (Edge cases)
- محرك GK يرجع عبارات "no_evidence" أو canned placeholders -> شغّل NLP fallback ثم OpenAI KB (بشرط وجود مفتاح صالح).
- المفتاح الخارجي غير صالح -> سجّل الخطأ واستخدم مزوّد محلي أو رد موحّد قابل للشرح.
- طلبات حسّاسة/قانونية/طبية -> امنع الإجابة الآلية واطلب استشارة إنسانية.
- جلسات طويلة جدًا -> قطع السياق واختصار (sliding window).

معايير القبول (Acceptance criteria)
- تتوفّر وثيقة `Integration_Layer/PIPELINE.md` تحتوي الخطوات والعقد وحالات الحافة.
- اختبارات: ملف `tests/test_pipeline_spec.py` يمرّ (يتحقق من وجود الوثيقة ومقتطف JSON في المحتوى).

خطوات متابعة مقترحة
- تنفيذ `Pipeline_Orchestrator` أو تحديثه ليطبّق المنطق أعلاه.
- إضافة قياسات زمنية لكل طبقة ومؤشرات جودة (QA) لحالة الدقة.
- إعداد مفتاح OpenAI آمن/اختباري أو محاكاة (mock) لكي تُقاس الفائدة الحقيقية من OpenAI KB.

