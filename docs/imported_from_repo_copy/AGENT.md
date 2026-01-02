AGENT quick start (Arabic-first, short)

هذا الملف يشرح بسرعة كيفية تشغيل AGL محليًا وكيف يختار الوكيل موفر الـLLM.

1) اختيار مزوّد النموذج

- المتغير الرئيسي: `AGL_LLM_PROVIDER` (مثال: `ollama`, `openai`, `http`)
- نموذج/نسخة: `AGL_LLM_MODEL` (مثال: `qwen2.5:3b-instruct`)
- نقطة النهاية (عند استخدام HTTP/ollama local): `AGL_LLM_BASEURL` أو `OLLAMA_API_URL` (مثال: `http://127.0.0.1:11434`)

2) فحص سريع (PowerShell واحد-سطر)

استخدم هذا السطر لتشغيل فحص الـLLM سريعًا (PowerShell):

    $env:AGL_FEATURE_ENABLE_RAG='1'; $env:AGL_LLM_MODEL='qwen2.5:3b-instruct'; $env:AGL_LLM_BASEURL='http://127.0.0.1:11434'; python scripts/quick_llm_ping.py --expect 200 --timeout 10

3) متى تستخدم المحاكاة (mocks)

- المتغيرات: `AGL_EXTERNAL_INFO_MOCK`, `AGL_OLLAMA_KB_MOCK`, `AGL_OPENAI_KB_MOCK` — عند تفعيلها تعيد المحركات مخرجات مُعلّمة بـ "محاكاة:".

4) أين تنظر عند فشل الاختبارات

- `artifacts/bootstrap_report.json` — قائمة المحركات المسجلة والمتخطاة.
- `artifacts/logs/` — سجلات تشغيل المحركات والتشخيص.

5) تلميحات سريعة لإصلاحات شائعة

- 405 Method Not Allowed: تأكد أن `AGL_LLM_BASEURL` يشير إلى endpoint يقبل POST مثل `/api/generate`.
- CLI not found: إذا تعتمد على `ollama` عبر CLI تأكد أن `ollama.exe` في PATH أو استخدم HTTP endpoint.
- JSON decode errors: قد يكون الخادم يعِدّ استريم chunked — حدّث الخادم أو استخدم نسخة متوافقة من العميل.

انظر `.github/copilot-instructions.md` لوصف تفصيلي ثنائي اللغة وإرشادات إضافية.

# AGENT.md

## مرحبًا — موجز للوكيل / Assistant quickstart

العربية: هذا ملف ترحيبي موجز لوكيل الذكاء الاصطناعي أو لمطور جديد. ابدأ بقراءة `d:\AGL\.github\copilot-instructions.md` (العربية أولًا ثم الإنجليزية). يتضمن الملف مفاتيح التشغيل، متغيّرات البيئة المهمة، وكيفية كشف وضع المحاكاة (mock).

English: Short welcome for an AI assistant or a new developer. Read `.github/copilot-instructions.md` first (Arabic-first). It contains run keys, env vars, and mock detection.

## تشغيل سريع

- افحص `AGL_LLM_PROVIDER`, `AGL_LLM_MODEL`, `AGL_LLM_BASEURL` وامسح أي متغيّرات mock.
- شغّل فحص سريع:

```powershell
Remove-Item env:AGL_OLLAMA_KB_MOCK -ErrorAction SilentlyContinue;
& 'C:\Path\To\python.exe' 'D:\AGL\quick_llm_ping.py'
```

## أين أبحث عن السلوكيات الأساسية

- نقطتان رئيسيتان: `Core_Engines/Hosted_LLM.py` و`Core_Engines/Ollama_KnowledgeEngine.py`.

English: Quickstart: clear mock env, run the ping script, and inspect `Hosted_LLM.py` and `Ollama_KnowledgeEngine.py` for model selection and mock behavior.

---

تشغيل الـLLM ودمج RAG (سريع)

المتغيرات الأساسية

AGL_FEATURE_ENABLE_RAG=1 لتفعيل مسار RAG.

اختيار المزوّد:

Ollama HTTP

AGL_LLM_PROVIDER=ollama

AGL_LLM_BASEURL=<http://127.0.0.1:11434>

AGL_LLM_MODEL=qwen2.5:3b-instruct (أو ما تفضّل)

OpenAI

AGL_LLM_PROVIDER=openai

OPENAI_API_KEY=...

(اختياري) AGL_LLM_MODEL=gpt-4.1-mini (أو الاسم المناسب)

وضع المحاكاة (للـCI أو التطوير بدون نموذج):

AGL_OLLAMA_KB_MOCK=1 و/أو AGL_EXTERNAL_INFO_MOCK=1

كيف يُبنى الـPrompt؟

يعتمد `rag_wrapper.rag_answer(...)` على
`Integration_Layer.Hybrid_Composer.build_prompt_context(story, questions)`
لينتج رسالتين: system + user، ويتم إرسالها للمزوّد (Ollama/OpenAI).

تدفق التنفيذ (تبسيط):

1. بناء prompt عبر Hybrid_Composer.

2. محاولة الاتصال:

HTTP Ollama → ثم CLI Ollama (fallback) → ثم OpenAI (إذا مفعّل).

3. إن فشل الاتصال أو عاد نص فارغ:

إن كان وضع المحاكاة مفعّلًا → يرجع engine=rag-mock مع نص غير فارغ.

غير ذلك → engine=rag-noop.

فحص سريع (PowerShell)

$env:AGL_FEATURE_ENABLE_RAG='1'
$env:AGL_LLM_PROVIDER='ollama'
$env:AGL_LLM_BASEURL='http://127.0.0.1:11434'
$env:AGL_LLM_MODEL='qwen2.5:7b-instruct'
python scripts/quick_llm_ping.py

> لو فشل الـping (خادم غير متاح)، فعّل المحاكاة مؤقتًا:

$env:AGL_OLLAMA_KB_MOCK='1'
$env:AGL_EXTERNAL_INFO_MOCK='1'
