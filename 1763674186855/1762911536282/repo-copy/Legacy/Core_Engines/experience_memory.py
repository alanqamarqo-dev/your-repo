"""Legacy copy of Core_Engines.experience_memory

This file was moved to Legacy during cleanup. It contains the previous
implementation of the experience memory kept for historical/reference purposes.
"""

from __future__ import annotations

# Experience memory and micro-update scheduler.
#
# Stores before/after experiences for each run, computes simple metrics
# (RMSE, ECE, BIC when possible) and schedules micro-updates within
# a time/compute budget. This is intentionally conservative and local-only.

import json
import os
import time
import uuid
from math import log
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARTIFACTS_DIR = os.path.join(ROOT, "artifacts")
EXPERIENCE_PATH = os.path.join(ARTIFACTS_DIR, "experience_memory.json")
MICRO_UPDATES_PATH = os.path.join(ARTIFACTS_DIR, "micro_updates.json")

os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def _safe_load(path: str) -> List[Dict[str, Any]]:
	if not os.path.exists(path):
		return []
	try:
		with open(path, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		return []


def _safe_write(path: str, data: List[Dict[str, Any]]):
	tmp = path + ".tmp"
	with open(tmp, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)
	os.replace(tmp, path)


def _parse_first_number(text: Optional[str]) -> Optional[float]:
	if not text:
		return None
	import re

	m = re.search(r"[-+]?(?:\d+\.?\d*|\d*\.?\d+)(?:[eE][-+]?\d+)?", text)
	if not m:
		return None
	try:
		return float(m.group(0))
	except Exception:
		return None


class ExperienceMemory:
	def __init__(self, path: str = EXPERIENCE_PATH):
		self.path = path
		self._data = _safe_load(self.path)

	def append_experience(self, before: Dict[str, Any], after: Dict[str, Any], metrics: Dict[str, Any]):
		entry = {
			"id": str(uuid.uuid4()),
			"ts": int(time.time()),
			"before": before,
			"after": after,
			"metrics": metrics,
		}
		self._data.append(entry)
		_safe_write(self.path, self._data)
		return entry

	def all(self) -> List[Dict[str, Any]]:
		return list(self._data)


class MicroUpdateScheduler:
	"""Simple scheduler that records micro-updates and checks a budget.

	A 'micro-update' here is a small payload describing a planned improvement
	(e.g., a param delta or a golden example to add to a replay buffer).
	The scheduler stores planned updates and enforces a simple time/compute
	budget when scheduling.
	"""

	def __init__(self, path: str = MICRO_UPDATES_PATH, time_budget_sec: int = 3600, compute_budget: float = 100.0):
		self.path = path
		self.time_budget_sec = time_budget_sec
		self.compute_budget = compute_budget
		self._data = _safe_load(self.path)

	def remaining_budget(self) -> Dict[str, float]:
		# naive: subtract sum of scheduled est_time/est_compute from budgets
		used_time = sum([u.get("est_time_sec", 0) for u in self._data])
		used_compute = sum([u.get("est_compute", 0.0) for u in self._data])
		return {
			"time_sec": max(0, self.time_budget_sec - used_time),
			"compute": max(0.0, self.compute_budget - used_compute),
		}

	def schedule(self, payload: Dict[str, Any], est_time_sec: int = 60, est_compute: float = 1.0) -> Dict[str, Any]:
		rb = self.remaining_budget()
		if est_time_sec > rb["time_sec"] or est_compute > rb["compute"]:
			return {"ok": False, "error": "budget_exceeded", "remaining": rb}

		item = {
			"id": str(uuid.uuid4()),
			"ts": int(time.time()),
			"payload": payload,
			"est_time_sec": est_time_sec,
			"est_compute": est_compute,
			"state": "pending",
		}
		self._data.append(item)
		_safe_write(self.path, self._data)
		return {"ok": True, "item": item, "remaining": self.remaining_budget()}

	def all(self) -> List[Dict[str, Any]]:
		return list(self._data)


def compute_basic_metrics(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
	"""Attempt to compute RMSE, ECE, and a simple BIC where feasible.

	- RMSE: if ground truth present in before['query']['ground_truth'] or in tool outputs
	  and a numeric prediction appears in after['answer']['text'].
	- ECE: if confidence is present and correctness (boolean) provided.
	- BIC: computed only when a residuals list is provided in metrics; otherwise omitted.
	"""
	metrics: Dict[str, Any] = {}

	# RMSE attempt
	gt = None
	if isinstance(before.get("query", {}), dict):
		gt_raw = before["query"].get("ground_truth")
		if gt_raw is not None:
			try:
				gt = float(gt_raw)
			except Exception:
				gt = None

	# fallback: check tool outputs for an 'expected' numeric
	if gt is None:
		tlist = before.get("working", {}).get("calls", [])
		for t in tlist:
			out = t.get("out") or {}
			if isinstance(out, dict) and out.get("expected") is not None:
				val = out.get("expected")
				try:
					if val is not None:
						gt = float(val)
						break
				except Exception:
					gt = None

	pred = None
	try:
		pred = _parse_first_number(after.get("answer", {}).get("text", ""))
	except Exception:
		pred = None

	if gt is not None and pred is not None:
		rmse = ((pred - gt) ** 2) ** 0.5
		metrics["rmse"] = rmse

	# ECE (single-sample calibration): |confidence - label|
	conf = after.get("answer", {}).get("confidence")
	correct = None
	# if ground_truth present we can attempt to compare exact match (best-effort)
	if gt is not None and pred is not None:
		correct = abs(pred - gt) < 1e-6
	else:
		# if after includes an explicit 'correct' flag
		correct = after.get("metrics", {}).get("correct")

	if conf is not None and correct is not None:
		try:
			conf_f = float(conf)
			label = 1.0 if correct else 0.0
			metrics["ece"] = abs(conf_f - label)
		except Exception:
			pass

	# BIC: only if residuals list provided
	residuals = after.get("metrics", {}).get("residuals")
	if isinstance(residuals, list) and len(residuals) > 0:
		n = len(residuals)
		rss = sum([r * r for r in residuals])
		k = after.get("metrics", {}).get("model_params", 1)
		try:
			bic = k * log(n) + n * log(max(1e-12, rss / n))
			metrics["bic"] = bic
		except Exception:
			pass

	return metrics
