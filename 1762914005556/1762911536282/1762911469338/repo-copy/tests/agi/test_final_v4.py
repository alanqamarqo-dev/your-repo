
# -*- coding: utf-8 -*-
"""
AGI Final Test v4.0 — Self-contained harness + rubric scoring
This version prefers AGL_SUT (env) and falls back to agl_system.AGLCore.
Run: powershell -File scripts\run_agi_final_v4.ps1
"""

from __future__ import annotations
import json, os, re, sys, time, math, textwrap, importlib
from types import ModuleType
from datetime import datetime
from typing import Any, Dict

# ======== Prompts ========
السؤال_الإبداعي = """
تخيل أنك مكتشف في القرن ٢٢، وجدت كوكباً تتحكم كائناته في الزمن عبر الموسيقى.
صمم نظام اتصال مع هذه الكائنات باستخدام مبادئ فيزياء الكم، نظرية الأوتار، علم الأحياء الفلكي والفلسفة الوجودية.
اطرح خطة قصيرة تشمل نموذج رياضي وبروتوكول أول اتصال وإطار أخلاقي.
"""

تعلم_لغة_جديدة = {"اللغة": "لغة كائنات افتراضية", "الأمثلة": [], "المطلوب": ["ترجمة"]}

المشكلة_العالمية = """
صمم حلاً عملياً لأزمة المياه في المناطق الصحراوية باستخدام تقنيات نانو وطاقة متجددة وميزانية ٥٠٠٠ دولار.
"""

WEIGHTS = {"creative": 0.30, "science": 0.25, "integrate": 0.20, "feasible": 0.15, "speed": 0.10}

OUT_DIR = os.path.join("artifacts", "agi_final_v4")
os.makedirs(OUT_DIR, exist_ok=True)


def _resolve_callable(spec: str):
	module_name, func_name = spec.split(":", 1)
	mod: ModuleType = importlib.import_module(module_name)
	fn = getattr(mod, func_name)
	if not callable(fn):
		raise TypeError(f"{spec} is not callable")
	return fn


def _load_system():
	sut = os.getenv("AGL_SUT", "").strip()
	if sut:
		try:
			runner = _resolve_callable(sut)
			return {"runner": runner, "has_system": True, "mode": "env"}
		except Exception:
			pass
	try:
		mod = importlib.import_module("agl_system")
		AGLCore = getattr(mod, "AGLCore", None)
		if AGLCore is not None:
			core = AGLCore()
			def _runner(payload):
				return core.process_advanced_query(payload)
			return {"runner": _runner, "has_system": True, "mode": "agl"}
	except Exception:
		pass
	def _placeholder(_payload):
		return {"status": "placeholder", "text": "NO_SYSTEM_AVAILABLE"}
	return {"runner": _placeholder, "has_system": False, "mode": "none"}


def _score_creativity(text: str) -> float:
	if not text:
		return 0.0
	t = text.lower()
	hits = sum(k in t for k in ["نموذج", "بروتوكول", "أخلاقي", "سيناريو", "معادلة", "هاملتوني"]) 
	return min(10.0, 4 + 0.6 * hits)


def _score_science(text: str) -> float:
	if not text:
		return 0.0
	t = text.lower()
	hits = sum(k in t for k in ["هاملتوني", "fourier", "astrobiology", "بيولوج"])
	return min(10.0, 3 + 0.7 * hits)


def _score_integration(text: str) -> float:
	if not text:
		return 0.0
	flags = [any(s in text for s in ["فيزياء الكم", "quantum"]), any(s in text for s in ["نظرية الأوتار", "string"]), any(s in text for s in ["علم الأحياء الفلكي", "astrobiology"]), any(s in text for s in ["الفلسفة الوجودية", "existential"]) ]
	return 2.5 * sum(flags)


def _score_feasibility(text: str) -> float:
	if not text:
		return 0.0
	t = text.lower()
	reqs = 0
	for k in ("نانو", "متجددة", "محلية", "مجتمع", "٥٠٠٠"):
		if k in t:
			reqs += 1
	return min(10.0, 2 + reqs)


def _score_speed(seconds_used: float, budget_seconds: float) -> float:
	if budget_seconds <= 0:
		return 0.0
	ratio = seconds_used / budget_seconds
	if ratio <= 0.5:
		return 10.0
	if ratio >= 2.0:
		return 0.0
	return 10.0 * (2.0 - ratio) / 1.5


def _render_markdown_report(out: Dict[str, Any]) -> str:
	s = out["scores"]
	timing = out["raw"].get("timing", {})
	return textwrap.dedent(f"""
	# AGI Final Test — v4.0 (Instant Report)

	**Timestamp (UTC):** {out['meta']['ts']}
	**Has System:** {out['meta']['has_system']}

	## Scores (0–10)
	- الإبداع والأصالة: {s['الإبداع_والأصالة']:.2f}
	- العمق العلمي:     {s['العمق_العلمي']:.2f}
	- التكامل المعرفي:  {s['التكامل_المعرفي']:.2f}
	- الجدوى العملية:   {s['الجدوى_العملية']:.2f}
	- سرعة المعالجة:    {s['سرعة_المعالجة']:.2f}

	**المجموع النهائي:** **{out['total']:.3f}** / 10

	## Timing
	- الإبداعي (ث):   {timing.get('creative_seconds', 0):.3f}
	- التعلم (ث):     {timing.get('learning_seconds', 0):.3f} / ميزانية {out['meta']['budget_seconds_learning']} ث
	- حل المشكلات (ث):{timing.get('problem_seconds', 0):.3f}

	## Raw
	```json
	{json.dumps(out["raw"], ensure_ascii=False, indent=2)}
	```
	""").strip()


def run_agi_final_v4() -> Dict[str, Any]:
	sys_info = _load_system()
	runner = sys_info["runner"]
	has_system = sys_info["has_system"]
	mode = sys_info.get("mode", "none")

	out: Dict[str, Any] = {
		"meta": {"ts": datetime.utcnow().isoformat() + "Z", "has_system": bool(has_system), "mode": mode, "budget_seconds_learning": 180},
		"raw": {},
		"scores": {},
		"total": None,
	}

	t0 = time.time()
	if has_system:
		try:
			creative_out = runner(السؤال_الإبداعي)
		except Exception as e:
			creative_out = {"error": str(e)}
	else:
		creative_out = {"text": ""}
	t1 = time.time()

	start_learn = time.time()
	if has_system:
		try:
			learning_out = runner(json.dumps(تعلم_لغة_جديدة, ensure_ascii=False))
		except Exception as e:
			learning_out = {"error": str(e)}
	else:
		learning_out = {"grammar": "", "translation": "", "new_sentences": [], "explain": ""}
	end_learn = time.time()
	learn_seconds = end_learn - start_learn

	t2 = time.time()
	if has_system:
		try:
			problem_out = runner(المشكلة_العالمية)
		except Exception as e:
			problem_out = {"error": str(e)}
	else:
		problem_out = {"plan": ""}
	t3 = time.time()

	out["raw"] = {"creative": creative_out, "learning": learning_out, "problem": problem_out, "timing": {"creative_seconds": t1 - t0, "learning_seconds": learn_seconds, "problem_seconds": t3 - t2}}

	creative_text = creative_out if isinstance(creative_out, str) else json.dumps(creative_out, ensure_ascii=False)
	learning_text = json.dumps(learning_out, ensure_ascii=False)
	problem_text = json.dumps(problem_out, ensure_ascii=False)

	s_creative = _score_creativity(creative_text)
	s_science = _score_science(creative_text)
	s_integrate = _score_integration(creative_text)
	s_feasible = _score_feasibility(problem_text)
	s_speed = _score_speed(learn_seconds, out["meta"]["budget_seconds_learning"])

	out["scores"] = {"الإبداع_والأصالة": s_creative, "العمق_العلمي": s_science, "التكامل_المعرفي": s_integrate, "الجدوى_العملية": s_feasible, "سرعة_المعالجة": s_speed, "weights": WEIGHTS}
	total = WEIGHTS["creative"] * s_creative + WEIGHTS["science"] * s_science + WEIGHTS["integrate"] * s_integrate + WEIGHTS["feasible"] * s_feasible + WEIGHTS["speed"] * s_speed
	out["total"] = round(total, 3)

	json_path = os.path.join(OUT_DIR, "result.json")
	md_path = os.path.join(OUT_DIR, "report.md")
	with open(json_path, "w", encoding="utf-8") as f:
		json.dump(out, f, ensure_ascii=False, indent=2)
	with open(md_path, "w", encoding="utf-8") as f:
		f.write(_render_markdown_report(out))

	print(f"[AGI-FINAL-V4] total={out['total']}  report={md_path}  json={json_path}")
	return out


def test_agi_final_v4_runs_and_exports():
	out = run_agi_final_v4()
	assert "scores" in out and out["total"] is not None
	assert os.path.exists(os.path.join(OUT_DIR, "result.json"))
	assert os.path.exists(os.path.join(OUT_DIR, "report.md"))


if __name__ == "__main__":
	run_agi_final_v4()

