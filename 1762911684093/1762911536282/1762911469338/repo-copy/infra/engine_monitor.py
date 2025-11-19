import time
ENGINE_STATS = {}


def monitor_engine(fn):
    def wrapper(self, payload):
        name = getattr(self, "name", self.__class__.__name__)
        t0 = time.time()
        ok = True
        try:
            out = fn(self, payload)
            ok = bool(out.get("ok", True)) if isinstance(out, dict) else True
            return out
        finally:
            dt = (time.time() - t0) * 1000.0
            st = ENGINE_STATS.setdefault(name, {"calls": 0, "avg_ms": 0.0, "ok": 0, "fail": 0})
            st["calls"] += 1
            # incremental average
            st["avg_ms"] = (st["avg_ms"] * (st["calls"] - 1) + dt) / st["calls"]
            st["ok"] += 1 if ok else 0
            st["fail"] += 0 if ok else 1


def system_status():
    return {"ok": True, "engines": ENGINE_STATS}
