import io
import json
import os
from datetime import datetime

STATE_PATH = os.path.join(os.path.dirname(__file__), 'self_state.json')


def load_state(path: str = None, default=None): # type: ignore
    p = path or STATE_PATH
    if default is None:
        default = {"sessions": []}
    try:
        with io.open(p, 'r', encoding='utf-8-sig') as fh:
            return json.load(fh)
    except Exception:
        return default


def save_state(state: dict, path: str = None): # type: ignore
    p = path or STATE_PATH
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with io.open(p, 'w', encoding='utf-8-sig') as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2)
    except Exception:
        # best-effort
        pass


def record_run(summary: dict, path: str = None): # type: ignore
    """Append a run summary to self_state.json and update last_run timestamp.

    summary: dict containing at least keys like 'wins', 'fails', 'patterns'.
    """
    state = load_state(path)
    ts = datetime.utcnow().isoformat()
    state['last_run'] = ts # type: ignore
    entry = {'ts': ts, **(summary or {})}
    state.setdefault('sessions', []).append(entry)
    save_state(state, path)
    return state
