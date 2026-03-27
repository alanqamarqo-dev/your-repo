import os
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="AGL NextGen Command Center")

# Path to the state file updated by the ASI Pulse
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_FILE = os.path.join(PROJECT_ROOT, "dashboard_state.json")

# Mount static files
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api/state")
async def get_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"error": "Could not read state file"}
    return {"status": "Offline", "cycle": 0, "phi_score": 0.0}

if __name__ == "__main__":
    import uvicorn
    # Initial state creation
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({"cycle": 0, "status": "Waiting"}, f)
            
    print(f"🚀 AGL Dashboard starting at http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)
