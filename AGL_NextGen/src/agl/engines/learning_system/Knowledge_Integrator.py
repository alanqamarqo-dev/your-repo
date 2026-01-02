# -*- coding: utf-8 -*-
from __future__ import annotations # type: ignore

import io, json, os, tempfile, shutil

def write_json_atomic(path, obj):
    d = os.path.dirname(path) or '.'
    os.makedirs(d, exist_ok=True)
    # Safety: if writing the canonical KB, ensure 'patterns' key exists and is a list
    try:
        if os.path.basename(path) == 'Learned_Patterns.json':
            if not isinstance(obj, dict) or 'patterns' not in obj or not isinstance(obj['patterns'], list):
                raise ValueError("Refusing to write KB: missing or invalid 'patterns' list")
    except Exception:
        # Raise to caller; do not attempt to write a bad KB
        raise
    fd, tmp = tempfile.mkstemp(prefix='.kb_', dir=d, text=True)
    try:
        # fd is an OS file descriptor; open a file object for writing
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(json.dumps(obj, ensure_ascii=False, indent=2))
        shutil.move(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
import os, json
from datetime import datetime, timezone


class KnowledgeIntegrator: # type: ignore
    """
    يدمج المعرفة الجديدة:
    - حفظ سجل التجارب في JSONL
    - تحديث agl_config.json (الأوزان/العتبات)
    """
    def __init__(self, base_dir:str = None): # type: ignore
        self.base_dir = base_dir or os.getcwd()
        self.data_dir = os.path.join(self.base_dir, "data")
        self.cfg_dir  = os.path.join(self.base_dir, "configs")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cfg_dir, exist_ok=True)
        self.cfg_path = os.path.join(self.cfg_dir, "agl_config.json")
        self.exp_path = os.path.join(self.data_dir, "experiences.jsonl")

    def _load_cfg(self) -> dict:
        if os.path.exists(self.cfg_path):
            with open(self.cfg_path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        return {"fusion_weights": {}, "confidence_gate": {"min_pass": 0.70, "target": 0.80}}

    def _save_cfg(self, cfg: dict):
        with open(self.cfg_path, "w", encoding="utf-8-sig") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

    def _append_experience(self, rec: dict):
        rec = dict(rec)
        rec["ts_iso"] = datetime.now(timezone.utc).isoformat()
        with open(self.exp_path, "a", encoding="utf-8-sig") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def integrate_new_knowledge(self, applied_plan_or_run: dict) -> dict:
        """
        إذا استقبل خطة تحسين: يحدّث الإعدادات.
        إذا استقبل سجل تشغيل: يحفظه كسطر JSONL.
        """
        if not isinstance(applied_plan_or_run, dict):
            raise TypeError("expected dict")

        if "fusion_weights" in applied_plan_or_run or "confidence_gate" in applied_plan_or_run:
            cfg = self._load_cfg()
            cfg.setdefault("fusion_weights", {})
            cfg["fusion_weights"].update(applied_plan_or_run.get("fusion_weights", {}))
            if "confidence_gate" in applied_plan_or_run:
                cfg.setdefault("confidence_gate", {})
                cfg["confidence_gate"].update(applied_plan_or_run["confidence_gate"])
            self._save_cfg(cfg)
            return {"action": "config_updated", "config": cfg}

        # otherwise treat as a run record and append
        self._append_experience(applied_plan_or_run)
        return {"action": "experience_logged", "path": self.exp_path}
