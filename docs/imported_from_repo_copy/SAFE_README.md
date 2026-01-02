هدف هذه الوثيقة

قائمة تحقق وإرشادات لتشغيل مكوّنات `Self_Improvement` في بيئة اختبار مُعزَّلة وآمنة دون السماح بتعديلات مباشرّة على الشيفرة المصدرية أو الوصول للشبكة.

ملاحظات عاجلة (مُلخّص النتائج)

- تم مسح مجلد `Self_Improvement/` وُجدت عمليات كتابة ملفات واسعة النطاق (many open(..., 'w')), استدعاءات `subprocess.run(...)`, واستخدام `importlib.import_module(...)` ووجود دالة `apply_patch(...)` في `Knowledge_Graph.py` التي تطبّق باتشات عبر git.
- ملفات ذات أولوية مراجعة: `Self_Improvement/Knowledge_Graph.py`, `Self_Improvement/hosted_llm_adapter.py`, `Self_Improvement/Self_Improvement_Engine.py`, و`Self_Improvement/safe_self_mod.py`.

قائمة التحقق قبل تفعيل أي تعديل آلي أو تنفيذ شيفرة متولّدة:

- [ ] عمل نسخة احتياطية كاملة من المستودع (نسخة git أو أرشيف ZIP).
- [ ] تعطيل الشبكة للبيئة الاختبارية (network disabled أو firewall rules).
- [ ] ربط المستودع داخل الحاوية كـ read-only إلا لمسار `artifacts/` مخصص.
- [ ] الحد من موارد الحاوية (CPU, memory) وتحديد `no-new-privileges` و`cap_drop: ALL`.
- [ ] إضافة طبقة موافقة بشرية قبل أي عملية `apply_patch` أو عمليات كتابة ملفات/commit.
- [ ] تسجيل متكامل (audit) لجميع محاولات الكتابة أو استدعاءات subprocess، وتخزين السجلات في `/artifacts` فقط.
- [ ] إعداد آلية استرجاع (rollback) تلقائية: snapshot للـ repo أو استرجاع من git إذا فشلت عملية التعديل.
- [ ] مراجعة يدوية للكود المقترح للتعديل قبل التطبيق؛ رفض أي باتش يحتوي على `os.system(..., shell=True)` أو `subprocess.run(..., shell=True)` أو استدعاءات `exec`/`eval`.

تشغيل بيئة الاختبار (اقتراح سريع)

1) تأكد من تثبيت Docker و Docker Compose على الآلة المضيفة.
2) من جذر المشروع شغّل (PowerShell):

```powershell
Set-Location -Path 'd:\AGL\repo-copy'
docker compose -f docker-compose.self_improve.yml up -d --build
```

3) ادخل للحاوية للعمل التحقُّقي (البيئة بدون شبكة):

```powershell
docker exec -it agl_self_improve_sandbox /bin/sh
# داخل الحاوية يمكنك تشغيل فحوصات قراءة فقط، مثال:
# python -c "import re, sys; print('ok')"
```

نصائح تشغيل آمن داخل الحاوية (يدوي)

- شغّل فقط أوامر قراءة أو تحليلات static (grep, flake8, mypy) قبل أي تنفيذ.
- إن احتجت لتشغيل جزء من الشيفرة، قدّم نسخة مُحكَمَة من المدخلات واطلب من وحدة التحكم فقط إخراجاً إلى `/artifacts`.

مقترحات تقنية إضافية

- أضف حارسًا (gatekeeper) على دالة `apply_patch` بحيث تتطلب توقيعًا بشريًا وملف اعتماد قبل التطبيق.
- سجّل كل استدعاءات `subprocess.run` مع الحجة `shell` وتعرّف على أي استخدامات لـ `shell=True` وغيّرها أو احظرها.
- فكّر في استخدام sandboxed interpreter مثل `subprocess` إلى حاوية مخصصة أصغر أو استخدام أدوات مثل `nsjail` / `gVisor` لإجراء تنفيذ شيفرات قصيرة المدة.

ما الذي أوصي به الآن

- راجع يدوياً `Self_Improvement/Knowledge_Graph.py` و`hosted_llm_adapter.py` (تركيز على أي مكان يستخدم `subprocess` أو `apply_patch`).
- بعد الموافقة اليدوية، نفّذ تجربة عدمية (dry-run) داخل الحاوية وراجع `/artifacts` للسجلات.
- عند القبول، ضع بوابتَي موافقة بشرية قبل أي تطبيق باتش أو تعديل دائم.

إذا أردت، أستطيع الآن:

- فتح مقتطفات الكود من الملفات الخطرة التي وجدتُها (عرض أسطر بها الاستدعاءات الخطرة)،
- أو توليد سكربت صغير داخل `artifacts/` يقوم بجمع تقارير تفصيلية (ملف JSON) عن أماكن الاستدعاءات الخطرة.
