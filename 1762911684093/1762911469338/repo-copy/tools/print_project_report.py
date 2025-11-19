# -*- coding: utf-8 -*-
"""
Print a detailed project report for the AGL workspace to the terminal.
This script is intended to be run from the repository root (d:\\AGL).
"""
import os
import json

report = r"""
تقرير مفصّل لمشروع AGL
======================
المسار الجذري: d:\AGL
الفرع الحالي: feat/new-engines

ملخص تنفيذي
------------
هذا المشروع هو منصة ذكاء اصطناعي متعددة المكوّنات تُدير محادثات، محركات نطاق (NLP, GK, Visual, ...)،
ومتكاملة مع مزود حقائق خارجي (ExternalInfoProvider) لاستخراج "حقائق" بشكل JSON فقط. تمَّ تنفيذ
آليات تحقق، كاش، حد يومي، عامل حصاد دوري (worker) يجلب حقائق من المزود ويخزن المقبول في KB،
مع طابور مراجعة للعناصر المتعارضة.

ملفّات ومجلدات رئيسية
----------------------
- server.py
  - واجهات: /chat, /health, /health/engines, /admin/external-info,
    /admin/external-info/clear, /harvest/status, /admin/harvest/review,
    /admin/harvest/review/clear
- web/index.html  (واجهة المستخدم)
- Core_Engines/
  - External_InfoProvider.py (جديد): مزوّد حقائق، parsing دفاعي، file-cache، daily quota
  - General_Knowledge.py: استدعاء المزود عند "no_evidence"، تحقق ثم upsert
  - GK_graph.py: upsert_facts يدعم dict-like facts ويمتلك edge_meta للحفظ provenance
  - GK_verifier.py: score_and_check و scan_graph
  - NLP_Advanced.py, Visual_Spatial.py, Creative_Innovation.py, ...
- Integration_Layer/
  - Conversation_Manager.py, Domain_Router.py, Output_Formatter.py, Intent_Recognizer.py
- workers/
  - knowledge_harvester.py (جديد): عامل دوري يجلب حقائق، يفلتر، upsert الآمن، يدفع التعارض للمراجعة
- configs/
  - agl_config.json (يحتوي على external_info_provider settings)
  - harvest_plan.yaml (خطة الحصاد، domains, seeds, target_facts, policy)
  - README.md (تعليمات تفعيل واختبار)
- artifacts/
  - external_info_cache/ (cache files + usage.json)
  - harvest_state.json
  - harvested_facts.jsonl
  - harvest_review.jsonl

آليات العمل والسلامة
-------------------
- لا نستخدم مخرجات LLM مباشرةً للرد للمستخدم؛ نأخذ حقائق JSON فقط.
- تمرُّ الحقائق عبر GKVerifier.score_and_check. فقط facts ذات confidence >= 0.7 ومصدر صالح تُقبل.
- تضارُب facts يُرسَل إلى artifacts/harvest_review.jsonl للمراجعة البشرية.
- ExternalInfoProvider يتعامل مع cache (SHA256 للسؤال+hints) وusage.json للحد اليومي.

التشغيل والاختبار
-----------------
أوامر سريعة (PowerShell):
1) ضبط المتغيرات البيئة:
   $env:OPENAI_API_KEY = 'sk-...'
   $env:AGL_EXTERNAL_INFO_ENABLED = '1'
2) تشغيل الخادم:
   .\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
3) probe /chat مثال:
   Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method POST -ContentType 'application/json' -Body (@{ session_id='ext_probe_1'; text='ما الفرق بين الانصهار والانشطار؟' } | ConvertTo-Json) | ConvertTo-Json -Depth 10
4) تشغيل العامل مرة واحدة:
   .\.venv\Scripts\python.exe .\workers\knowledge_harvester.py
5) واجهات إدارية:
   /admin/external-info
   /admin/external-info/clear
   /harvest/status
   /admin/harvest/review
   /admin/harvest/review/clear

اختبارات
--------
حُرِّكت الـunit tests بالكامل: النتائج الحالية بعد آخر تغييرات: 219 passed, 2 skipped

نقاط توسيع مقترحة
------------------
- واجهة مراجعة بشرية للـharvest_review.jsonl (قبول/رفض) مع provenance و audit trail.
- TTL للكاش ومؤشرات TTL invalidation.
- تكامل metrics (Prometheus) لمراقبة hits/misses/usage.

الخاتمة
-------
المشروع مُجهَّز لبناء KB تزايدي يعتمد ExternalInfoProvider كمزوّد حقائق فقط. هناك آليات
تحقيق ومراجعة تمنع إدخال معلومات خاطئة إلى KB دون إشراف. يمكنك الآن تشغيل الخادم والعامل
والتحقق عبر نقاط الإدارة المذكورة أعلاه.

"""

print(report)

# Additionally, print a short tree summary (top-level)
root = os.getcwd()
print("\n---\nTop-level files and directories:\n")
for name in sorted(os.listdir(root)):
    if name.startswith('.git'):
        continue
    print(name)

# Exit
print('\nتقرير مُنجز.')
