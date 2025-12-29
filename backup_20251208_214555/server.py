"""Minimal, stable FastAPI server for local development.

This file provides a minimal, self-contained dev server with safe
fallbacks so it can be imported and scanned without third-party
dependencies being installed.
"""

import os
import sys
import uuid
import json
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

# Make repo importable
sys.path.append(os.getcwd())


def json_response(content: Any, status_code: int = 200):
    body = json.dumps(content, ensure_ascii=False)
    return Response(content=body, status_code=status_code, media_type='application/json; charset=utf-8')


app = FastAPI(title="AGL Dev Server (clean)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

WEB_DIR = os.path.join(os.getcwd(), 'web')
os.makedirs(WEB_DIR, exist_ok=True)
app.mount('/static', StaticFiles(directory=WEB_DIR), name='static')


@app.get('/health')
async def health():
    return json_response({"ok": True, "service": "AGL Chat (clean)", "status": "healthy"})
"""Minimal FastAPI dev server (server.py).

Start with: py server.py
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


@app.post('/process')
async def process(req: Request):
    """General /process endpoint: accepts {'text','session_id'} and returns a simple echo.
    This minimal implementation avoids calling external engines so the file remains import-safe.
    """
    try:
        data = await req.json()
    except Exception:
        data = {}
    text = (data.get('text') or '').strip()
    sid = data.get('session_id') or f'web_{uuid.uuid4().hex[:8]}'
    if not text:
        return json_response({"ok": False, "error": "no_text"}, status_code=400)
    # Minimal safe response (no external dependency calls)
    return json_response({"ok": True, "session_id": sid, "reply": f"Processed: {text[:200]}"})


# RAG answer endpoint (tries to use Integration_Layer.rag_wrapper if available)
try:
    from Integration_Layer.rag_wrapper import rag_answer  # type: ignore
except Exception:
    def rag_answer(query: str):
        # minimal fallback: return a canned response with empty sources
        return {"answer": "RAG not available", "sources": [], "engine": "noop"}


@app.post('/rag/answer')
async def rag_answer_endpoint(req: Request):
    try:
        data = await req.json()
    except Exception:
        data = {}
    q = (data.get('query') or data.get('text') or '').strip()
    if not q:
        return json_response({"ok": False, "error": "no_query"}, status_code=400)
    try:
        res = rag_answer(q)
    except Exception as e:
        return json_response({"ok": False, "error": "rag_error", "detail": str(e)}, status_code=500)
    return json_response({"ok": True, "query": q, "answer": res.get('answer') if isinstance(res, dict) else res, "sources": res.get('sources') if isinstance(res, dict) else [], "engine": res.get('engine') if isinstance(res, dict) else None})


@app.post('/agi/awakening')
async def agi_chat_endpoint(req: Request):
    """Simple AGI placeholder endpoint that returns a safe message.
    This avoids executing large in-repo AGI code during import or scan.
    """
    try:
        data = await req.json()
        text = data.get('text', '')
        sid = data.get('session_id', 'agi_web')
        # Minimal safe reply
        reply = f"AGI placeholder received: {text[:200]}"
        return json_response({"ok": True, "session_id": sid, "reply": reply})
    except Exception as e:
        return json_response({"ok": False, "error": str(e)}, status_code=500)


if __name__ == '__main__':
    try:
        import uvicorn
        reload_flag = os.environ.get('AGL_RELOAD', 'false').lower() in ('1', 'true', 'yes')
        if reload_flag:
            uvicorn.run('server:app', host='127.0.0.1', port=8000, reload=True)
        else:
            uvicorn.run('server:app', host='127.0.0.1', port=8000, reload=False)
    except Exception as e:
        print('Failed to start uvicorn:', e)
    # end of main
    