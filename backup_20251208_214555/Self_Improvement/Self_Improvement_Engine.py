"""Self-Improvement engine and lightweight SelfLearningManager (refactor).

This module provides a small, safe self-improvement engine along with a
lightweight, opt-in SelfLearningManager used for experimental learning runs.

Design goals:
"""

from __future__ import annotations

import os
import json
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# === [BEGIN ADDITION :: guided self-learning helpers] ===
import hashlib
from pathlib import Path


def _utcstamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _next_epoch():
    """Compute next epoch as max(existing epochs) + 1 (safe against malformed files)."""
    lc = Path("artifacts") / "learning_curve.json"
    if not lc.is_file():
        return 1
    try:
        arr = json.loads(lc.read_text(encoding="utf-8")) or []
        mx = 0
        for it in arr:
            try:
                mx = max(mx, int(it.get("epoch", 0)))
            except Exception:
                continue
        return mx + 1
    except Exception:
        return 1


def _ensure_dir(p: Path):
    try:
        p.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def load_events():
    """
    يقرأ events.jsonl من AGL_SELF_LEARNING_LOGDIR (إن وُجد) ويعيد قائمة أحداث.
    كل حدث: {"event": "...", "payload": {...}, "ts": "..."}
    يتسامح مع عدم وجود الملف أو أسطر تالفة.
    """
    logdir = os.getenv("AGL_SELF_LEARNING_LOGDIR", "").strip()
    if not logdir:
        return []
    fpath = Path(logdir) / "events.jsonl"
    if not fpath.is_file():
        return []
    out = []
    try:
        with fpath.open("r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rec = json.loads(ln)
                    out.append(rec)
                except Exception:
                    # تجاهل السطر التالف
                    continue
    except Exception:
        return []
    return out


def _weights_checksum(weights: dict) -> str:
    try:
        blob = json.dumps(weights, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]
    except Exception:
        return "na"


class _SimpleAdaptiveWeights:
    """
    مخزن أوزان داخلي بسيط (مفاتيح عامة من أحداث self-learning).
    يجري تحديثًا بأسلوب المتوسط المتحرّك: w <- (1-eta)*w + eta*reward
    """
    def __init__(self):
        self.weights = {}   # key -> float

    def update(self, key: str, reward: float, eta: float = 0.2):
        cur = float(self.weights.get(key, 0.5))
        new = (1.0 - eta) * cur + eta * float(reward)
        self.weights[key] = float(max(min(new, 1.0), 0.0))  # قص ضمن [0,1]

    def as_dict(self):
        return dict(self.weights)


def train_from_feedback(events, eta: float = None):
    """
    يحوّل أحداث record/improve إلى تعديلات على أوزان داخلية.
    يعيد (avg_reward, weights_dict) للاستخدام في حفظ اللقطة وتحديث منحنى التعلم.
    """
    if eta is None:
        try:
            eta = float(os.getenv("AGL_SELF_LEARNING_ETA", "0.2"))
        except Exception:
            eta = 0.2

    store = _SimpleAdaptiveWeights()
    rewards = []

    for e in events or []:
        try:
            etype = e.get("event")
            payload = e.get("payload", {})
            if etype == "record":
                key = str(payload.get("key", "")).strip()
                reward = payload.get("reward", None)
                if key and isinstance(reward, (int, float)):
                    store.update(key, float(reward), eta=eta)
                    rewards.append(float(reward))
            elif etype == "improve":
                # يمكن لاحقًا تفسير improve بطريقة مختلفة؛ الآن نمنح مكافأة+0.8 افتراضيًا إن لم يُحدد
                key = str(payload.get("key", "improve")).strip() or "improve"
                reward = float(payload.get("reward", 0.8))
                store.update(key, reward, eta=eta)
                rewards.append(reward)
        except Exception:
            # تجاهل حدث واحد سيء
            continue

    avg_reward = float(sum(rewards) / len(rewards)) if rewards else 0.0
    return avg_reward, store.as_dict()


def save_snapshot(state: dict):
    """
    يحفظ لقطة في artifacts/self_runs/<ts>.json
    """
    root = Path("artifacts")
    runs = root / "self_runs"
    if not _ensure_dir(runs):
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    fpath = runs / f"{ts}.json"
    try:
        with fpath.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return str(fpath)
    except Exception:
        return None


def _update_learning_curve(entry: dict):
    """
    يضيف سطرًا إلى artifacts/learning_curve.json
    """
    root = Path("artifacts")
    if not _ensure_dir(root):
        return
    fpath = root / "learning_curve.json"
    data = []
    if fpath.is_file():
        try:
            with fpath.open("r", encoding="utf-8") as f:
                data = json.load(f) or []
                if not isinstance(data, list):
                    data = []
        except Exception:
            data = []
    data.append(entry)
    try:
        with fpath.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# دمج مع SelfLearningManager الموجود
_SELF_LEARN_ENABLED = os.getenv("AGL_SELF_LEARNING_ENABLE", "0") == "1"
_SELF_LEARN_MODE = os.getenv("AGL_SELF_LEARNING_MODE", "offline")
_SELF_LEARN_DIR = os.getenv("AGL_SELF_LEARNING_LOGDIR", "")


class _EventLogger:
    def __init__(self, base_dir: str):
        self._enabled = bool(base_dir)
        self._path: Optional[str] = None
        self._lock = threading.Lock()
        if self._enabled:
            try:
                os.makedirs(base_dir, exist_ok=True)
                self._path = os.path.join(base_dir, "events.jsonl")
                with open(self._path, "a", encoding="utf-8"):
                    pass
            except Exception:
                self._enabled = False

    def log(self, event: str, payload: Optional[dict] = None) -> None:
        if not self._enabled or not self._path:
            return
        # compatible timestamp helper (fallback to ISO)
        def _utc_iso_local():
            return datetime.now(timezone.utc).isoformat()
        rec = {"ts": _utc_iso_local(), "event": event, "payload": payload or {}}
        line = json.dumps(rec, ensure_ascii=False)
        try:
            with self._lock:
                with open(self._path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
        except Exception:
            pass


_LOGGER: Optional[_EventLogger] = _EventLogger(_SELF_LEARN_DIR) if _SELF_LEARN_ENABLED and _SELF_LEARN_DIR else None
if _LOGGER:
    _LOGGER.log("module_loaded", {"module": "Self_Improvement_Engine"})

class SelfLearningManager:
    """Self-learning manager — minimal, testable, and opt-in persistence.

    This is a small, safe baseline implementation so the module provides a
    concrete `SelfLearningManager` even if no registry wiring is used.
    """
    def __init__(self, enable_persistence: bool = _SELF_LEARN_ENABLED) -> None:
        self.memory: Dict[str, float] = {}
        self.enable_persistence = bool(enable_persistence)

    def record(self, key: str, reward: float, note: Optional[str] = None) -> None:
        r = float(reward)
        self.memory[key] = max(self.memory.get(key, 0.0), r)
        if self.enable_persistence and _LOGGER:
            _LOGGER.log("record", {"key": key, "reward": r, "note": note})

    def improve(self, context: Optional[Dict[str, Any]] = None) -> bool:
        if self.enable_persistence and _LOGGER:
            _LOGGER.log("improve", {"context": context or {}, "mode": _SELF_LEARN_MODE})
        # safely no-op behavior for now
        return True

    def summarize(self) -> Dict[str, Any]:
        return {"items": len(self.memory), "max_reward": max(self.memory.values(), default=0.0)}

try:
    class SelfLearningManager(SelfLearningManager):  # يوسّع/يركّب على الموجود
        def run_training_epoch(self, eta: float = None):
            """
            دورة تدريب قصيرة محسّنة:
            - قراءة الأحداث
            - إن لم توجد أحداث: نتخطّى بلطف (بدون إدخالات فارغة)
            - تحديث الأوزان
            - حفظ لقطة + تحديث منحنى التعلم مع ترقيم عصور متصاعد
            """
            if os.getenv("AGL_SELF_LEARNING_ENABLE", "0") != "1":
                return {"ok": False, "reason": "SELF_LEARNING disabled"}

            events = load_events()
            if not events:
                # لا توجد أحداث: نتجنّب إنشاء إدخالات فارغة
                return {"ok": True, "skipped": "no_events"}

            avg_reward, weights = train_from_feedback(events, eta=eta)

            snapshot = {
                "ts": _utcstamp(),
                "avg_reward": avg_reward,
                "weights": weights,
            }
            path = save_snapshot(snapshot)

            # Compute next epoch robustly
            entry = {
                "ts": snapshot["ts"],
                "epoch": _next_epoch(),
                "avg_reward": avg_reward,
                "weights_checksum": _weights_checksum(weights),
            }
            _update_learning_curve(entry)

            return {
                "ok": True,
                "snapshot_path": path,
                "learning_curve_entry": entry,
            }
except NameError:
    # في حال لم تكن SelfLearningManager معرفة لسبب ما، نتجاهل التوسيع
    pass

# === [END ADDITION :: guided self-learning helpers] ===
 

# Compatibility shim: some tests and modules import `SelfImprovementEngine` from
# this module. Provide a safe alias backed by `SelfLearningManager` so imports
# succeed without changing behaviour. This is low-risk and reversible.
try:
    # Prefer exposing the concrete manager as the engine alias
    SelfImprovementEngine = SelfLearningManager
except NameError:
    # If for some reason SelfLearningManager isn't defined, provide a tiny
    # proxy that raises sensible AttributeError on access.
    class SelfImprovementEngine:
        """Compatibility shim for test importers expecting SelfImprovementEngine."""
        def __init__(self, *a, **kw):
            if 'SelfLearningManager' in globals():
                self._mgr = globals()['SelfLearningManager'](*a, **kw)
            else:
                self._mgr = None

        def __getattr__(self, name):
            if self._mgr is not None:
                return getattr(self._mgr, name)
            raise AttributeError(name)


    # === Phase-10: StrategicMemoryEngine (embedded here per user request — no new files) ===
    class StrategicMemoryEngine:
        """Selective strategic memory storing failure patterns and success strategies.

        Stored as a small JSON at `artifacts/strategic_memory.json`.
        """
        def __init__(self, path: str = None):
            self.path = path or os.getenv('AGL_STRATEGIC_MEMORY_PATH', 'artifacts/strategic_memory.json')
            self.state = {
                'patterns': [],
                'failures': [],
                'success_strategies': []
            }
            self._load()

        def _load(self):
            try:
                if os.path.exists(self.path):
                    with open(self.path, 'r', encoding='utf-8') as f:
                        self.state = json.load(f) or self.state
            except Exception:
                # tolerate malformed
                self.state = {'patterns': [], 'failures': [], 'success_strategies': []}

        def save(self):
            try:
                p = Path(self.path)
                p.parent.mkdir(parents=True, exist_ok=True)
                with p.open('w', encoding='utf-8') as f:
                    json.dump(self.state, f, ensure_ascii=False, indent=2)
                return True
            except Exception:
                return False

        def record_failure_pattern(self, info: dict):
            try:
                rec = dict(info or {})
                rec['ts'] = _utcstamp()
                self.state.setdefault('failures', []).append(rec)
                self.save()
            except Exception:
                pass

        def record_success_strategy(self, info: dict):
            try:
                rec = dict(info or {})
                rec['ts'] = _utcstamp()
                self.state.setdefault('success_strategies', []).append(rec)
                self.save()
            except Exception:
                pass

        def suggest_for(self, problem: dict) -> dict:
            # Lightweight hinting based on simple heuristics: if question words match previous failures,
            # suggest increased cot depth or enabling rag.
            out = {'recommended_cot_depth': 1, 'should_use_rag': False}
            try:
                q = (problem.get('question') or problem.get('title') or '') if isinstance(problem, dict) else str(problem)
                ql = str(q).lower()
                # if any recent failure mentions domain keywords, bump cot
                failures = self.state.get('failures', [])[-20:]
                for f in failures:
                    text = json.dumps(f, ensure_ascii=False) if not isinstance(f, dict) else ' '.join([str(v) for v in f.values()])
                    if any(w in text.lower() for w in ('medical','health','symptom','treatment','pharmacy')) and any(w in ql for w in ('دواء','علاج','أعراض','medical','symptom')):
                        out['recommended_cot_depth'] = max(out['recommended_cot_depth'], 2)
                        out['should_use_rag'] = True
                        break
            except Exception:
                pass
            return out


    # === Phase-11: ExecutiveAgent (task manager) ===
    from dataclasses import dataclass, field


    @dataclass
    class ExecTask:
        task_id: str
        goal: str
        status: str = "pending"
        created_at: float = field(default_factory=time.time)
        updated_at: float = field(default_factory=time.time)
        steps: List[Dict[str, Any]] = field(default_factory=list)
        meta: Dict[str, Any] = field(default_factory=dict)


    class ExecutiveAgent:
        """
        يدير المهام طويلة الأمد داخل AGL (مشاريع، تجارب، تقييمات).
        """

        def __init__(self, persist_path: Optional[str] = None):
            self.tasks: Dict[str, ExecTask] = {}
            self.persist_path = persist_path or os.getenv('AGL_EXECUTOR_TASKS_PATH', 'artifacts/executive_tasks.json')
            self._load()

        def _load(self):
            try:
                if os.path.exists(self.persist_path):
                    with open(self.persist_path, 'r', encoding='utf-8') as f:
                        arr = json.load(f) or []
                        for it in arr:
                            try:
                                t = ExecTask(**it)
                                self.tasks[t.task_id] = t
                            except Exception:
                                continue
            except Exception:
                pass

        def _save(self):
            try:
                p = Path(self.persist_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                arr = [dict(task_id=t.task_id, goal=t.goal, status=t.status, created_at=t.created_at, updated_at=t.updated_at, steps=t.steps, meta=t.meta) for t in self.tasks.values()]
                with p.open('w', encoding='utf-8') as f:
                    json.dump(arr, f, ensure_ascii=False, indent=2)
                return True
            except Exception:
                return False

        def register_task(self, task_id: str, goal: str, meta: Optional[Dict[str, Any]] = None) -> ExecTask:
            if task_id not in self.tasks:
                self.tasks[task_id] = ExecTask(task_id=task_id, goal=goal, meta=meta or {})
                self._save()
            return self.tasks[task_id]

        def update_task(self, task_id: str, status: Optional[str] = None,
                        note: Optional[str] = None, metrics: Optional[Dict[str, Any]] = None) -> Optional[ExecTask]:
            t = self.tasks.get(task_id)
            if not t:
                return None
            if status:
                t.status = status
            t.updated_at = time.time()
            step = {"ts": t.updated_at, "note": note or "", "metrics": metrics or {}}
            t.steps.append(step)
            self._save()
            return t

        def next_action(self, task_id: str, session_state: Dict[str, Any], strategic_hints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            t = self.tasks.get(task_id)
            if not t:
                return {"action": "noop"}

            hints = strategic_hints or {}
            used_engines = session_state.get("used_engines", []) if isinstance(session_state, dict) else []

            return {
                "action": "plan_next_query",
                "prefer_engines": hints.get("prefer_engines", []),
                "avoid_engines": hints.get("avoid_engines", []),
                "used_engines": used_engines,
            }


    # === Phase-12: SelfModel (meta self-assessment) ===
    class SelfModel:
        """
        نموذج ذاتي بسيط: يتتبع أداء النظام حسب المجال (domain).
        """
        def __init__(self):
            # domain -> {"success": int, "fail": int, "avg_score": float, "seen": int}
            self.stats: Dict[str, Dict[str, float]] = {}

        def _ensure_domain(self, domain: str):
            if domain not in self.stats:
                self.stats[domain] = {"success": 0, "fail": 0, "avg_score": 0.0, "seen": 0}

        def update(self, domain: str, score: float, threshold: float = 0.6):
            try:
                self._ensure_domain(domain)
                d = self.stats[domain]
                d["seen"] += 1
                if score >= threshold:
                    d["success"] += 1
                else:
                    d["fail"] += 1
                d["avg_score"] = ((d["avg_score"] * (d["seen"] - 1)) + float(score)) / d["seen"]
            except Exception:
                pass

        def reliability(self, domain: str) -> float:
            try:
                self._ensure_domain(domain)
                d = self.stats[domain]
                if d["seen"] == 0:
                    return 0.5
                return float(d["avg_score"])
            except Exception:
                return 0.5

        def suggest_mode(self, domain: str) -> str:
            r = self.reliability(domain)
            if r >= 0.75:
                return "fast"
            elif r >= 0.5:
                return "cot_short"
            elif r >= 0.3:
                return "cot_long"
            else:
                return "rag_heavy"


