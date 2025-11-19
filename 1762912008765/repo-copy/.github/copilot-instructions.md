Short, actionable guidance for AI coding assistants working in this repository.
## ⚙️ ما يجب معرفته أولًا | What to know first

العربية (مختصر): هذا المشروع يشغّل نظام AGL محلي مدعوم بنماذج لغوية ويَتكوّن من ثلاث طبقات رئيسية:
- `Core_Engines/`: محركات ومولّدات المعرفة وواجهات LLM (انظر `Hosted_LLM.py`, `Ollama_KnowledgeEngine.py`, `External_InfoProvider.py`, `__init__.py`).
- `Integration_Layer/`: تكوين المطالبات وتوجيه الطلبات (انظر `Hybrid_Composer.py`, `Action_Router.py`).
- واجهة المستخدم والسكربتات: `AGL_UI/` وملفات الأدوات مثل `quick_llm_ping.py` و `quick_run_test1.py`.

English (short): The repo runs a local, LLM-backed AGL orchestration system with three main areas: `Core_Engines/` (LLM adapters and engines), `Integration_Layer/` (prompt composer & router), and UI/scripts (`AGL_UI/`, quick checks).


## ⚙️ اختيار النموذج | Model Selection

العربية: الدالة الرئيسية التي تستدعي النماذج هي `Core_Engines.Hosted_LLM.chat_llm`. تبني prompt من أول رسالة `system` وأول رسالة `user` ثم تختار موفّر النموذج عبر متغيّر البيئة `AGL_LLM_PROVIDER` (أو `AGL_EXTERNAL_INFO_IMPL`).
إن كان الموفر `ollama`/`http` وموضوعة المتغيرات `AGL_LLM_BASEURL` (أو `OLLAMA_API_URL`) و`AGL_LLM_MODEL` فستحاول `chat_llm` إرسال HTTP POST إلى مسارات شائعة مع retry/backoff (المتغيران: `AGL_HTTP_RETRIES`, `AGL_HTTP_BACKOFF`). عند الفشل، تُعيد المحاولة داخليًا إلى `OllamaKnowledgeEngine.ask()`، التي تفضّل `OLLAMA_API_URL` وإلا تستدعي CLI `ollama`.

English: `chat_llm` builds a single prompt (first system + first user), picks a provider using `AGL_LLM_PROVIDER`, attempts HTTP POSTs for Ollama-like servers (with retries/backoff), and falls back to `OllamaKnowledgeEngine.ask()` which uses `OLLAMA_API_URL` HTTP or the `ollama` CLI.


## 🧰 متغيّرات بيئة مهمة | Important environment variables

العربية: لا تترجم أسماء المتغيرات/الملفات عند الإشارة إليها — اذكر شرحًا عربيًا بعدها.
- Mock flags: `AGL_EXTERNAL_INFO_MOCK`, `AGL_OLLAMA_KB_MOCK`, `AGL_OPENAI_KB_MOCK` — (عربي: عند التفعيل تُرجع المحركات مُخرجات مقلّدة).
- موفّر/نموذج/قاعدة: `AGL_LLM_PROVIDER`, `AGL_LLM_MODEL`, `AGL_LLM_BASEURL`, `OLLAMA_API_URL` — (عربي: تحدد مصدر النموذج وURL للخادم).
- كاش وسلوك: `AGL_OLLAMA_KB_CACHE`, `AGL_OLLAMA_KB_CACHE_ENABLE`، وإعدادات HTTP: `AGL_HTTP_RETRIES`, `AGL_HTTP_BACKOFF`.

PowerShell (نسخة سريعة لمسح وضعية mock وتعيين مزوّد محلي):

```powershell
Remove-Item env:AGL_EXTERNAL_INFO_MOCK -ErrorAction SilentlyContinue;
Remove-Item env:AGL_OLLAMA_KB_MOCK -ErrorAction SilentlyContinue;
Remove-Item env:AGL_FORCE_EXTERNAL -ErrorAction SilentlyContinue;
$env:AGL_LLM_PROVIDER='ollama';
$env:AGL_LLM_MODEL='qwen2.5:7b-instruct';
$env:AGL_LLM_BASEURL='http://localhost:11434';
```

English: Keep names exact (`AGL_LLM_PROVIDER`, etc.). Use the PowerShell snippet above to clear mock flags and point to a local Ollama endpoint.


## 🧭 اكتشاف الوضع الوهمي (Mock) | How to detect mock/stubbed responses

العربية: `OllamaKnowledgeEngine._call_model` يُرجع نصًا يبدأ بـ `محاكاة:` عندما يكون `AGL_OLLAMA_KB_MOCK` مفعّلًا. البحث عن هذه البادئة يكشف ردود مقلّدة.

English: In mock mode `OllamaKnowledgeEngine._call_model` returns responses prefixed with `محاكاة:` — use this string to detect stubbed replies.


## ✍️ نمط بناء المطالبات | Prompt & messaging conventions

العربية: استخدم `Integration_Layer.Hybrid_Composer.build_prompt_context(story, questions)` — تُعيد قائمتين (`system`, `user`) وتطبّق `AR_SYSTEM` (تعليمات عربية). ملاحظة: `chat_llm` حالياً يلتقط فقط أول `system` وأول `user`، فادمج رسائلك إذا احتجت أكثر.

English: Prefer `build_prompt_context(story, questions)` to create [{role:system},{role:user}]. `chat_llm` currently consumes only the first system and first user message.


## 🔌 تسجيل وتهيئة المحركات | Engine bootstrap & registration

العربية: انظر `Core_Engines.__init__.ENGINE_SPECS` و`bootstrap_register_all_engines(registry, ...)`. السلوكيات المهمة:
- يفضّل `create_engine(config)` إذا وُجد، وإلا يبني الصنف (يحاول تمرير `config`).
- يتأكد من وجود `process_task` (duck-typing) ويعيّن `name` افتراضيًا إذا لم يكن موجودًا.
- دالة `_try_registry_register` تقبل عدة واجهات `registry` (dict، `register(name=..., engine=...)`, `add_engine`, ...).
- دالة التسجيل تكتب `artifacts/bootstrap_report.json` التي تحتوي قوائم المحركات المسجّلة والمتخطاة.

English: `bootstrap_register_all_engines` prefers `create_engine`, validates `process_task`, handles many registry APIs, and writes `artifacts/bootstrap_report.json`.


## 🔍 أمثلة لأخطاء نمطية وكيفية إصلاحها | Common error examples & fixes

1) HTTP 405 Method Not Allowed
- السبب: تشغيل خادم دون تمكين POST على المسار `/api/generate` أو استخدام الجذر بدلاً من المسار الصحيح.
- الإصلاح: تأكد أن `AGL_LLM_BASEURL` يشير إلى المسار الصحيح (مثلاً `/api/generate`) أو قم بتشغيل الخادم مع تمكين POST.

English: Ensure `AGL_LLM_BASEURL` points at the correct endpoint (e.g. `/api/generate`) and server accepts POST.

2) CLI not found (OSError [WinError 2])
- السبب: `ollama` غير موجود في PATH.
- الإصلاح: أضف `ollama.exe` إلى PATH أو استخدم `AGL_LLM_BASEURL` للتواصل عبر HTTP.

English: Add `ollama` to PATH or configure `AGL_LLM_BASEURL` to use HTTP endpoint.

3) JSON Decode Error from Ollama HTTP
- السبب: نسخ قديمة من Ollama تُرجع استريم chunked بدلاً من JSON كامل.
- الإصلاح: حدّث Ollama إلى ≥ 0.2.8 أو عيّن الخادم لإرجاع JSON أو عالج stream chunks في العميل.

English: Upgrade Ollama (>=0.2.8) or adjust server/consumer to handle streaming chunks.

4) Timeout (> AGL_LLM_TIMEOUT)
- الإصلاح: قلّل طول الـprompt أو استخدم نموذج أصغر (`qwen-3b` بدلاً من `qwen-7b`)، أو زيّد مهلة HTTP.

English: Reduce prompt size, use smaller model (e.g. qwen-3b), or increase HTTP timeout.


## 🧪 Continuous Integration Notes

العربية: `conftest.py` يضبط المتغيرات الافتراضية لاعدادات RAG ويشغّل `bootstrap_register_all_engines` قبل الاختبارات. تولّد CI تقارير مثل `artifacts/bootstrap_report.json` و`artifacts/latency_summary.json`.
فشل `quick_llm_ping.py` في CI غالبًا يدل على عدم توافر المزود الخارجي (ليس دائماً فشلًا شاملاً).

English: `conftest.py` sets default RAG env vars and runs engine bootstrap; CI artifacts include `bootstrap_report.json` and `latency_summary.json`. `quick_llm_ping.py` failure in CI often indicates external LLM unavailability rather than full-test failure.


## 🛠️ ملفات مساعدة مقترحة | Suggested companion files

- `AGENT.md`: a short Arabic-first welcome with the core pointers and env names.
- `scripts/smoke_llm_ping.py`: a smoke-check script for CI: `python scripts/smoke_llm_ping.py --expect 200 --timeout 10`.


## إن أردت المزيد
أستطيع تجهيز نسخة كاملة ثنائية اللغة، إضافة أمثلة أخطاء إضافية أو إنشاء hook بسيط في CI لتشغيل `scripts/smoke_llm_ping.py` بعد الـbootstrap. أخبرني بما تفضّل.

If anything is unclear or you want different emphasis (fully Arabic main copy, extra error examples, or CI hooks), tell me and I'll update the files.
