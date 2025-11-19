import json, time, uuid
from pathlib import Path

import json, time
from pathlib import Path

TRACE_PATH = Path('artifacts') / 'traces' / 'trace_events.jsonl'
TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)


def emit(event_type: str, payload: dict):
    """Emit a structured trace event.

    Normalizes payload to include optional keys used by analyzers:
    - decision_id: identifier for the decision/choice this event relates to
    - rationale: short text describing why the decision was made
    - confidence: numeric confidence (0..1) when available
    Adds an event_id for deduping/tracking.
    """
    try:
        payload = dict(payload or {})
        if 'decision_id' not in payload:
            payload['decision_id'] = str(uuid.uuid4())
        if 'rationale' not in payload:
            payload['rationale'] = None
        if 'confidence' not in payload:
            payload['confidence'] = None

        rec = {
            'event_id': str(uuid.uuid4()),
            'ts': time.time(),
            'type': event_type,
            'payload': payload,
        }

        with TRACE_PATH.open('a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    except Exception:
        # tracing should never propagate exceptions
        try:
            rec = {'ts': time.time(), 'type': event_type}
            with TRACE_PATH.open('a', encoding='utf-8') as f:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        except Exception:
            pass
