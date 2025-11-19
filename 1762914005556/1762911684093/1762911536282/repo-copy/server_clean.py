"""Minimal FastAPI dev server (server_clean.py).

Start with: py server_clean.py
"""
import os
import sys
import uuid
import json
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

sys.path.append(os.getcwd())

app = FastAPI(title="AGL Dev Server (clean)")


def json_response(content: Any, status_code: int = 200):
    body = json.dumps(content, ensure_ascii=False)
    return Response(content=body, status_code=status_code, media_type='application/json; charset=utf-8')

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

WEB_DIR = os.path.join(os.getcwd(), 'web')
os.makedirs(WEB_DIR, exist_ok=True)
app.mount('/static', StaticFiles(directory=WEB_DIR), name='static')


@app.get('/health')
async def health():
    return json_response({"ok": True, "service": "AGL Chat (clean)", "status": "healthy"})


@app.get('/')
async def index():
    path = os.path.join(WEB_DIR, 'index.html')
    if os.path.exists(path):
        return FileResponse(path, media_type='text/html')
    return json_response({"ok": False, "error": "index_missing"}, status_code=404)


@app.post('/chat')
async def chat(req: Request):
    try:
        data = await req.json()
    except Exception:
        data = {}
    text = (data.get('text') or '').strip()
    sid = data.get('session_id') or f'web_{uuid.uuid4().hex[:8]}'
    # lightweight fallback responder
    if not text:
        return json_response({"ok": True, "session_id": sid, "reply": "أرسل رسالة..."})
    reply = f"Echo: {text[:200]}"
    return json_response({"ok": True, "session_id": sid, "reply": reply})


if __name__ == '__main__':
    try:
        import uvicorn
        uvicorn.run('server_clean:app', host='127.0.0.1', port=8000, reload=False)
    except Exception as e:
        print('Failed to start uvicorn:', e)
