from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

app = FastAPI(title="AGL Web UI")

BASE = Path(__file__).resolve().parent
LOG_PATH = BASE / "repo-copy_test_run.log"


@app.get("/api/log")
async def get_log():
    if not LOG_PATH.exists():
        return PlainTextResponse("", status_code=200)
    try:
        text = LOG_PATH.read_text(encoding="utf-8", errors="ignore")
        # Return last ~1000 lines to keep payload small
        lines = text.splitlines()
        tail = "\n".join(lines[-1000:])
        return PlainTextResponse(tail, status_code=200)
    except Exception as e:
        return PlainTextResponse(f"Error reading log: {e}", status_code=500)


@app.get("/api/config")
async def get_config():
    keys = ["AGL_LLM_BASEURL", "AGL_LLM_MODEL", "AGL_LLM_TYPE", "AGL_HTTP_TIMEOUT", "AGL_LLM_ENDPOINT"]
    cfg = {k: os.getenv(k, "") for k in keys}
    return cfg


@app.get("/")
async def index():
    html_path = BASE / "web" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"), status_code=200)
    # fallback simple page
    return HTMLResponse(
        """
        <html><body>
        <h1>AGL Web UI</h1>
        <p>No UI installed. Please create `web/index.html` or run the Streamlit dashboard.</p>
        </body></html>
        """, status_code=200)


def mount_static(app: FastAPI):
    # serve /web static directory if present
    web_dir = BASE / "web"
    if web_dir.exists():
        app.mount("/web", StaticFiles(directory=str(web_dir)), name="web_static")


mount_static(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_ui:app", host="127.0.0.1", port=8080, reload=False)
