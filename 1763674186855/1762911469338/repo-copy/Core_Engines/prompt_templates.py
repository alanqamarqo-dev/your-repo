"""Prompt templates used by the Orchestrator.

Each template below is written in Arabic and enforces a strict output
contract so the orchestrator can parse and act deterministically.

Roles implemented:
- TOOL_CHOOSER: summarize the user query and return ONE JSON object only
  (no extra text). The JSON must follow the schema described in the
  template. This prompt must force the model to choose one tool and to
  produce well-formed JSON.
- SYNTHESIS: take tool outputs and produce a concise Arabic answer with
  numbered bullet points (when helpful) and a single-line final result.
  Do not introduce facts not present in the tool outputs; if evidence
  is missing, state that explicitly.
- VERIFIER: self-critique the draft answer (or the tool outputs). Return
  a short JSON report with pass/fail and short notes.
"""


TOOL_CHOOSER = (
    "مهمة: اختر أكثر أداة مناسبة للإجابة على طلب المستخدم. أجبْ بـ JSON واحد فقط "
    "دون أي تعليق نصي إضافي.")

TOOL_CHOOSER += (
    "\n\nقواعد خروج المخرَج (الزامي):\n"
    "1) أعد كائن JSON وحيد بصيغة: {\n"
    "   \"tool\": \"<tool_name>\",   // اسم الأداة بالضبط\n"
    "   \"args\": { ... }               // كائن الوسائط (قد يكون فارغًا)\n"
    "}\n"
    "2) لا تضع أي نص خارج JSON. لا تستخدم علامات اقتباس زائدة أو شروح.\n"
    "3) إذا لم تكن بحاجة لأي أداة، استخدم: {\"tool\": \"none\", \"args\": {}}\n"
)

TOOL_CHOOSER += (
    "\nالمخرجات المتاحة (مثال أسماء): \n"
    "- exp_algebra.solve  => يحل معادلات/حسابات دقيقة\n"
    "- rag.search         => استرجاع مستندات/مراجع (RAG)\n"
    "- causal.infer       => استنتاجات سببيّة وتحليل علاقات سببية\n"
    "- safety.review      => فحص سياسات/سلامة ومراجعة محتوى\n"
    "\nتناول الطلب أدناه ثم أعد JSON اختيار الأداة فقط.\n"
    "مثال ناجح:\n{\"tool\": \"rag.search\", \"args\": {\"query\": \"متى اكتُشفت البنسلين؟\"}}\n"
)


SYNTHESIS = (
    "مهمة: صِغ إجابة عربية دقيقة ومختصرة بناءً فقط على مخرجات الأدوات التالية.\n"
    "اتبع القواعد التالية بدقة:\n"
    "1) لا تضف معلومات خارج مخرجات الأدوات. إن كانت معلومة ناقصة، اذكر بوضوح ما الناقص.\n"
    "2) اجعل الإجابة قصيرة: 2-5 جمل إجمالية، مع نقاط مرقمة موجزة عند الحاجة.\n"
    "3) ابدأ بعنوان موجز (سطر واحد)، ثم نقاط مرقمة (إن وُجدت)، ثم سطر «النتيجة النهائية: ...».\n"
    "4) اجعل اللغة رسمية وواضحة بالعربية، واحتفظ بالحقائق فقط.\n"
  "5) إذا أرفقنا مقتطفات بحث (RAG) فاستشهد بها بصيغة مرجع رقمي [1], [2], ... عند بناء الاستنتاجات، واكتب في خانة الاقتباسات (citations) فقط المراجع المستخدمة.\n"
    "\nالمدخل: JSON يصف مخرجات الأدوات، مثال:\n"
    "{\n  \"tools\": [\n    {\"name\": \"exp_algebra.solve\", \"result\": \"x=3\"},\n    {\"name\": \"rag.search\", \"result\": \"مقتطف من مصدر: ...\"}\n  ]\n}\n"
    "\nالمخرجات المتوقعة (نموذجي):\n"
    "<عنوان موجز>\n1) نقطة موجزة واحدة أو اثنتين تستند إلى الأدلة.\n2) (اختياري) تقييدات/ملاحظات قصيرة إن وجدت.\nالنتيجة النهائية: <خلاصة أحادية السطر>\n"
)


VERIFIER = (
    "مهمة: افحص النص/الادعاءات والمخرجات المقدمة وابحث عن تناقضات أو ادعاءات غير مدعومة.\n"
    "أعد فقط JSON قصيرًا بالصيغة التالية:\n"
    "{\n  \"passed\": true|false,    // هل اجتاز الفحص من وجهة نظرك؟\n  \"notes\": [\"ملاحظة قصيرة 1\", \"ملاحظة قصيرة 2\"]\n}\n"
    "قواعد:\n"
    "- اذا كان هناك نقص في الأدلة أو تناقض واضح، اجعل passed=false واذكر الملاحظة المختصرة.\n"
    "- الاكتفاء بالملاحظات القصيرة (1-3 عناصر). لا تُطِل.\n"
)

# End of templates
