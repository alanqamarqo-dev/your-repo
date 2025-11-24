# أوراق أُوامر AGL — إدارة لوحة التقارير

الملف يحتوي أوامر جاهزة لتشغيل وتجديد تقارير AGL وإجراء مهام شائعة. هناك نسخ PowerShell و Bash في نفس المجلد.

ملاحظة سريعة: قبل تشغيل أي أمر احرص على تفعيل البيئة الافتراضية (إن وُجِدت) أو استخدم مسار .venv\Scripts\python.exe على Windows.

## إعداد مرّة واحدة (PowerShell)

```powershell
# من جذر المشروع
$env:PYTHONIOENCODING = "utf-8"; $env:PYTHONPATH = (Get-Location).Path

# توليد كل التقارير/الملفات
.\.venv\Scripts\python.exe scripts\generate_all_reports.py
.\.venv\Scripts\python.exe scripts\make_models_report.py
.\.venv\Scripts\python.exe scripts\make_visual_report.py
.\.venv\Scripts\python.exe scripts\self_optimize.py --out reports\self_optimization
.\.venv\Scripts\python.exe -m scripts.safety_suite --out reports\safety_suite

# (اختياري) توليد مانيفست لتجميع التقارير
'{"html":["models_report.html","auto_reports/ohm_report.html","auto_reports/power_report.html","safety_suite/safety_report.html"],"json":["safety_suite/safety_report.json","self_optimization/self_optimization.json","last_success.json"]}' | Set-Content -Encoding utf8 reports\report_manifest.json

# تشغيل خادم بسيط
python -m http.server 8000

# افتح المتصفح على
# http://localhost:8000/reports/models_report.html
```

## إعداد مرّة واحدة (Bash)

```bash
export PYTHONIOENCODING=utf-8
export PYTHONPATH="$(pwd)"
python3 scripts/generate_all_reports.py
python3 scripts/make_models_report.py
python3 scripts/make_visual_report.py
python3 scripts/self_optimize.py --out reports/self_optimization
python3 -m scripts.safety_suite --out reports/safety_suite
printf '{"html":["models_report.html","auto_reports/ohm_report.html","auto_reports/power_report.html","safety_suite/safety_report.html"],"json":["safety_suite/safety_report.json","self_optimization/self_optimization.json","last_success.json"]}' > reports/report_manifest.json
python3 -m http.server 8000
# افتح: http://localhost:8000/reports/models_report.html
```

## أوامر شائعة سريعة

- عرض الأخطاء الحالية (سريع):
  - PowerShell: `Get-Content reports\safety_suite\safety_report.json`
  - Bash: `cat reports/safety_suite/safety_report.json`

- تصدير تقرير إلى PDF (Chrome headless):
  - مثال PowerShell:
    `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --print-to-pdf="reports\AGL_report.pdf" "http://localhost:8000/reports/models_report.html"`
  - Bash (قد يختلف المسار):
    `google-chrome --headless --disable-gpu --print-to-pdf="reports/AGL_report.pdf" "http://localhost:8000/reports/models_report.html"`

- تحديث التقارير بعد تدريب/تنظيف:
  - PowerShell:

    ```powershell
    .\.venv\Scripts\python.exe scripts\generate_all_reports.py
    .\.venv\Scripts\python.exe scripts\self_optimize.py --out reports\self_optimization
    .\.venv\Scripts\python.exe -m scripts.safety_suite --out reports\safety_suite
    ```

  - Bash:

    ```bash
    python3 scripts/generate_all_reports.py
    python3 scripts/self_optimize.py --out reports/self_optimization
    python3 -m scripts.safety_suite --out reports/safety_suite
    ```

- تحسين جودة بيانات power/freefall (Cook's Distance + إعادة تدريب):
  - PowerShell:

    ```powershell
    .\.venv\Scripts\python.exe tools\power_data_refine.py --in data\training\C_freefall_A.csv --x "s[m]" --y "t[s]" --out data\training\C_freefall_A_refined.csv
    .\.venv\Scripts\python.exe -m Learning_System.self_learning_cli --base power --data data\training\C_freefall_A_refined.csv --out artifacts\models\power_refined_A
    ```

  - Bash:

    ```bash
    python3 tools/power_data_refine.py --in data/training/C_freefall_A.csv --x "s[m]" --y "t[s]" --out data/training/C_freefall_A_refined.csv
    python3 -m Learning_System.self_learning_cli --base power --data data/training/C_freefall_A_refined.csv --out artifacts/models/power_refined_A
    ```

- فحص صحة النظام (كل الاختبارات):
  - PowerShell:
    `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v`
  - Bash:
    `python3 -m unittest discover -s tests -p "test_*.py" -v`

---

ملفات إضافية: يوجد ملف نصي PowerShell و Bash في نفس المجلد لتنفيذ الأوامر بسرعة.
