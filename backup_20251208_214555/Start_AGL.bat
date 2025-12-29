@echo off
TITLE AGL System Launcher
COLOR 0A

echo =====================================================
echo        AGL INTELLIGENCE SYSTEM - v1.0
echo        Advanced General Learning Core
echo =====================================================
echo.
echo [1/3] Activating Virtual Environment...
call D:\AGL\.venv\Scripts\activate.bat

echo [2/3] Starting FastAPI High-Performance Server...
echo.
echo    - API: http://127.0.0.1:8000/api/chat
echo    - UI:  http://127.0.0.1:8000/
echo.
echo    DO NOT CLOSE THIS WINDOW while using the system.
echo.

REM --- تشغيل المتصفح أولًا حتى يتاح الرابط قبل بدء الخادم ---
start "" "http://127.0.0.1:8000"

REM --- تشغيل السيرفر (تأكد من وجود server.py في نفس المجلد) ---
python server.py

pause
