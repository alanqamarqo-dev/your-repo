"""Minimal Associative Graph adapter for Self_Improvement.

This module provides a tiny in-memory associative graph useful for tests
and demos. It's intentionally small, safe, and disabled by default unless
`AGL_ASSOC_GRAPH_ENABLE=1` is set. It is registered via the Integration
Registry under the key `associative_graph`.
"""
import os
import json
import hashlib
import importlib, sys, time
from agl.engines.self_improvement.Self_Improvement.continual_learning import load_learned_facts_as_context
try:
	from agl.engines.self_improvement.Self_Improvement.rag_index import retrieve_context
except Exception:
	def retrieve_context(q, k=5):
		return ""
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional, List as _List, Any as _Any


# === Phase-4 helpers: multi-step QA support ===
import time as _ptime


def extract_plain_answer(answer_field) -> str:
	"""
	ØªØ­Ø§ÙˆÙ„ Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø§Ù„Ù†Øµ Ø§Ù„Ø¹Ø±Ø¨ÙŠ Ø§Ù„ØµØ§ÙÙŠ Ù…Ù† answer_field
	Ø§Ù„Ø°ÙŠ Ù‚Ø¯ ÙŠÙƒÙˆÙ†:
	- dict ÙÙŠÙ‡ 'answer' Ø£Ùˆ 'response'
	- Ø³ØªØ±Ù†Ø¬ ÙŠØ­ØªÙˆÙŠ JSON
	- Ø£Ùˆ Ù†Øµ Ø¹Ø§Ø¯ÙŠ
	"""
	# 1) Ù„Ùˆ dict
	if isinstance(answer_field, dict):
		if "answer" in answer_field:
			return str(answer_field["answer"]).strip()
		if "response" in answer_field:
			return str(answer_field["response"]).strip()
		# try common keys
		for k in ("final", "text", "result", "summary"):
			if k in answer_field:
				return str(answer_field[k]).strip()
		return str(answer_field).strip()

	# 2) Ù„Ùˆ Ø³ØªØ±Ù†Ø¬
	text = str(answer_field).strip()

	# Ù„Ùˆ Ø´ÙƒÙ„Ù‡ JSON
	if text.startswith("{") and ("\"response\"" in text or "\"answer\"" in text):
		try:
			obj = json.loads(text)
			if "answer" in obj:
				return str(obj["answer"]).strip()
			if "response" in obj:
				return str(obj["response"]).strip()
		except Exception:
			pass

	# Ù…Ø­Ø§ÙˆÙ„Ø© Ø§Ù„ØªÙ‚Ø§Ø· Ø§Ù„Ù†Øµ Ø§Ù„Ø¹Ø±Ø¨ÙŠ Ù…Ù† stream Ø·ÙˆÙŠÙ„
	if "created_at" in text and "model" in text:
		parts = re.findall(r"[\u0600-\u06FF0-9\sØŒ\.\-]+", text)
		if parts:
			return " ".join(parts).strip()

	return text


def infer_task_type(question: str) -> str:
	"""
	Ø§Ø³ØªØ¯Ù„Ø§Ù„ Ø¨Ø³ÙŠØ·:
	- Ù„Ùˆ Ø§Ù„Ø³Ø¤Ø§Ù„ ÙÙŠÙ‡ 'Ù…Ù† Ø­ÙŠØ«' Ø£Ùˆ ':' ÙˆØ£ÙƒØ«Ø± Ù…Ù† ÙØ§ØµÙ„Ø© â†’ Ù†Ø¹ØªØ¨Ø±Ù‡ multi-step
	- ØºÙŠØ± Ø°Ù„Ùƒ â†’ qa_single
	"""
	q = (question or "").strip()
	# Ø¹Ù„Ø§Ù…Ø§Øª ØªØ¯Ù„ Ø¹Ù„Ù‰ ØªØ¹Ø¯Ø¯ Ø§Ù„Ù…Ø­Ø§ÙˆØ±
	multi_hints = ["Ù…Ù† Ø­ÙŠØ«", "Ø§Ù„ØªØ¹Ø±ÙŠÙ", "Ø§Ù„Ø£Ø³Ø¨Ø§Ø¨", "Ø§Ù„Ù…Ø¶Ø§Ø¹ÙØ§Øª", "Ø·Ø±Ù‚ Ø§Ù„ÙˆÙ‚Ø§ÙŠØ©", "Ø§Ù„Ø¹Ù„Ø§Ø¬"]
	score = 0
	for h in multi_hints:
		if h in q:
			score += 1

	if ":" in q:
		score += 1
	if "ØŒ" in q and q.count("ØŒ") >= 2:
		score += 1

	if score >= 2:
		return "qa_multi"
	return "qa_single"


def simple_step_split(question: str) -> _List[str]:
	"""
	ØªÙ‚Ø³ÙŠÙ… Ø¨Ø¯Ø§Ø¦ÙŠ Ù„Ù„Ø³Ø¤Ø§Ù„ Ø¥Ù„Ù‰ Ø®Ø·ÙˆØ§Øª ÙØ±Ø¹ÙŠØ© Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ ':' Ùˆ 'ØŒ' ÙˆØ¨Ø¹Ø¶ Ø§Ù„ÙƒÙ„Ù…Ø§Øª Ø§Ù„Ù…ÙØªØ§Ø­ÙŠØ©.
	"""
	q = question or ""
	# Ø¨Ø¹Ø¯ Ø§Ù„Ù†Ù‚Ø·ØªÙŠÙ† ØºØ§Ù„Ø¨Ù‹Ø§ ØªØ£ØªÙŠ Ø§Ù„Ù…Ø­Ø§ÙˆØ±: "Ù…Ù† Ø­ÙŠØ«: Ø§Ù„ØªØ¹Ø±ÙŠÙØŒ Ø§Ù„Ø£Ø³Ø¨Ø§Ø¨ØŒ Ø§Ù„Ù…Ø¶Ø§Ø¹ÙØ§ØªØŒ Ø§Ù„ÙˆÙ‚Ø§ÙŠØ©"
	if ":" in q:
		head, tail = q.split(":", 1)
	else:
		head, tail = "", q

	# ØªÙ‚Ø³ÙŠÙ… tail Ø¹Ù„Ù‰ Ø§Ù„ÙÙˆØ§ØµÙ„
	raw_parts = [p.strip() for p in re.split("ØŒ|,", tail) if p.strip()]

	steps: _List[str] = []
	for p in raw_parts:
		# Ù†Ø­Ø§ÙˆÙ„ ØªÙƒÙˆÙŠÙ† Ø®Ø·ÙˆØ© ÙˆØ§Ø¶Ø­Ø©
		if any(k in p for k in ["ØªØ¹Ø±ÙŠÙ", "Ø§Ù„ØªØ¹Ø±ÙŠÙ"]):
			steps.append(f"Ø§Ø´Ø±Ø­ ØªØ¹Ø±ÙŠÙ Ø§Ù„Ø­Ø§Ù„Ø© Ø§Ù„Ø·Ø¨ÙŠØ© Ø§Ù„Ù…Ø°ÙƒÙˆØ±Ø© ÙÙŠ Ø§Ù„Ø³Ø¤Ø§Ù„ Ø§Ù„Ø£ØµÙ„ÙŠ: {question}")
		elif any(k in p for k in ["Ø³Ø¨Ø¨", "Ø§Ù„Ø£Ø³Ø¨Ø§Ø¨"]):
			steps.append(f"Ø§Ø°ÙƒØ± Ø§Ù„Ø£Ø³Ø¨Ø§Ø¨ Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ© Ù„Ù„Ø­Ø§Ù„Ø© Ø§Ù„Ø·Ø¨ÙŠØ© Ø§Ù„Ù…Ø°ÙƒÙˆØ±Ø© ÙÙŠ Ø§Ù„Ø³Ø¤Ø§Ù„ Ø§Ù„Ø£ØµÙ„ÙŠ: {question}")
		elif any(k in p for k in ["Ù…Ø¶Ø§Ø¹ÙØ§Øª", "Ø§Ù„Ù…Ø¶Ø§Ø¹ÙØ§Øª"]):
			steps.append(f"Ø§Ø°ÙƒØ± Ø§Ù„Ù…Ø¶Ø§Ø¹ÙØ§Øª ÙˆØ§Ù„Ù…Ø®Ø§Ø·Ø± Ø§Ù„Ù…Ø­ØªÙ…Ù„Ø© Ù„Ù„Ø­Ø§Ù„Ø© Ø§Ù„Ø·Ø¨ÙŠØ© Ø§Ù„Ù…Ø°ÙƒÙˆØ±Ø© ÙÙŠ Ø§Ù„Ø³Ø¤Ø§Ù„ Ø§Ù„Ø£ØµÙ„ÙŠ: {question}")
		elif any(k in p for k in ["Ø§Ù„ÙˆÙ‚Ø§ÙŠØ©", "Ø§Ù„ÙˆÙ‚Ø§ÙŠÙ‡", "Ø·Ø±Ù‚ Ø§Ù„ÙˆÙ‚Ø§ÙŠØ©"]):
			steps.append(f"Ø§Ø´Ø±Ø­ Ø·Ø±Ù‚ Ø§Ù„ÙˆÙ‚Ø§ÙŠØ© Ù…Ù† Ø§Ù„Ø­Ø§Ù„Ø© Ø§Ù„Ø·Ø¨ÙŠØ© Ø§Ù„Ù…Ø°ÙƒÙˆØ±Ø© ÙÙŠ Ø§Ù„Ø³Ø¤Ø§Ù„ Ø§Ù„Ø£ØµÙ„ÙŠ: {question}")
		else:
			steps.append(f"Ø§Ø´Ø±Ø­ Ø§Ù„Ù…Ø­ÙˆØ± Ø§Ù„ØªØ§Ù„ÙŠ Ø§Ù„Ù…ØªØ¹Ù„Ù‚ Ø¨Ø§Ù„Ø³Ø¤Ø§Ù„ Ø§Ù„Ø£ØµÙ„ÙŠ: {p} â€“ ÙÙŠ Ø¶ÙˆØ¡ Ø§Ù„Ø³Ø¤Ø§Ù„: {question}")

	# Ù„Ùˆ Ù…Ø§ Ø·Ù„Ø¹ Ø´ÙŠØ¡ØŒ Ù†Ø±Ø¬Ø¹ Ø®Ø·ÙˆØ© ÙˆØ§Ø­Ø¯Ø© Ø¹Ù„Ù‰ Ø§Ù„Ø£Ù‚Ù„
	if not steps:
		steps.append(question)

	# Cap number of sub-steps to avoid explosion in multi-step pipelines.
	try:
		MAX_STEPS = int(os.getenv('AGL_MAX_STEP_SPLIT', '6'))
	except Exception:
		MAX_STEPS = 6
	if MAX_STEPS and len(steps) > MAX_STEPS:
		steps = steps[:MAX_STEPS]

	return steps

# === End Phase-4 helpers ===

# Optional emergency retrieval integration (non-fatal import)
try:
	from agl.engines.self_improvement.Self_Improvement.emergency_retrieval import EmergencyRetrieval
except Exception:
	EmergencyRetrieval = None


# small helpers used by memory/logging
def _utc():
	return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _jsave(path, data, append_jsonl=False):
	p = Path(path) if not isinstance(path, Path) else path
	p.parent.mkdir(parents=True, exist_ok=True)
	if append_jsonl:
		with p.open("a", encoding="utf-8") as f:
			f.write(json.dumps(data, ensure_ascii=False) + "\n")
	else:
		with p.open("w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)


class SessionState:
	"""Lightweight session state recorder stored in-memory and savable to artifacts.

	Kept here to avoid creating new files per user request.
	"""
	def __init__(self, session_id: str):
		self.session_id = session_id
		self.current_problem = None
		self.stage = None
		self.used_engines = []
		self.notes = []

	def to_dict(self):
		return {
			"session_id": self.session_id,
			"current_problem": self.current_problem,
			"stage": self.stage,
			"used_engines": list(self.used_engines),
			"notes": list(self.notes),
		}


def _save_session_state(session_state: SessionState, artifacts_root: str = "artifacts"):
	try:
		_ensure_dir(artifacts_root)
		path = Path(artifacts_root)/f"session_state_{session_state.session_id}.json"
		_write_json(path, session_state.to_dict())
		# also append a short jsonl entry for timeline
		_append_jsonl(str(Path(artifacts_root)/"session_states.jsonl"), {"ts": _ts(), "session_id": session_state.session_id, "stage": session_state.stage})
		return True
	except Exception:
		return False


def describe_session_state(session_state: SessionState) -> str:
	try:
		p = session_state.current_problem or {}
		title = p.get('title') or p.get('question') or ''
		engines = ', '.join(sorted(set(getattr(session_state, 'used_engines', []) or [])))
		return (
			f"Ø§Ù„Ù…Ù‡Ù…Ø© Ø§Ù„Ø­Ø§Ù„ÙŠØ©: {title}\n"
			f"Ø§Ù„Ù…Ø±Ø­Ù„Ø©: {getattr(session_state, 'stage', None)}\n"
			f"Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù…Ø© Ø­ØªÙ‰ Ø§Ù„Ø¢Ù†: {engines}"
		)
	except Exception:
		return "session_state:invalid"

# [BEGIN PATCH :: dynamic overrides]
def _append_jsonl(path, obj):
	try:
		os.makedirs(os.path.dirname(path), exist_ok=True)
		with open(path, "a", encoding="utf-8") as f:
			f.write(json.dumps(obj, ensure_ascii=False) + "\n")
	except Exception:
		pass

def _import_symbol(spec: str):
	"""
	spec Ø´ÙƒÙ„ Ù…Ù‚Ø¨ÙˆÙ„:
	  - "pkg.mod:ClassName"
	  - "pkg.mod#ClassName"
	ÙŠØ±Ø¬Ø¹ (cls, err) Ø­ÙŠØ« cls ØµÙ†Ù Ù‚Ø§Ø¨Ù„ Ù„Ù„Ø¥Ù†Ø´Ø§Ø¡ØŒ ÙˆØ¥Ù„Ø§ None Ù…Ø¹ Ù†Øµ Ø§Ù„Ø®Ø·Ø£.
	"""
	if not spec or not isinstance(spec, str):
		return None, "empty-spec"
	mod_name, sep, cls_name = spec.replace("#", ":").partition(":")
	if not sep or not mod_name or not cls_name:
		return None, f"bad-spec:{spec}"
	try:
		mod = importlib.import_module(mod_name)
	except Exception as e:
		return None, f"import-module-failed:{mod_name}:{repr(e)}"
	try:
		cls = getattr(mod, cls_name)
	except Exception as e:
		return None, f"getattr-failed:{mod_name}.{cls_name}:{repr(e)}"
	return cls, None

def _parse_engine_impls_env(env_val: str):
	"""
	ÙŠØ¯Ø¹Ù… Ø´ÙƒÙ„ÙŠÙ†:
	  1) JSON dict: {"planner":"pkg.mod:Class", "math":"x.y:Z"}
	  2) comma pairs: "planner=pkg.mod:Class, math=x.y:Z"
	ÙŠØ¹ÙŠØ¯ dict name -> spec
	"""
	if not env_val:
		return {}
	env_val = env_val.strip()
	# JSONØŸ
	if env_val.startswith("{"):
		try:
			data = json.loads(env_val)
			return {str(k).strip(): str(v).strip() for k, v in data.items()}
		except Exception:
			pass
	# pairs
	pairs = {}
	for part in env_val.split(","):
		part = part.strip()
		if not part:
			continue
		if "=" in part:
			k, v = part.split("=", 1)
			k, v = k.strip(), v.strip()
			if k and v:
				pairs[k] = v
	return pairs

def _load_overrides_from_env():
	raw = os.getenv("AGL_ENGINE_IMPLS", "").strip()
	mapping = _parse_engine_impls_env(raw)
	overrides = {}
	for name, spec in mapping.items():
		cls, err = _import_symbol(spec)
		if cls is None:
			_append_jsonl("artifacts/engine_impls_log.jsonl", {
				"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
				"event": "override_import_failed",
				"engine": name, "spec": spec, "error": err
			})
			continue
		try:
			inst = cls()  # Ù†ØªÙˆÙ‚Ù‘Ø¹ ØµÙ†Ù Adapter Ù…ØªÙˆØ§ÙÙ‚
			try:
				# mark instance as override for registry
				setattr(inst, "_impl", "override")
			except Exception:
				pass
			overrides[name] = inst
			_append_jsonl("artifacts/engine_impls_log.jsonl", {
				"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
				"event": "override_import_ok",
				"engine": name, "spec": spec, "impl_type": str(type(inst).__name__)
			})
		except Exception as e:
			_append_jsonl("artifacts/engine_impls_log.jsonl", {
				"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
				"event": "override_instantiate_failed",
				"engine": name, "spec": spec, "error": repr(e)
			})
	return overrides
# [END PATCH :: dynamic overrides]

# ==== Engine Capability Map (static bootstrap) ====
ENGINE_CAPABILITIES = {
	# core planning / analysis
	"planner": {"domains": ["planning", "strategy", "task_decomposition"], "kind": "symbolic"},
	"deliberation": {"domains": ["reasoning", "analysis", "tradeoffs"], "kind": "symbolic"},
	"analysis": {"domains": ["analysis", "logic", "language"], "kind": "llm"},
	"reason": {"domains": ["reasoning", "logic"], "kind": "llm"},
	"summarize": {"domains": ["language", "summarization"], "kind": "llm"},
	"translate": {"domains": ["language", "translation"], "kind": "llm"},
	# knowledge/retrieval
	"retriever": {"domains": ["knowledge", "retrieval", "facts"], "kind": "graph"},
	"GK_graph": {"domains": ["knowledge", "graph"], "kind": "graph"},
	"GK_reasoner": {"domains": ["knowledge", "reasoning"], "kind": "graph"},
	# math / proof
	"math": {"domains": ["math", "analysis"], "kind": "symbolic"},
	"proof": {"domains": ["math", "proof"], "kind": "symbolic"},
	# safety / policy
	"critic": {"domains": ["analysis", "qa", "review"], "kind": "symbolic"},
	"Law_Matcher": {"domains": ["law", "policy"], "kind": "symbolic"},
	# perception
	"vision": {"domains": ["perception", "vision"], "kind": "sensor"},
	"audio": {"domains": ["perception", "audio"], "kind": "sensor"},
	# meta
	"motivation": {"domains": ["meta", "reward"], "kind": "meta"},
	"timeline": {"domains": ["context", "temporal"], "kind": "meta"},
	# creativity
	"gen_creativity": {"domains": ["creativity", "meta"], "kind": "llm"},
	"hosted_storyqa": {"domains": ["language", "qa"], "kind": "llm"},
    "hosted_llm": {"domains": ["knowledge", "language", "qa", "general", "analysis", "reasoning"], "kind": "llm"},
}


def _infer_domains_from_name(n: str):
	k = (n or '').lower()
	if any(s in k for s in ("math","algebra","calc","optimiz")): return ("math","analysis")
	if any(s in k for s in ("proof","logic","verify","checker")): return ("reasoning","verification")
	if any(s in k for s in ("summar","translate","nlp","lang")):  return ("language","nlp")
	if any(s in k for s in ("vision","image","visual")):          return ("perception","visual")
	if any(s in k for s in ("audio","voice","speech")):           return ("perception","audio")
	if any(s in k for s in ("sensor","telemetry","signal")):      return ("perception","sensor")
	if any(s in k for s in ("plan","schedule","policy","design")):return ("planning","policy")
	if any(s in k for s in ("retriev","search","mapper","router")):return ("knowledge","routing")
	if any(s in k for s in ("critic","review","judge","safety","ethic","privacy","security")):
		return ("governance","safety")
	if any(s in k for s in ("gen_creativity","creative","story","idea")):
		return ("creativity","synthesis")
	return ("generic",)

def _score_engine_for_domains(name, domains_needed, health=None):
	"""Score an engine name by domain overlap and HealthMonitor snapshot."""
	caps = ENGINE_CAPABILITIES.get(name, {})
	eng_domains = set(caps.get("domains", []))
	needed = set(domains_needed or ())

	# domain match score
	if not needed:
		domain_score = 1.0
	else:
		overlap = len(eng_domains & needed)
		domain_score = overlap / max(len(needed), 1)

	# health score (0.1..1.0)
	health_score = 1.0
	if health is not None:
		try:
			snap = health.snapshot()
			eng_info = snap.get("engines", {}).get(name)
			if eng_info:
				calls = eng_info.get("calls", 0) or 0
				fails = eng_info.get("fails", 0) or 0
				avg_q = eng_info.get("avg_quality", 0.5)
				fail_rate = (fails / calls) if calls > 0 else 0.0
				health_score = max(0.1, float(avg_q) * (1.0 - float(fail_rate)))
		except Exception:
			health_score = 0.5

	# weighted combination
	return 0.7 * float(domain_score) + 0.3 * float(health_score)

def route_engines(all_available, domains_needed=None, health=None, top_k=None):
	"""Return ordered engine names selected from `all_available` using capability map and health."""
	scored = []
	for name in all_available:
		s = _score_engine_for_domains(name, domains_needed, health)
		scored.append((float(s), name))
	scored.sort(reverse=True)
	if top_k and isinstance(top_k, int) and top_k > 0:
		scored = scored[:top_k]
	return [n for s, n in scored if s > 0.0]


# ==== Stage-5: Embodied Perception (drop-in) ====
class PerceptionBus:
	def __init__(self):
		self.frames = []  # [{k:"vision|audio|sensor", x:<payload>, ts:<iso>}]

	def push(self, kind, payload, ts):
		try:
			self.frames.append({"k": str(kind), "x": payload, "ts": str(ts)})
		except Exception:
			pass

	def latest(self, kind):
		for fr in reversed(self.frames):
			try:
				if fr.get("k") == kind:
					return fr.get("x")
			except Exception:
				continue
		return None
# ================================================


class AssociativeGraph:
	"""Small in-memory associative graph used by tests/demos.

	Enabled via AGL_ASSOC_GRAPH_ENABLE=1. Lightweight API: add_edge, neighbors, find_associates.
	"""
	def __init__(self):
		self.enabled = os.getenv("AGL_ASSOC_GRAPH_ENABLE", "0") == "1"
		# node -> list of (neighbor, weight)
		self._edges: Dict[str, List[Tuple[str, float]]] = {}

	def add_edge(self, a: str, b: str, weight: float = 1.0) -> None:
		if not self.enabled:
			return
		self._edges.setdefault(a, [])
		self._edges[a].append((b, float(weight)))

	def neighbors(self, a: str) -> List[Tuple[str, float]]:
		return list(self._edges.get(a, []))

	def find_associates(self, seed: str, depth: int = 2) -> List[str]:
		if not self.enabled:
			return []
		seen = set()
		q = [seed]
		for _ in range(depth):
			next_q = []
			for n in q:
				for (nbr, _) in self._edges.get(n, []):
					if nbr not in seen:
						seen.add(nbr)
						next_q.append(nbr)
			q = next_q
		return list(seen)


class CollectiveMemorySystem:
	"""Ø°Ø§ÙƒØ±Ø© Ø¬Ù…Ø§Ø¹ÙŠØ© Ø¨Ø³ÙŠØ·Ø©: JSONL + Ø§Ø³ØªØ¹Ù„Ø§Ù… ÙÙ„ØªØ±Ø© Ù†ØµÙŠÙ‘Ø© Ø®ÙÙŠÙØ©."""
	def __init__(self):
		self.mem_path = Path("artifacts/collective_memory.jsonl")

	def share_learning(self, engine_name, learning_data, verified_by=None):
		entry = {
			"ts": _utc(),
			"source_engine": engine_name,
			"learning": learning_data,
			"verified_by": verified_by or [],
		}
		_jsave(self.mem_path, entry, append_jsonl=True)
		return entry

	def query_shared_memory(self, keywords=None, limit=20):
		if not self.mem_path.is_file():
			return []
		out = []
		with self.mem_path.open("r", encoding="utf-8") as f:
			for ln in f:
				try:
					rec = json.loads(ln)
				except Exception:
					continue
				if not keywords:
					out.append(rec)
				else:
					txt = json.dumps(rec, ensure_ascii=False)
					if all(str(k) in txt for k in keywords):
						out.append(rec)
				if len(out) >= limit:
					break
		return out

	def synthesize(self, records):
		"""Ø¯Ù…Ø¬ Ø¨Ø³ÙŠØ·: Ø¯Ù…Ø¬ Ù…ÙØ§Ù‡ÙŠÙ… ÙˆØªÙ„Ø®ÙŠØµ Ù†ØµÙŠ Ø³Ø±ÙŠØ¹."""
		if not records:
			return {"summary": "no-shared-knowledge", "concepts": []}
		concepts = []
		for r in records:
			learning = r.get("learning", {})
			if isinstance(learning, dict):
				concepts.extend(list(learning.keys()))
		concepts = sorted(set(concepts))
		return {"summary": f"synthesized-{len(records)}-items", "concepts": concepts}

class CognitiveIntegrationEngine:
	"""
	Ø±Ø¨Ø· Â«Ù…Ø­Ø±ÙƒØ§ØªÂ» Ù…ØªØ¹Ø¯Ù‘Ø¯Ø© Ø¹Ø¨Ø± Ø³Ø¬Ù„ Ø¨Ø³ÙŠØ· + Ø­Ø§ÙÙ„Ø© Ù…Ø¹Ø±ÙØ© + Ø³Ø¬Ù„ ØªØ¹Ø§ÙˆÙ†.
	Ø¥Ø°Ø§ ÙˆÙØ¬Ø¯ IntegrationRegistry ÙÙŠ Ø§Ù„Ù…Ù†Ø¸ÙˆÙ…Ø©ØŒ Ø³Ù†Ø­Ø§ÙˆÙ„ Ø§Ø³ØªØ¯Ø¹Ø§Ø¡Ù‡Ø› ÙˆØ¥Ù„Ø§ Ù†Ø¹Ù…Ù„ Ø¨ÙˆØ¶Ø¹ fallback.
	"""
	def __init__(self):
		self.engines_registry = {}      # name -> {capabilities, status, collaboration_score}
		self.knowledge_bus = []         # Ø±Ø³Ø§Ø¦Ù„ Ù‚ØµÙŠØ±Ø© Ø¨ÙŠÙ† Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª
		self.collaboration_log = Path("artifacts/collaboration_log.jsonl")
		self.collective = CollectiveMemorySystem()

	# --- Ø§ÙƒØªØ´Ø§Ù Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª ---
	def detect_available_engines(self):
		# Fallback: Ù…Ù† Ù…ØªØºÙŠØ± Ø¨ÙŠØ¦Ø© Ø£Ùˆ Ù‚Ø§Ø¦Ù…Ø© Ø§ÙØªØ±Ø§Ø¶ÙŠØ© ØµØºÙŠØ±Ø©
		env_list = os.getenv("AGL_ENGINES", "")
		if env_list.strip():
			return [x.strip() for x in env_list.split(",") if x.strip()]
		# Ù‚Ø§Ø¦Ù…Ø© Ø±Ù…Ø²ÙŠØ©Ø› Ø§Ø³ØªØ¨Ø¯Ù„Ù‡Ø§ Ù„Ø§Ø­Ù‚Ù‹Ø§ Ø¨Ù‚Ø±Ø§Ø¡Ø© Ø­Ù‚ÙŠÙ‚ÙŠØ© Ù…Ù† IntegrationRegistry Ø¥Ù† Ù…ØªØ§Ø­
		return ["planner", "deliberation", "emotion", "associative", "retriever", "self_learning"]

	def get_engine_capabilities(self, name):
		# ØªØ¹Ø±ÙŠÙ Ø¨Ø³ÙŠØ·Ø› ÙŠÙ…ÙƒÙ† Ø±Ø¨Ø·Ù‡ Ø¨Ù‚Ø§Ø¦Ù…Ø© Ù‚Ø¯Ø±Ø§Øª Ø­Ù‚ÙŠÙ‚ÙŠØ© Ù„Ø§Ø­Ù‚Ù‹Ø§
		base = {
			"planner": ["planning", "task_graph"],
			"deliberation": ["reasoning", "self_critique"],
			"emotion": ["affect", "tone_control"],
			"associative": ["analogy", "blend"],
			"retriever": ["semantic_search", "rerank"],
			"self_learning": ["feedback_log", "adaptive_weight"],
		}
		return base.get(name, ["generic"])

	def connect_engines(self):
		self.engines_registry.clear()
		for name in self.detect_available_engines():
			self.engines_registry[name] = {
				"capabilities": self.get_engine_capabilities(name),
				"status": "active",
				"collaboration_score": 0.0
			}
		return self.engines_registry

	# --- Ø§Ø®ØªÙŠØ§Ø± Ù…Ø­Ø±ÙƒØ§Øª Ø­Ø³Ø¨ Ù…Ø¬Ø§Ù„ ---
	def find_engines_for_domain(self, domain):
		got = []
		for n, meta in self.engines_registry.items():
			caps = meta.get("capabilities", [])
			if domain in caps or domain in n or domain in " ".join(caps):
				got.append(n)
		# fallback: Ø¥Ù† Ù„Ù… Ù†Ø¬Ø¯ØŒ Ø£Ø¹ÙØ¯ Ø¹Ø¯Ø© Ù…Ø­Ø±ÙƒØ§Øª Ø§ÙØªØ±Ø§Ø¶ÙŠÙ‹Ø§
		return got or list(self.engines_registry.keys())[:2]

	# --- Ø§Ø³ØªØ¯Ø¹Ø§Ø¡ Ù…Ø­Ø±Ùƒ ---
	def query_engine(self, engine_name, problem, context=None):
		"""
		Ø¥Ù† ÙƒØ§Ù† Ù…ÙˆØ¬ÙˆØ¯ IntegrationRegistry ÙØ­Ø§ÙˆÙ„ Ø§Ø³ØªØ¯Ø¹Ø§Ø¡ Ù…Ø­Ø±Ùƒ Ø¨Ø§Ù„Ø§Ø³Ù…Ø›
		ÙˆØ¥Ù„Ø§ Ù†ÙÙ†ØªØ¬ Ø§Ø³ØªØ¬Ø§Ø¨Ø© Ø±Ù…Ø²ÙŠØ© ØªØªØ¶Ù…Ù† Ø¨ØµÙ…Ø© + Ø³ÙŠØ§Ù‚.
		"""
		try:
			from Integration_Layer import Domain_Router as DR  # Ø¥Ù† ÙˆØ¬Ø¯
			if hasattr(DR, "IntegrationRegistry"):
				reg = getattr(DR, "IntegrationRegistry")
				if hasattr(reg, "get") and reg.get(engine_name):
					fn = reg.get(engine_name)
					return {
						"engine": engine_name,
						"ts": _utc(),
						"result": fn(problem, context=context)  # Ù‚Ø¯ ØªØªØ·Ù„Ø¨ ØªÙˆÙ‚ÙŠØ¹Ù‹Ø§ Ù…Ø®ØªÙ„ÙÙ‹Ø§
					}
		except Exception:
			pass
		# fallback
		payload = {
			"engine": engine_name,
			"ts": _utc(),
			"result": {
				"echo": str(problem)[:160],
				"hints": [f"used:{engine_name}", f"context_size:{len(context or [])}"]
			}
		}
		_jsave(self.collaboration_log, {"phase": "query", "payload": payload}, append_jsonl=True)
		return payload

	# --- Ø¯Ù…Ø¬ Ø­Ù„ÙˆÙ„ ---
	def integrate_solutions(self, solutions):
		blob = json.dumps(solutions, ensure_ascii=False)
		digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]
		merged = {
			"ts": _utc(),
			"solutions": solutions,
			"integration_id": digest,
			"policy": "simple-merge+uniquify"
		}
		_jsave(self.collaboration_log, {"phase": "integrate", "payload": {"integration_id": digest}}, append_jsonl=True)
		return merged

	def learn_from_collaboration(self, problem, solutions, integrated_solution):
		entry = {
			"problem": problem,
			"solutions_n": len(solutions),
			"integration_id": integrated_solution.get("integration_id"),
			"signals": {"diversity": len({s.get("engine") for s in solutions})}
		}
		return self.collective.share_learning("cognitive_integration", entry, verified_by=[])

	# --- ÙˆØ§Ø¬Ù‡Ø© Ø§Ù„Ø­Ù„ Ø§Ù„ØªØ¹Ø§ÙˆÙ†ÙŠ ---
	def collaborative_solve(self, problem, domains_needed):
		if not self.engines_registry:
			self.connect_engines()
		sols = []
		for dom in domains_needed:
			engines = self.find_engines_for_domain(dom)
			for en in engines:
				sols.append(self.query_engine(en, problem, context=sols))
		# create a stable integration id and log the collaboration
		integration_id = uuid.uuid4().hex[:12]
		integrated = self.integrate_solutions(sols)
		# log integration phase
		_jsave(self.collaboration_log, {"phase": "integrate", "payload": {"integration_id": integration_id, "solutions_n": len(sols)},}, append_jsonl=True)
		# write to collective memory
		self.collective.share_learning("cognitive_integration", {
			"problem": problem,
			"solutions_n": len(sols),
			"integration_id": integration_id,
			"signals": {"diversity": len(set([s.get("engine", "?") for s in sols]))}
		}, verified_by=[])
		# return concise result
		# return concise result
# === [END PATCH :: Knowledge_Graph.py] ===

# === [BEGIN :: Phase-3 extensions in Knowledge_Graph.py] ===
import os, json, uuid, math
from pathlib import Path
from datetime import datetime, timezone


def _ts():
	return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _ensure_dir(path):
	"""Create parent dir for a file path or directory Path-like.

	Accepts either a pathlib.Path or a string path to a file or directory.
	Returns True on success, False otherwise.
	"""
	try:
		# import here to avoid circular at top-level
		from pathlib import Path as _Path
		if isinstance(path, _Path):
			path.mkdir(parents=True, exist_ok=True)
			return True
		# assume string path to a file (ensure parent)
		d = os.path.dirname(str(path))
		if d:
			os.makedirs(d, exist_ok=True)
		return True
	except Exception:
		return False

def _write_json(path: Path, obj):
	try:
		_ensure_dir(path.parent)
		with path.open("w", encoding="utf-8") as f:
			json.dump(obj, f, ensure_ascii=False, indent=2)
		return True
	except Exception:
		return False

class KnowledgeNetwork:
	"""
	Ø´Ø¨ÙƒØ© Ù…Ø¹Ø±ÙØ© ØªØ±Ø¨Ø· Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª ÙˆØªØ³ØªÙ†ØªØ¬ Ø§Ù„Ù…Ø³Ø§Ø±Ø§Øª Ø§Ù„Ù…Ø«Ù„Ù‰ Ø¨ÙŠÙ† Ø§Ù„Ù‚Ø¯Ø±Ø§Øª (domains).
	- nodes: Ø£Ø³Ù…Ø§Ø¡ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª + Ù‚Ø¯Ø±Ø§ØªÙ‡Ø§
	- edges: Ø£ÙˆØ²Ø§Ù† (Ø­ÙÙ…Ù„/Ø¬ÙˆØ¯Ø©/Ø²Ù…Ù†) ØªÙØ­Ø¯Ù‘ÙŽØ« ÙˆÙÙ‚ Ø§Ù„Ø£Ø¯Ø§Ø¡
	"""
	def __init__(self):
		self.nodes = {}   # name -> {capabilities: [...], score: float}
		self.edges = {}   # (a,b) -> weight (Ø£Ù‚Ù„ Ø£ÙØ¶Ù„)
		self.metrics = {"updates": 0}

	def add_engine(self, name, capabilities, perf_score=0.5):
		self.nodes[name] = {"capabilities": list(capabilities), "score": float(perf_score)}

	def connect(self, a, b, weight=1.0):
		self.edges[(a,b)] = float(max(weight, 1e-6))

	def suggest_path(self, domains_needed):
		"""
		Ù…Ø³Ø§Ø± Ø¨Ø³ÙŠØ· greedy: ÙŠØ®ØªØ§Ø± Ù„ÙƒÙ„ domain Ø£ÙØ¶Ù„ Ù…Ø­Ø±Ùƒ (score/capability) Ù…Ø¹ ØªÙ‚Ù„ÙŠÙ„ Ø§Ù„ÙˆØ²Ù†.
		ÙŠÙ…ÙƒÙ† Ù„Ø§Ø­Ù‚Ø§Ù‹ Ø§Ø³ØªØ¨Ø¯Ø§Ù„Ù‡ Ø¨Ù€ Dijkstra/ILP. Ø§Ù„Ø¢Ù† Ø³Ø±ÙŠØ¹ ÙˆØ®ÙÙŠÙ.
		"""
		path = []
		used = set()
		for d in domains_needed:
			best = None; best_val = -1.0
			for n, info in self.nodes.items():
				if n in used: 
					continue
				if d in info["capabilities"]:
					val = info["score"] / (1.0 + sum(self.edges.get((n,x),1.0) for x in used))
					if val > best_val:
						best, best_val = n, val
			if best is not None:
				path.append({"domain": d, "engine": best, "score": round(best_val, 3)})
				used.add(best)
		return path

	def export(self, artifacts_root="artifacts"):
		graph = {
			"ts": _ts(),
			"nodes": self.nodes,
			"edges": {f"{a}->{b}": w for (a,b),w in self.edges.items()},
		}
		_write_json(Path(artifacts_root)/"knowledge_network_graph.json", graph)
		return graph

	def build_graph(self, engines_registry: dict):
		"""Build graph nodes/edges from a CognitiveIntegrationEngine.engines_registry mapping.
		Expects engines_registry: name -> {"capabilities": [...], "status":..., "collaboration_score": float}
		This is a lightweight heuristic builder used for smoke runs and tests.
		"""
		# clear existing
		self.nodes.clear(); self.edges.clear(); self.metrics["updates"] = 0
		# add nodes
		for name, meta in (engines_registry or {}).items():
			caps = meta.get("capabilities") or meta.get("domains") or []
			try:
				score = float(meta.get("collaboration_score", 0.5))
			except Exception:
				score = 0.5
			self.add_engine(name, caps, perf_score=score)
		# connect engines that share capabilities or adjacent in registry order
		names = list(engines_registry.keys())
		for i, a in enumerate(names):
			for j in range(i+1, min(i+4, len(names))):
				b = names[j]
				# weight lower when engines share capabilities
				caps_a = set((engines_registry.get(a) or {}).get("capabilities") or [])
				caps_b = set((engines_registry.get(b) or {}).get("capabilities") or [])
				shared = len(caps_a & caps_b)
				weight = 1.0 / (1 + shared)
				self.connect(a, b, weight=weight)
				self.metrics["updates"] += 1
		return {"nodes": list(self.nodes.keys()), "edges": len(self.edges)}

	def export_optimal_paths(self, domains_needed, artifacts_root="artifacts"):
		path = self.suggest_path(domains_needed)
		out = {"ts": _ts(), "domains": domains_needed, "path": path}
		_write_json(Path(artifacts_root)/"optimal_knowledge_paths.json", out)
		return out

class ConsensusVotingEngine:
	"""
	ØªØµÙˆÙŠØª/Ø¥Ø¬Ù…Ø§Ø¹ Ø¹Ù„Ù‰ Ø­Ù„ÙˆÙ„ Ù…ØªØ¹Ø¯Ø¯Ø©:
	- ÙŠÙ‚ÙŠÙ‘Ù… ÙƒÙ„ Ø­Ù„ (Ø¬ÙˆØ¯Ø©/ØªØºØ·ÙŠØ© Ø´Ø±ÙˆØ·/ØªØ¹Ù„ÙŠÙ„)
	- ÙŠØ±ØªÙ‘Ø¨ Ø§Ù„Ø­Ù„ÙˆÙ„ ÙˆÙŠØ¹ÙŠØ¯ Ø§Ù„Ù…Ø®ØªØ§Ø± + Ù…Ù„Ø®Øµ Ù…Ø¨Ø±Ø±Ø§Øª
	- ÙŠÙƒØªØ¨ Ù…Ù‚Ø§ÙŠÙŠØ³ Ø¬Ù…Ø§Ø¹ÙŠØ© Ø¥Ù„Ù‰ artifacts/collaborative_intelligence_metrics.json
	"""
	def __init__(self):
		self.history = []

	def score_proposal(self, proposal):
		# ØªÙˆÙ‚Ø¹ Ø´ÙƒÙ„: {"text":..., "checks": {"constraints": bool, "feasible": bool}, "rationale": "...", "novelty":0..1}
		c = proposal.get("checks", {})
		base = 0.0
		base += 0.5 if c.get("constraints") else 0.0
		base += 0.3 if c.get("feasible") else 0.0
		base += 0.2 * float(proposal.get("novelty", 0.5))
		return round(base, 3)

	def rank_and_select(self, proposals):
		scored = []
		for p in proposals:
			s = self.score_proposal(p)
			scored.append({"proposal": p, "score": s})
		scored.sort(key=lambda x: x["score"], reverse=True)
		top = scored[:3]
		winner = top[0] if top else None
		return {"winner": winner, "top": top, "n": len(proposals)}

	def aggregate_rationales(self, scored):
		lines = []
		for item in scored.get("top", []):
			r = item["proposal"].get("rationale","").strip()
			if r: lines.append(r)
		return " | ".join(lines[:5])

	def export_metrics(self, integration_id, scored, artifacts_root="artifacts"):
		payload = {
			"ts": _ts(),
			"integration_id": integration_id,
			"solutions_n": scored.get("n",0),
			"winner_score": (scored.get("winner") or {}).get("score"),
			"notes": self.aggregate_rationales(scored),
		}
		_write_json(Path(artifacts_root)/"collaborative_intelligence_metrics.json", payload)
		return payload

# ØªÙˆØ³ÙŠØ¹/ØªØ±Ù‚ÙŠØ© CognitiveIntegrationEngine Ø§Ù„Ø­Ø§Ù„ÙŠ (Ø¯ÙˆÙ† ÙƒØ³Ø± Ø§Ù„ÙˆØ§Ø¬Ù‡Ø©)
try:
	class CognitiveIntegrationEngine(CognitiveIntegrationEngine):  # type: ignore
		def __init__(self):
			super().__init__()
			self.kn = KnowledgeNetwork()
			self.voter = ConsensusVotingEngine()

		def connect_engines(self):
			# Ø§Ø³ØªØ¯Ø¹Ø§Ø¡ Ø§Ù„Ø£ØµÙ„ÙŠ
			super().connect_engines()
			# ØªØºØ°ÙŠØ© Ø§Ù„Ø´Ø¨ÙƒØ© Ø¨Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ù…ØªØ§Ø­Ø©
			for name, meta in getattr(self, "engines_registry", {}).items():
				caps = meta.get("capabilities", [])
				score = float(meta.get("collaboration_score", 0.6))
				self.kn.add_engine(name, caps, perf_score=score)
			# ÙˆØµÙ„ Ø§ÙØªØ±Ø§Ø¶ÙŠ Ø®ÙÙŠÙ (ÙŠÙ…ÙƒÙ† Ù„Ø§Ø­Ù‚Ø§Ù‹ Ø§Ù„ØªØ¹Ù„Ù… Ù…Ù† Ø§Ù„Ø³Ø¬Ù„)
			names = list(self.engines_registry.keys())
			for i in range(len(names)-1):
				self.kn.connect(names[i], names[i+1], weight=1.0)

		def collaborative_solve(self, problem, domains_needed):
			# Ø§Ù„Ù…Ø³Ø§Ø± Ø§Ù„Ø£ØµÙ„ÙŠ: ØªÙˆÙ„ÙŠØ¯ Ø­Ù„ÙˆÙ„ Ù…Ù† Ù…Ø­Ø±ÙƒØ§Øª Ù…ØªØ¹Ø¯Ø¯Ø©
			solutions_raw = []
			for d in domains_needed:
				engines = self.find_engines_for_domain(d)
				for eng in engines:
					sol = self.query_engine(eng, problem, context=solutions_raw)
					# ØªØ­ÙˆÙŠÙ„ Ø­Ù„ Ø£ÙˆÙ„ÙŠ Ø¥Ù„Ù‰ Ø§Ù‚ØªØ±Ø§Ø­ Ù…ÙÙ‚ÙŠÙ‘ÙŽÙ…
					proposal = {
						"text": str(sol),
						"checks": {"constraints": True, "feasible": True},
						"rationale": f"{eng} rationale for {d}",
						"novelty": 0.6,
					}
					solutions_raw.append(proposal)

			# 1) Ù…Ø³Ø§Ø± Ø£Ù…Ø«Ù„ Ø¹Ø¨Ø± Ø§Ù„Ø´Ø¨ÙƒØ©
			optimal = self.kn.export_optimal_paths(domains_needed)

			# 2) Ø¥Ø¬Ù…Ø§Ø¹/ØªØµÙˆÙŠØª
			ranked = self.voter.rank_and_select(solutions_raw)
			integration_id = uuid.uuid4().hex[:12]

			# 3) Ø­ÙØ¸ Ø§Ù„Ø³Ø¬Ù„Ø§Øª (Ù…ØªØ³Ù‚ Ù…Ø¹ Ù…Ø±Ø­Ù„ØªÙƒ 2)
			collog = Path("artifacts")/"collaboration_log.jsonl"
			memlog = Path("artifacts")/"collective_memory.jsonl"
			_ensure_dir(collog.parent)
			with collog.open("a", encoding="utf-8") as f:
				f.write(json.dumps({"phase":"integrate-advanced",
									"payload":{"integration_id":integration_id,
											   "optimal_path": optimal,
											   "top_n": min(3, ranked.get("n",0))},
									"ts": _ts()}, ensure_ascii=False) + "\n")
			with memlog.open("a", encoding="utf-8") as f:
				f.write(json.dumps({"ts": _ts(),
									"source_engine":"cognitive_integration",
									"learning":{"problem": problem,
												"solutions_n": ranked.get("n",0),
												"integration_id": integration_id,
												"signals":{"diversity": min(5, ranked.get("n",0))}},
									"verified_by":[]}, ensure_ascii=False) + "\n")

			# 4) ØªØµØ¯ÙŠØ± Ø§Ù„Ù…Ù‚Ø§ÙŠÙŠØ³ Ø§Ù„Ø¬Ù…Ø§Ø¹ÙŠØ©
			metrics = self.voter.export_metrics(integration_id, ranked)

			# 5) Ù†Ø¹ÙŠØ¯ Ù…ÙˆØ¬Ø²Ù‹Ø§ ØµØºÙŠØ±Ù‹Ø§ (Ù…ØªÙˆØ§ÙÙ‚ Ù…Ø¹ Ù…Ø§ Ø·Ø¨Ø¹ØªÙŽÙ‡ Ø³Ø§Ø¨Ù‚Ø§Ù‹)
			return {"integration_id": integration_id,
					"solutions": ranked.get("n",0),
					"winner_score": (ranked.get("winner") or {}).get("score"),
					"optimal_path_len": len(optimal.get("path", []))}
except NameError:
	pass
# === [END :: Phase-3 extensions] ===


# === [BEGIN PATCH :: Knowledge_Graph.py :: Multi-Engine Integration] ===
import time, threading
from queue import Queue, Empty

# Ø³Ø¬Ù„/Ù…Ù‚Ø§ÙŠÙŠØ³ Ø¨Ø³ÙŠØ·Ø© Ù…Ø¶Ø§ÙØ© Ù„Ù…Ø±Ø­Ù„Ø© 3
def _now_ms():
	return int(time.time() * 1000)

def _safe_float(x, default=0.0):
	try:
		return float(x)
	except Exception:
		return default


# --- env helpers for tunable parameters ---
def _env_float(name, default):
	try:
		return float(os.getenv(name, str(default)))
	except Exception:
		return default

def _env_int(name, default):
	try:
		return int(os.getenv(name, str(default)))
	except Exception:
		return default

# safer env helpers (override older behavior)

def _env_float(key: str, default: float) -> float:
	try:
		return float(os.getenv(key, "").strip() or default)
	except Exception:
		return default


def _env_int(key: str, default: int) -> int:
	try:
		return int(float(os.getenv(key, "").strip() or default))
	except Exception:
		return default


def _env(name: str, default: str = "") -> str:
	return os.getenv(name, default)


# FAST_MODE gate: when enabled, tests/benchmarks may avoid memory augmentation.
# Keep the flag available; do not forcibly disable global memory here so
# individual tests and components can opt-out when needed.
FAST_MODE = os.getenv("AGL_FAST_MODE", "0") == "1"

# Ø°Ø§ÙƒØ±Ø© Ù…ÙØ¹Ù‘Ù„Ø© Ø§ÙØªØ±Ø§Ø¶ÙŠÙ‹Ø§Ø› Ø¹Ø·Ù‘Ù„Ù‡Ø§ ÙÙŠ CI Ø¨Ù€ AGL_MEMORY_ENABLE=0
AGL_MEMORY_ENABLE = _env("AGL_MEMORY_ENABLE", "1")  # '1' Ø£Ùˆ '0'


# ---[ constants ]-------------------------------------------------------------
PERCEPTION_ENGINES = ("vision", "audio", "sensor")
CORE_META_ENGINES = ("perceptual_hub", "goal_engine", "motivation",
					 "timeline", "contextualizer")

# === [ADD :: Per-engine EMA priors] ===
_STATS_FILE = "artifacts/engine_stats.json"
def _load_engine_stats(path: str = None):
	p = path or _STATS_FILE
	try:
		with open(p, "r", encoding="utf-8") as f:
			return json.load(f) or {}
	except Exception:
		return {}


def _save_engine_stats(d, path: str = None):
	try:
		p = path or _STATS_FILE
		# ensure parent exists
		try:
			_ensure_dir(os.path.dirname(p) or ".")
		except Exception:
			pass
		with open(p, "w", encoding="utf-8") as f:
			json.dump(d, f, ensure_ascii=False, indent=2)
	except Exception:
		pass
# === [END] ===

# 1) ÙˆØ§Ø¬Ù‡Ø© Ù…Ø­ÙˆÙ„ Ù…ÙˆØ­Ù‘Ø¯Ø© Ù„Ù„Ù…Ø­Ø±Ù‘ÙƒØ§Øª
class EngineAdapter:
	name = "base"
	domains = ()  # tuple of domain tags it can handle

	def infer(self, problem: dict, context: list = None, timeout_s: float = 3.0):
		t0 = _now_ms()
		out = {
			"engine": self.name,
			"content": f"[echo] {problem.get('title','task')}",
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.5,
			"meta": {"latency_ms": _now_ms() - t0, "tokens": 0},
		}
		return out

# 2) Ø£Ù…Ø«Ù„Ø© Ù…Ø­ÙˆÙ‘Ù„Ø§Øª Ø¬Ø§Ù‡Ø²Ø© Ù„Ù„Ù…Ø­Ø±Ù‘ÙƒØ§Øª Ø§Ù„Ø´Ø§Ø¦Ø¹Ø©
class PlannerAdapter(EngineAdapter):
	name = "planner"; domains = ("planning","policy","engineering","science")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0 = _now_ms()
		outline = ["goals","constraints","phases","risks","milestones"]
		return {
			"engine": self.name,
			"content": {"plan_outline": outline, "hints":"planner coarse plan"},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.55,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

class DeliberationAdapter(EngineAdapter):
	name = "deliberation"; domains = ("reasoning","logic","analysis")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		pro_con = {"pros": ["path A","path B"], "cons": ["risk X","risk Y"]}
		return {
			"engine": self.name,
			"content": {"deliberation": pro_con},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.6,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

class RetrieverAdapter(EngineAdapter):
	name = "retriever"; domains = ("knowledge","search","context")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		return {
			"engine": self.name,
			"content": {"snippets": ["knw:signal_1","knw:signal_2"]},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.45,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}


class RAGAdapter(EngineAdapter):
	name = "rag"
	domains = ("knowledge", "retrieval")

	def infer(self, problem, context=None, timeout_s=2.0):
		t0 = _now_ms()
		try:
			q = problem.get('question') if isinstance(problem, dict) else str(problem)
			k = int(problem.get('rag_k', 5) or 5) if isinstance(problem, dict) else 5
			ctx = retrieve_context(q or '', k=k)
			return {
				"engine": self.name,
				"content": {"answer": ctx},
				"checks": {"constraints": True, "feasible": True},
				"novelty": 0.2,
				"meta": {"latency_ms": _now_ms() - t0, "tokens": 0},
				"domains": list(self.domains),
				"score": 0.4,
			}
		except Exception:
			return {"engine": self.name, "content": {"answer": ""}, "checks": {"constraints": True, "feasible": True}, "novelty": 0.1, "meta": {"latency_ms": _now_ms()-t0}, "domains": list(self.domains), "score": 0.1}

class AssociativeAdapter(EngineAdapter):
	name = "associative"; domains = ("creativity","synthesis","cross-domain")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		blends = ["analogy: biologyâ†’algorithms", "analogy: artâ†’design"]
		return {
			"engine": self.name,
			"content": {"analogies": blends},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.7,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

class EmotionAdapter(EngineAdapter):
	name = "emotion"; domains = ("psychology","ux","communication")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		return {
			"engine": self.name,
			"content": {"tone": "empathetic-analytical", "risk_of_bias": "low"},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.4,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

class SelfLearningAdapter(EngineAdapter):
	name = "self_learning"; domains = ("meta","adaptation")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		hints = {"learn": ["reward shaping", "constraint adherence"], "eta_hint": 0.3}
		return {
			"engine": self.name,
			"content": hints,
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.5,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

# === [ADD :: Extra adapters] ===
class MathAdapter(EngineAdapter):
	name = "math"; domains = ("math","science","proof")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		return {
			"engine": self.name,
			"content": {"sketch":"assumptionsâ†’lemmasâ†’result","hints":["use Banach/cvx/ODE if applicable"]},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.55,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

class ProofAdapter(EngineAdapter):
	name = "proof"; domains = ("proof","logic","math")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		return {
			"engine": self.name,
			"content": {"proof_style":"sketchâ†’rigorâ†’edge-cases"},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.58,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

class TranslateAdapter(EngineAdapter):
	name = "translate"; domains = ("language","nlp","translation")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		return {
			"engine": self.name,
			"content": {"ops":["meterâ†’ÙˆØ²Ù†","idiomsâ†’Ø«Ù‚Ø§ÙØ©","registerâ†’Ù…Ù‚ØµØ¯"]},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.46,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

class SummarizeAdapter(EngineAdapter):
	name = "summarize"; domains = ("analysis","language","nlp")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		bullets = ["context","key-points","risks","next-steps"]
		return {
			"engine": self.name,
			"content": {"summary": bullets},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.44,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

class CriticAdapter(EngineAdapter):
	name = "critic"; domains = ("analysis","qa","review")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		return {
			"engine": self.name,
			"content": {"review":["consistency","assumptions","bias","safety"]},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.52,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

class OptimizerAdapter(EngineAdapter):
	name = "optimizer"; domains = ("optimization","planning","policy","engineering")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		return {
			"engine": self.name,
			"content": {"multi_objective":"quality/latency/risk/cost","suggestion":"tune beams/thresholds"},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.57,
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}
# === [PATCH D1 :: Generative Creativity Adapter] ===
class GenerativeCreativityAdapter(EngineAdapter):
	name = "gen_creativity"; domains = ("creativity","synthesis","ideation")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		title = problem.get("title","new idea")
		ideas = [
			{"idea": "Design a cognitive lens that merges visual and abstract perception", "novelty": 0.82},
			{"idea": "Simulate social reasoning between independent engines", "novelty": 0.79},
			{"idea": "Develop an evolving ontology based on cooperative learning", "novelty": 0.85},
		]
		return {
			"engine": self.name,
			"content": {"ideas": ideas[:int(os.getenv('AGL_GCE_TOP','3') or '3')]},
			"checks": {"constraints": True, "feasible": True},
			"novelty": max(i.get("novelty",0.0) for i in ideas),
			"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
		}

# === [PATCH :: Perception shims] ===
class VisionAdapter(EngineAdapter):
	name = "vision"; domains = ("perception","visual")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0 = _now_ms()
		return {
			"engine": self.name,
			"content": {"detected": ["patterns","shapes","signals"]},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.6,
			"meta": {"latency_ms": _now_ms() - t0, "tokens": 0},
		}

class AudioAdapter(EngineAdapter):
	name = "audio"; domains = ("perception","auditory")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0 = _now_ms()
		return {
			"engine": self.name,
			"content": {"recognized": ["tone","speech","rhythm"]},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.5,
			"meta": {"latency_ms": _now_ms() - t0, "tokens": 0},
		}

class SensorAdapter(EngineAdapter):
	name = "sensor"; domains = ("perception","environment")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0 = _now_ms()
		return {
			"engine": self.name,
			"content": {"inputs": ["temperature","motion","pressure"]},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.4,
			"meta": {"latency_ms": _now_ms() - t0, "tokens": 0},
		}
# === [END PATCH] ===


# === [BEGIN PATCH :: Stage-2.0 :: Memory Loop + Perceptual Hub + Goal Engine] ===
import os, json, time

# 0) Ø£Ø¯ÙˆØ§Øª Ù…Ø³Ø§Ø¹Ø¯Ø© Ø¨Ø³ÙŠØ·Ø© Ù„ØªØ®Ø²ÙŠÙ†/Ù‚Ø±Ø§Ø¡Ø© Ø§Ù„Ø°Ø§ÙƒØ±Ø©
def _read_json(path, default):
	try:
		with open(path, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		return default

def _write_json(path, obj):
	try:
		_ensure_dir(path)
		with open(path, "w", encoding="utf-8") as f:
			json.dump(obj, f, ensure_ascii=False, indent=2)
	except Exception:
		pass

# 1) Ø­Ù„Ù‚Ø© Ø§Ù„Ø°Ø§ÙƒØ±Ø© (STM/LTM)
from dataclasses import dataclass, asdict


def _mem_root():
	return os.getenv("AGL_MEMORY_ROOT", "artifacts/memory")


@dataclass
class MemoryItem:
	ts: str
	task: dict
	winner: dict
	confidence: float
	features: dict


class MemorySystem:
	def __init__(self, root: str = None):
		self.root = os.path.abspath(root or _mem_root())
		# ensure the memory directory exists
		try:
			os.makedirs(self.root, exist_ok=True)
		except Exception:
			_ensure_dir(self.root)
		self.stm_path = os.path.join(self.root, "stm.json")
		self.ltm_path = os.path.join(self.root, "ltm.json")
		# ensure files exist
		for p in (self.stm_path, self.ltm_path):
			if not os.path.exists(p):
				with open(p, 'w', encoding='utf-8') as f:
					f.write('[]')
		# rotation and promotion params
		self.stm_max = int(os.getenv('AGL_STM_MAX', '128'))
		self.promote_min = float(os.getenv('AGL_LTM_PROMOTE_MIN', '0.15'))

	def write_stm(self, item):
		"""Append item to STM; accepts dataclass or dict. Rotates by stm_max."""
		try:
			if hasattr(item, '__dict__'):
				try:
					from dataclasses import asdict, is_dataclass
					if is_dataclass(item):
						item = asdict(item)
				except Exception:
					item = item.__dict__
			elif not isinstance(item, dict):
				item = {'value': item}
			stm = _read_json(self.stm_path, []) or []
			stm.append(item)
			# trim to max
			if isinstance(self.stm_max, int) and len(stm) > self.stm_max:
				stm = stm[-self.stm_max:]
			_write_json(self.stm_path, stm)
		except Exception:
			pass

		def consolidate_ltm(self):
			"""Promote high-confidence STM entries into LTM using promote_min."""
			try:
				stm = _read_json(self.stm_path, []) or []
				ltm = _read_json(self.ltm_path, []) or []
				promoted = []
				keep = []
				for it in stm:
					try:
						score = float(it.get('score', it.get('confidence', 0.0)))
						if score >= float(self.promote_min):
							promoted.append(it)
						else:
							keep.append(it)
					except Exception:
						keep.append(it)
				if promoted:
					ltm.extend(promoted)
					_write_json(self.ltm_path, ltm)
					_write_json(self.stm_path, keep)
				return {'promoted': len(promoted), 'ltm_size': len(ltm)}
			except Exception:
				return {'promoted': 0, 'ltm_size': 0}

	def recall(self, k: int = 5):
		stm = json.load(open(self.stm_path, "r", encoding="utf-8")) or []
		ltm = json.load(open(self.ltm_path, "r", encoding="utf-8")) or []
		return {"stm": list(reversed(stm))[:k], "ltm": list(reversed(ltm))[:k]}

# 2) Perceptual Hub: ÙŠØ¯Ù…Ø¬ vision/audio/sensor
class PerceptualIntegrationAdapter(EngineAdapter):
	name = "perceptual_hub"
	domains = ("perception", "fusion", "meta")

	def infer(self, q, context=None, timeout_s=2.5):
		seen = q.get('_percepts', {}) if isinstance(q, dict) else {}
		fused = {'signals': sorted(set(sum((seen.get(k, []) for k in ('vision','audio','sensor')), [])))}
		return {'engine': self.name, 'content': fused, 'checks': {'constraints': True, 'feasible': True},
				'novelty': 0.4, 'meta': {'latency_ms': 0, 'tokens': 0}, 'domains': self.domains}

# Compatibility alias: some parts of the codebase expect PerceptualHubAdapter
try:
	PerceptualHubAdapter = PerceptualIntegrationAdapter
except Exception:
	pass


class GoalAdapter(EngineAdapter):
	name = "goal_engine"
	domains = ("meta","planning","motivation")

	def infer(self, q, context=None, timeout_s=2.5):
		title = (q.get('title') if isinstance(q, dict) else 'task') or 'task'
		goal = f"Complete: {title.strip()}"
		return {'engine': self.name, 'content': {'goal': goal, 'feedback_hint': 0.1},
				'checks': {'constraints': True, 'feasible': True}, 'novelty': 0.35,
				'meta': {'latency_ms': 0, 'tokens': 0}, 'domains': self.domains}

# Ø³Ø¬Ù‘Ù„ Ø§Ù„Ù…Ø­ÙˆÙ„ÙŠÙ† Ø§Ù„Ø¬Ø¯Ø¯ (Ø³ÙŠØªÙ… Ø¯Ù…Ø¬Ù‡Ø§ Ù…Ø¹ Ø§Ù„Ù‚Ø§Ù…ÙˆØ³builtins Ù„Ø§Ø­Ù‚Ù‹Ø§)
_EXTRA_ADAPTERS = {
	'perceptual_hub': PerceptualIntegrationAdapter,
	'goal_engine': GoalAdapter,
}

# 4) Ø£Ø³Ù„Ø§Ùƒ CIE: Ø£Ø±Ø¨Ø· Ø§Ù„Ø°Ø§ÙƒØ±Ø© ÙˆHub Ø¯Ø§Ø®Ù„ Ø§Ù„ØªÙƒØ§Ù…Ù„
_old_init = getattr(CognitiveIntegrationEngine, "__init__", None)
def _cie_init_with_memory(self):
	if _old_init:
		_old_init(self)
	# create memory only if enabled (AGL_MEMORY_ENABLE)
	if AGL_MEMORY_ENABLE == "1":
		try:
			self.memory = MemorySystem(root=os.getenv("AGL_MEMORY_ROOT", "artifacts/memory"))
		except Exception:
			try:
				self.memory = MemoryLoop(root=os.getenv("AGL_MEMORY_ROOT", "artifacts/memory")) # type: ignore
			except Exception:
				self.memory = None
	else:
		self.memory = None
	# Ø§Ø¬Ø¹Ù„ Ø§Ù„Ù€ PerceptualHub ÙŠØ¹Ø±Ù Ø§Ù„Ù€ CIE (Ù„Ù„ÙˆØµÙˆÙ„ Ù„Ø§Ø­Ù‚Ù‹Ø§ Ø¹Ù†Ø¯ Ø§Ù„Ø­Ø§Ø¬Ø©)
	try:
		self.perceptual_hub = PerceptualHubAdapter(cie=self)
	except Exception:
		self.perceptual_hub = PerceptualHubAdapter()

CognitiveIntegrationEngine.__init__ = _cie_init_with_memory

# Ø£Ø¯Ø®Ù„ Ù†Ù‚Ø§Ø· ØªØ°ÙƒÙ‘Ø± ÙˆØªØ«Ø¨ÙŠØª Ø®ÙÙŠÙØ© Ø¯Ø§Ø®Ù„ collaborative_solve
_old_collab = CognitiveIntegrationEngine.collaborative_solve
def _collab_with_memory(self, problem: dict, domains_needed=()):
	res = _old_collab(self, problem, domains_needed)
	# 1) ØªØ°ÙƒÙ‘Ø± Ø§Ù„Ù…Ù„Ø®ØµØ§Øª Ø§Ù„ÙØ§Ø¦Ø²Ø© (STM)
	winner = res.get("winner") or {}
	if winner:
		try:
			if AGL_MEMORY_ENABLE == "1" and getattr(self, 'memory', None) is not None:
				mem = self.memory
				try:
					if hasattr(mem, 'write_stm'):
						mem.write_stm({"winner": winner.get("content"), "summary": f"win:{winner.get('engine')}", "score": winner.get("score", 0.0)})
					elif hasattr(mem, 'remember'):
						mem.remember({"content": winner.get("content"), "summary": f"win:{winner.get('engine')}", "score": winner.get("score", 0.0)})
				except Exception:
					pass
		except Exception:
			pass

	# 2) ØªØ±Ù‚ÙŠØ© Ø¥Ù„Ù‰ LTM Ù„Ùˆ Ù„Ø²Ù…
	try:
		if AGL_MEMORY_ENABLE == "1" and getattr(self, 'memory', None) is not None:
			try:
				mem = self.memory
				if hasattr(mem, 'consolidate_ltm'):
					mem.consolidate_ltm()
				elif hasattr(mem, 'consolidate'):
					mem.consolidate()
			except Exception:
				pass
	except Exception:
		pass

	# 3) Ø­Ù‚Ù† Hub Ù„Ø§Ø­Ù‚Ù‹Ø§: Ø¥Ø°Ø§ Ø±ØµØ¯Ù†Ø§ Ù…Ø®Ø±Ø¬Ø§Øª vision/audio/sensor Ø¶Ù…Ù† top ÙˆÙ„Ù… ÙŠÙˆØ¬Ø¯ hub ÙÙŠ topâ€”Ø£Ø¹Ø¯ Ø¥Ø¯Ø®Ø§Ù„ hub Ù„ØªØ¹Ø²ÙŠØ² Ø§Ù„Ø¯Ù…Ø¬
	names_top = [t.get("engine") for t in res.get("top", [])]
	if any(n in names_top for n in ("vision","audio","sensor")) and "perceptual_hub" not in names_top:
		try:
			hub_prop = self.perceptual_hub.infer(problem, context=res.get("top", []))
			hub_prop["novelty"] = max(hub_prop.get("novelty",0.6), 0.62)
			scored = self._consensus_score(res.get("top", []) + [hub_prop])
			res["top"] = scored[:5]
			res["winner"] = scored[0]
		except Exception:
			pass
	return res

CognitiveIntegrationEngine.collaborative_solve = _collab_with_memory
# === [END PATCH] ===


# Ø³Ø¬Ù„Ù‘Ù‡ ÙÙŠ Ø§Ù„Ø¨ÙÙ„Øª-Ø¥Ù†
# registration moved below after _BUILTIN_ADAPTERS is defined
# === [END PATCH D1] ===
# === [END :: Extra adapters] ===

# 3) Ø³Ø¬Ù„ Ù…Ø­ÙˆÙ„Ø§Øªâ€”ÙˆØ£Ø¯Ø§Ø© Ø§ÙƒØªØ´Ø§Ù Ù…Ù† AGL_ENGINES
_BUILTIN_ADAPTERS = {
	"planner": PlannerAdapter,
	"deliberation": DeliberationAdapter,
	"retriever": RetrieverAdapter,
	"associative": AssociativeAdapter,
	"emotion": EmotionAdapter,
	"self_learning": SelfLearningAdapter,
	# perception shims
	"vision": VisionAdapter,
	"audio": AudioAdapter,
	"sensor": SensorAdapter,
}

# register rag adapter
try:
    _BUILTIN_ADAPTERS["rag"] = RAGAdapter
except Exception:
    pass

def _register_extra_adapters():
	global _BUILTIN_ADAPTERS, _EXTRA_ADAPTERS
	try:
		if "_BUILTIN_ADAPTERS" in globals() and _EXTRA_ADAPTERS:
			_BUILTIN_ADAPTERS.update(_EXTRA_ADAPTERS)
	except Exception:
		pass

# Ø¯Ù…Ø¬ Ø£ÙŠ Ù…Ø­ÙˆÙ„Ø§Øª Ø¥Ø¶Ø§ÙÙŠØ© Ù…ÙØ¬Ù…Ø¹Ø© Ø³Ø§Ø¨Ù‚Ù‹Ø§
_register_extra_adapters()

# register generative creativity adapter if present
try:
    _BUILTIN_ADAPTERS["gen_creativity"] = GenerativeCreativityAdapter
except Exception:
    pass

def discover_engines_from_env():
	raw = os.getenv("AGL_ENGINES","" ).strip()
	names = [n.strip() for n in raw.split(",") if n.strip()]

	# NEW: ØªØ­Ù…ÙŠÙ„ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø­Ù‚ÙŠÙ‚ÙŠØ© Ù…Ù† Ø§Ù„Ø¨ÙŠØ¦Ø©
	overrides = _load_overrides_from_env()  # name -> instance

	# === [BEGIN PATCH :: Unknown-Engine Auto-Shim] ===
	# Shim Ø¹Ø§Ù… Ù„Ø£Ø³Ù…Ø§Ø¡ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª ØºÙŠØ± Ø§Ù„Ù…Ø¹Ø±Ù‘ÙØ© Ù…Ø³Ø¨Ù‚Ù‹Ø§
	class _DefaultShimAdapter(EngineAdapter):
		def __init__(self, dyn_name: str, dyn_domains=()):
			self.name = dyn_name
			self.domains = tuple(dyn_domains) or ("generic",)

		def infer(self, problem, context=None, timeout_s=3.0):
			t0 = _now_ms()
			return {
				"engine": self.name,
				"content": {"hint": f"{self.name} shim response"},
				"checks": {"constraints": True, "feasible": True},
				"novelty": 0.5,
				"meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
			}

	# Ù…Ø³Ø§Ø¹Ø¯ Ø¨Ø³ÙŠØ· Ù„Ø§Ø³ØªÙ†ØªØ§Ø¬ Ù†Ø·Ø§Ù‚Ø§Øª Ù…Ù† Ø§Ù„Ø§Ø³Ù…
	def _infer_domains_from_name(n: str):
		k = n.lower()
		if any(s in k for s in ("math","algebra","calc","optimiz")): return ("math","analysis")
		if any(s in k for s in ("proof","logic","verify","checker")): return ("reasoning","verification")
		if any(s in k for s in ("summar","translate","nlp","lang")):  return ("language","nlp")
		if any(s in k for s in ("vision","image","visual")):          return ("perception","visual")
		if any(s in k for s in ("audio","voice","speech")):           return ("perception","audio")
		if any(s in k for s in ("sensor","telemetry","signal")):      return ("perception","sensor")
		if any(s in k for s in ("plan","schedule","policy","design")):return ("planning","policy")
		if any(s in k for s in ("retriev","search","mapper","router")):return ("knowledge","routing")
		if any(s in k for s in ("critic","review","judge","safety","ethic","privacy","security")):
			return ("governance","safety")
		if any(s in k for s in ("gen_creativity","creative","story","idea")):
			return ("creativity","synthesis")
		return ("generic",)

	# Ø¹Ø¯Ù‘Ù„ Ø§Ù„Ø§ÙƒØªØ´Ø§Ù Ù„ÙŠÙ‚Ø¨Ù„ Ø§Ù„Ø´ÙÙ…Ø² Ø§Ù„ØªÙ„Ù‚Ø§Ø¦ÙŠ Ø¹Ù†Ø¯ ØªÙØ¹ÙŠÙ„ Ø§Ù„Ø¹Ù„Ù… AGL_ALLOW_UNKNOWN_SHIMS=1
	allow_unknown = os.getenv("AGL_ALLOW_UNKNOWN_SHIMS","0") == "1"

	adapters = []
	for n in names:
		# 1) Override Ø¯ÙŠÙ†Ø§Ù…ÙŠÙƒÙŠ (Ø§Ù„Ø£ÙˆÙ„ÙˆÙŠØ©)
		inst = overrides.get(n)
		if inst is not None:
			adapters.append(inst)
			continue
		# 2) Built-in Ø¥Ù† ÙˆÙØ¬Ø¯
		cls = _BUILTIN_ADAPTERS.get(n)
		if cls is not None:
			try:
				adapters.append(cls())
				continue
			except Exception:
				pass
		# 3) Shim ØªÙ„Ù‚Ø§Ø¦ÙŠ Ù„Ù„Ø£Ø³Ù…Ø§Ø¡ ØºÙŠØ± Ø§Ù„Ù…Ø¹Ø±ÙˆÙØ© (Ø§Ø®ØªÙŠØ§Ø±ÙŠ)
		if allow_unknown:
			try:
				adapters.append(_DefaultShimAdapter(n, _infer_domains_from_name(n)))
			except Exception:
				pass

	return adapters
	# === [END PATCH] ===

# === [PATCH :: Knowledge_Graph.py :: unify diversity + helper API] ===
# Ø§Ø¬Ø¹Ù„ Ù‡Ø°Ù‡ helpers Ø£Ø¹Ù„Ù‰ Ø§Ù„Ù…Ù„Ù Ø¥Ù† Ù„Ù… ØªÙƒÙ† Ù…ÙˆØ¬ÙˆØ¯Ø©
def _env_float(key: str, default: float) -> float:
	try:
		return float(os.getenv(key, "").strip() or default)
	except Exception:
		return default

def _env_int(key: str, default: int) -> int:
	try:
		return int(float(os.getenv(key, "").strip() or default))
	except Exception:
		return default

# === [END PATCH] ===

# 4) ØªÙˆØ³ÙŠØ¹ CognitiveIntegrationEngine Ù„Ø¯Ø¹Ù… Ø§Ù„ÙƒØ«ÙŠØ± Ù…Ù† Ø§Ù„Ù…Ø­Ø±Ù‘ÙƒØ§Øª Ø¨Ø§Ù„ØªÙˆØ§Ø²ÙŠ
try:
	_CIE_BASE = CognitiveIntegrationEngine
except NameError:
	class _CIE_BASE:
		def __init__(self): pass

class CognitiveIntegrationEngine(_CIE_BASE):
	def __init__(self):
		super().__init__()
		self.integration_id = uuid.uuid4().hex[:12]
		self.adapters = []
		self.metrics = {"invocations": 0, "success": 0, "fail": 0, "latency_ms": []}

	def connect_engines(self):
		# Discover adapter instances from environment / overrides
		env_adapters = discover_engines_from_env()

		# requested list from env or default to all known in capability map
		raw_list = os.getenv("AGL_ENGINES", "").strip()
		if raw_list:
			requested = [x.strip() for x in raw_list.split(",") if x.strip()]
		else:
			requested = list(ENGINE_CAPABILITIES.keys())

		# allow forcing full fanout of all known engines
		fanout_all = os.getenv("AGL_FANOUT_ALL", "0") == "1"

		# apply optional ordering hint
		ordered = os.getenv("AGL_ENGINE_ORDER", "").strip()
		if ordered:
			order = [x.strip() for x in ordered.split(",") if x.strip()]
			try:
				env_adapters.sort(key=lambda a: (order.index(a.name) if a.name in order else 10**6))
			except Exception:
				pass

		# capacity cap
		try:
			cap = int(os.getenv("AGL_ENGINE_MAX", "0"))
		except Exception:
			cap = 0

		# Build final adapter list
		inst_map = {getattr(a, 'name', None): a for a in env_adapters}
		final_adapters = []

		if fanout_all:
			# include all engines known in ENGINE_CAPABILITIES plus any requested/overrides
			all_names = list(dict.fromkeys(list(ENGINE_CAPABILITIES.keys()) + requested + list(inst_map.keys())))
			for n in all_names:
				# priority: override instances (inst_map), then builtins, then optional shim
				if n in inst_map:
					final_adapters.append(inst_map[n]); continue
				cls = _BUILTIN_ADAPTERS.get(n)
				if cls:
					try:
						final_adapters.append(cls())
					except Exception:
						continue
				# optional auto-shim for unknown engines (only if allowed)
				if os.getenv("AGL_ALLOW_UNKNOWN_SHIMS","0") == "1":
					try:
						# reuse discover_engines_from_env logic for shim creation
						final_adapters.append(type(f"shim_{n}", (EngineAdapter,), {"name": n, "domains": _infer_domains_from_name(n)})())
					except Exception:
						continue
		else:
			# route engines by capability map + health snapshot
			routed_names = route_engines(requested, domains_needed=getattr(self, '_current_domains_needed', ()), health=getattr(self, 'health', None), top_k=(cap if cap and cap > 0 else None))
			for n in routed_names:
				if n in inst_map:
					final_adapters.append(inst_map[n])
				else:
					# try instantiate built-in class if available
					cls = _BUILTIN_ADAPTERS.get(n)
					if cls:
						try:
							final_adapters.append(cls())
						except Exception:
							pass

		# apply cap trimming if cap specified
		if cap and cap > 0:
			final_adapters = final_adapters[:cap]

		# ensure hosted_storyqa is present (internalize fallback)
		if 'hosted_storyqa' not in [getattr(a,'name',None) for a in final_adapters]:
			cls = _BUILTIN_ADAPTERS.get('hosted_storyqa')
			if cls:
				try:
					final_adapters.append(cls())
				except Exception:
					pass

		# ensure hosted_llm is present so knowledge questions get a chance
		if 'hosted_llm' not in [getattr(a, 'name', None) for a in final_adapters]:
			# try builtins first
			cls = _BUILTIN_ADAPTERS.get('hosted_llm')
			if cls:
				try:
					final_adapters.append(cls())
				except Exception:
					pass
			else:
				# try to import the hosted adapter module directly (common case)
				try:
					mod = importlib.import_module('Self_Improvement.hosted_llm_adapter')
					cls = getattr(mod, 'HostedLLMAdapter', None)
					if cls:
						try:
							final_adapters.append(cls())
						except Exception:
							pass
				except Exception:
					# nothing to do
					pass

		self.adapters = final_adapters or self.adapters

		# register engines_registry metadata
		impls_spec = {}
		try:
			impls_spec = _parse_engine_impls_env(os.getenv("AGL_ENGINE_IMPLS", ""))
		except Exception:
			impls_spec = {}
		registry = {}
		for a in self.adapters:
			nm = getattr(a, "name", "unknown")
			impl_type = "override" if nm in impls_spec else "builtin"
			registry[nm] = {"domains": tuple(getattr(a, "domains", ()) or ()), "impl": impl_type, "status": "active"}
		self.engines_registry = registry
		# log summary
		try:
			_append_jsonl("artifacts/engine_impls_log.jsonl", {
				"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
				"event": "connect_engines_summary",
				"fanout_all": fanout_all,
				"engines": [getattr(a, "name", type(a).__name__) for a in self.adapters],
				"impl_types": [type(a).__name__ for a in self.adapters]
			})
		except Exception:
			pass
		return list(self.engines_registry.keys())

	def _attach_domains(self, proposal, adapter):
		if proposal is None:
			return {"engine": adapter.name, "content": {}, "checks": {}, "novelty": 0.5, "meta": {}}
		# Ø§Ø±ÙÙ‚ domains Ø¥Ù† ÙƒØ§Ù†Øª ØºÙŠØ± Ù…ÙˆØ¬ÙˆØ¯Ø©
		if "domains" not in proposal or not proposal.get("domains"):
			try:
				d = getattr(adapter, "domains", ())
				proposal["domains"] = tuple(d) if isinstance(d, (list, tuple, set)) else ()
			except Exception:
				proposal["domains"] = ()
		return proposal

	def _fanout_query(self, problem: dict, timeout_s: float = 3.5):
		results = []
		q = Queue()
		def worker(adapter: EngineAdapter):
			try:
				# protective skip: avoid running generative creativity adapters for non-creative queries
				try:
					current_domains = set(getattr(self, '_current_domains_needed', ()))
				except Exception:
					current_domains = set()
				aname = getattr(adapter, 'name', '').lower()
				if aname == 'gen_creativity' and 'creativity' not in current_domains:
					return
				self.metrics["invocations"] += 1
				t0=_now_ms()
				r = adapter.infer(problem, context=results, timeout_s=timeout_s)
				r = self._attach_domains(r or {}, adapter)
				self.metrics["success"] += 1
				self.metrics["latency_ms"].append(_now_ms()-t0)
				# record into HealthMonitor if present
				h = getattr(self, 'health', None)
				try:
					if h is not None:
						eng = getattr(adapter, 'name', None) or r.get('engine') or 'unknown'
						lat = _safe_float(r.get('meta', {}).get('latency_ms', _now_ms()-t0), 0.0)
						score = _safe_float(r.get('score', r.get('novelty', 0.5)), 0.5)
						h.record(engine_name=eng, latency_ms=lat, success=True, quality=score)
				except Exception:
					pass
				q.put(r)
				# record which engine was actually used in session_state if present on CIE
				try:
					ss = getattr(self, 'session_state', None)
					if ss is not None:
						ename = getattr(adapter, 'name', None) or (r.get('engine') if isinstance(r, dict) else None)
						if ename:
							# avoid duplicates
							if not hasattr(ss, 'used_engines'):
								try:
									setattr(ss, 'used_engines', [])
								except Exception:
									pass
							if ename not in getattr(ss, 'used_engines', []):
								try:
									getattr(ss, 'used_engines').append(ename)
								except Exception:
									pass
				except Exception:
					pass
			except Exception:
				self.metrics["fail"] += 1

		threads = []
		for a in self.adapters:
			th = threading.Thread(target=worker, args=(a,), daemon=True)
			th.start()
			threads.append(th)
		t_end = time.time() + timeout_s
		for _ in range(len(self.adapters)):
			remain = t_end - time.time()
			if remain <= 0:
				break
			try:
				results.append(q.get(timeout=remain))
			except Empty:
				break
		for th in threads:
			th.join(timeout=0.05)
		return results

	def get_loaded_engines(self):
		"""
		ÙŠÙØ±Ø¬Ø¹ Ù‚Ø§Ø¦Ù…Ø© Ù…Ø±ØªØ¨Ø© Ø¨Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ù…Ø­Ù…Ù‘Ù„Ø© Ù…Ø¹ Ù†ÙˆØ¹ Ø§Ù„ØªÙ†ÙÙŠØ°:
		[{"name": "...", "impl": "override|builtin", "domains": (...)}, ...]
		"""
		return [{"name": n,
			 "impl": (self.engines_registry.get(n, {}).get("impl") or "builtin"),
			 "domains": self.engines_registry.get(n, {}).get("domains", ())}
			for n in self.engines_registry.keys()]

	def _consensus_score(self, proposals):
		# Ù…Ø¹Ø§Ù…Ù„Ø§Øª Ù‚Ø§Ø¨Ù„Ø© Ù„Ù„Ø¶Ø¨Ø· Ù…Ù† Ø§Ù„Ø¨ÙŠØ¦Ø©
		tie_eps = _env_float("AGL_TIE_EPS", 0.01)
		diversity_bonus = _env_float("AGL_TIE_DIVERSITY_BONUS", 0.02)

		# 1) Ø§Ù„Ø³ÙƒÙˆØ± Ø§Ù„Ø£Ø³Ø§Ø³ÙŠ
		ranked = []
		for p in proposals:
			novelty = _safe_float(p.get("novelty", 0.5), 0.5)
			checks = p.get("checks", {})
			fit = 1.0 if checks.get("constraints", True) else 0.0
			feas = 1.0 if checks.get("feasible", True) else 0.0
			base = 0.5 * novelty + 0.3 * fit + 0.2 * feas
			# small domain-aware biasing: penalize generative creativity when not asked,
			# and boost hosted_llm for knowledge-oriented queries (best-effort).
			try:
				current_domains = set(getattr(self, '_current_domains_needed', ()))
			except Exception:
				current_domains = set()
			eng_name = (p.get('engine') or '').lower()
			if eng_name == 'gen_creativity' and 'creativity' not in current_domains:
				base = base - 0.25
			if eng_name == 'hosted_llm' and ('knowledge' in current_domains or 'general' in current_domains):
				base = base + 0.20
			ranked.append({**p, "score": base})

		ranked.sort(key=lambda r: r.get("score", 0.0), reverse=True)
		if not ranked:
			return ranked

		# 2) ØªØ¬Ù…ÙŠØ¹ Ø§Ù„ØªØ¹Ø§Ø¯Ù„Ø§Øª Ø§Ù„Ù‚Ø±ÙŠØ¨Ø© ÙˆØ¥Ø¹Ø§Ø¯Ø© ØªØ±ØªÙŠØ¨Ù‡Ø§ Ø¨ØªÙØ¶ÙŠÙ„ Ø§Ù„ØªÙ†ÙˆÙ‘Ø¹
		out = []
		seen_engines = set()
		i = 0
		while i < len(ranked):
			j = i
			ref = ranked[i]["score"]
			bucket = []
			while j < len(ranked) and abs(ranked[j]["score"] - ref) <= tie_eps:
				bucket.append(ranked[j]); j += 1

			# Ø¯Ø§Ø®Ù„ Ø§Ù„Ù€ bucket: ÙØ¶Ù‘Ù„ Ù…Ø­Ø±ÙƒØ§Øª Ø£Ù‚Ù„ ØªÙƒØ±Ø§Ø±Ù‹Ø§ (Ù„ØªØ¬Ù†Ø¨ Ø§Ù„ØªÙƒØ±Ø§Ø±)ØŒ Ø«Ù… ØºÙŠØ± Ø§Ù„Ù…Ø´Ø§Ù‡Ø¯ Ø«Ù… Ø§Ù„Ø£Ø¹Ù„Ù‰ Ø­Ø¯Ø§Ø«Ø©
			engine_counts = {}
			for it in bucket:
				engine_counts[it.get("engine")] = engine_counts.get(it.get("engine"), 0) + 1
			bucket_sorted = sorted(
				bucket,
				key=lambda r: (
					engine_counts.get(r.get("engine"), 0),
					(0 if r.get("engine") in seen_engines else -1),
					-_safe_float(r.get("novelty", 0.0))
				)
			)
			for item in bucket_sorted:
				eng = item.get("engine")
				if eng not in seen_engines:
					item["score"] = item.get("score", 0.0) + diversity_bonus
					seen_engines.add(eng)
				out.append(item)
			i = j

		out.sort(key=lambda r: r.get("score", 0.0), reverse=True)
		return out

	def _is_analytic_proposal(self, p: dict) -> bool:
		"""Heuristic: returns True for proposals that look like analytic/structured outputs (plans, pros/cons, ideas)."""
		if not isinstance(p, dict):
			return True
		c = p.get('content')
		if c is None:
			return True
		# string content is likely extractive
		if isinstance(c, str):
			# very long texts might be analytic, but assume short sentence = extractive
			return False if len(c) < 400 else True
		if isinstance(c, dict):
			keys = set(k.lower() for k in c.keys())
			analytic_keys = {'pros','cons','plan_outline','ideas','deliberation','review','summary','snippets','analogies'}
			if keys & analytic_keys:
				return True
			# if contains direct answer field, treat as non-analytic
			if 'answer' in keys or 'result' in keys:
				return False
			# default: consider analytic if many keys present
			return len(keys) > 2

	@staticmethod
	def _extract_answer_from_proposal(p: dict) -> Optional[str]:
		"""Try to extract a short answer string from a proposal.
		Returns string or None.
		"""
		if not isinstance(p, dict):
			return None
		c = p.get('content')
		if c is None:
			return None
		# If adapter provided direct answer
		if isinstance(c, dict) and 'answer' in c:
			try:
				return str(c.get('answer') or '').strip()
			except Exception:
				return None
		# string content
		if isinstance(c, str):
			return c.strip()
		# try common dict shapes
		if isinstance(c, dict):
			# single-key dict with sentence-like value
			for k, v in c.items():
				if isinstance(v, str) and len(v.split()) <= 40:
					return v.strip()
				if isinstance(v, list) and v and isinstance(v[0], str) and len(v[0].split()) <= 40:
					return v[0].strip()
		# fallback None
		return None


	def _is_knowledge_question(problem: dict) -> bool:
		"""Heuristic: detect whether the user's problem/question is knowledge-oriented."""
		try:
			q = (problem.get("question") or problem.get("title") or "") if isinstance(problem, dict) else str(problem or "")
			q = str(q).lower()
		except Exception:
			return False
		triggers = [
			"Ù…Ø§ Ù‡ÙŠ", "Ù…Ø§Ù‡ÙŠ", "Ù…Ø§ Ù‡Ùˆ", "Ù…Ø§Ù‡Ùˆ", "Ø§Ø¹Ø±Ø§Ø¶", "Ø£Ø¹Ø±Ø§Ø¶",
			"Ø¹Ù„Ø§Ø¬", "treatment", "symptoms", "what is", "define",
			"explain", "Ø³Ø¨Ø¨", "Ø§Ø³Ø¨Ø§Ø¨", "Ø£Ø³Ø¨Ø§Ø¨", "properties", "causes",
		]
		return any(t in q for t in triggers)


	def _prefer_hosted_llm_if_knowledge(problem: dict, solutions: list, current_winner: dict) -> dict:
		"""If the question is knowledge-like and there is a hosted_llm solution
		with a non-empty `content['answer']`, prefer it over the current winner.
		"""
		try:
			if not CognitiveIntegrationEngine._is_knowledge_question(problem):
				return current_winner
		except Exception:
			return current_winner

		hosted = None
		for s in (solutions or []):
			try:
				if (s.get("engine") or "").lower() == "hosted_llm":
					content = s.get("content") or {}
					ans = (content.get("answer") or "").strip() if isinstance(content, dict) else ""
					if ans:
						hosted = s
						break
			except Exception:
				continue

		return hosted or current_winner

	class FinalAnswerArbiter:
		"""Simple arbitration layer: prefer extractive answers (hosted_storyqa or 'answer' fields),
		otherwise pick highest-scoring but try to extract a short answer."""
		def __init__(self, prefer_hosted: bool = True):
			self.prefer_hosted = prefer_hosted

		def choose(self, problem: dict, proposals: list) -> dict:
			# proposals expected to be list of dicts with 'engine' and 'score' and 'content'
			if not proposals:
				return {}

			# Normalize problem into a dict-shaped payload so downstream helpers
			# and logging have a consistent view.
			try:
				if isinstance(problem, dict):
					problem_dict = problem
				else:
					problem_dict = {"id": uuid.uuid4().hex[:8], "title": str(problem)[:160], "question": str(problem)}
			except Exception:
				problem_dict = {"id": "-", "title": "-", "question": str(problem)}

			# Resolve knowledge-detection helper (accept either class-bound or module-level)
			help_is_knowledge = getattr(CognitiveIntegrationEngine, '_is_knowledge_question', None) or globals().get('_is_knowledge_question')
			is_knowledge = False
			try:
				if callable(help_is_knowledge):
					is_knowledge = bool(help_is_knowledge(problem_dict))
			except Exception:
				is_knowledge = False

			# Log for debugging visibility as requested
			try:
				candidates = []
				for c in (proposals or []):
					eng = (c.get('engine') or '')
					cont = c.get('content') or {}
					has_ans = False
					if isinstance(cont, dict):
						has_ans = bool(str(cont.get('answer') or '').strip())
					elif isinstance(cont, str):
						has_ans = bool(cont.strip())
					candidates.append((eng, has_ans))
				print("[ARBITER] problem:", repr(problem_dict))
				print("[ARBITER] is_knowledge:", is_knowledge)
				print("[ARBITER] candidates:", candidates)
			except Exception:
				pass

			# If RAG produced extractive evidence, prefer it immediately for knowledge queries
			try:
				if is_knowledge:
					for p in (proposals or []):
						try:
							if (p.get('engine') or '').lower() == 'rag':
								cont = p.get('content') or {}
								ans = (cont.get('answer') or '').strip() if isinstance(cont, dict) else ''
								if ans:
									print("[ARBITER] selecting rag (early)")
									return p
						except Exception:
							continue
			except Exception:
				pass

			# If this is a knowledge-like question, prefer any hosted_llm proposal
			# that provides a non-empty extractive answer. Return it immediately.
			if is_knowledge:
				# For knowledge questions, de-prioritize perception adapters and
				# prefer hosted_llm. Remove vision/audio/sensor proposals from
				# immediate consideration to avoid 'patterns' wins.
				filtered = [p for p in (proposals or []) if (p.get('engine') or '').lower() not in ('vision','audio','sensor')]
				if filtered:
					proposals = filtered
				for p in proposals:
					try:
						if (p.get('engine') or '').lower() == 'hosted_llm':
							content = p.get('content') or {}
							ans = (content.get('answer') or '').strip() if isinstance(content, dict) else ''
							if ans:
								new = dict(p)
								new['content'] = {'answer': ans}
								print("[ARBITER] selecting hosted_llm (early)")
								return new
					except Exception:
						continue
			# 1) prefer hosted_storyqa if present and provides an answer
			for p in proposals:
				try:
					if p.get('engine') == 'hosted_storyqa':
						ans = CognitiveIntegrationEngine._extract_answer_from_proposal(p) if hasattr(CognitiveIntegrationEngine, '_extract_answer_from_proposal') else None
						if ans:
							new = dict(p)
							new['content'] = {'answer': ans}
							return new
				except Exception:
					continue
			# 2) pick first extractive proposal
			for p in proposals:
				try:
					ans = CognitiveIntegrationEngine._extract_answer_from_proposal(p) if hasattr(CognitiveIntegrationEngine, '_extract_answer_from_proposal') else None
					if ans:
						new = dict(p)
						new['content'] = {'answer': ans}
						# before returning, if this is not hosted_llm but the question is knowledge-like,
						# prefer hosted_llm if available
						try:
							pref = CognitiveIntegrationEngine._prefer_hosted_llm_if_knowledge(problem, proposals, new)
							if pref and pref is not new:
								return pref
						except Exception:
							pass
						return new
				except Exception:
					continue
			# 3) fallback to top-scoring but ensure content formatted
			top = proposals[0]
			try:
				ans = CognitiveIntegrationEngine._extract_answer_from_proposal(top) if hasattr(CognitiveIntegrationEngine, '_extract_answer_from_proposal') else None
			except Exception:
				ans = None
			if ans:
				new = dict(top); new['content'] = {'answer': ans}; return new
			# leave as-is
			return top

	def postprocess_pipeline(self, problem: dict, ranked_proposals: list) -> dict:
		"""Run postprocessing/normalization + final arbitration over ranked proposals.
		Returns a standardized winner proposal (dict with 'engine','content':{'answer':...}, 'score').

		Accepts `problem` so postprocessing can apply question-aware preferences
		(e.g., prefer hosted_llm for knowledge questions).
		"""
		arb = self.FinalAnswerArbiter()
		try:
			# allow arbiter to pick (provide problem so arbiter can prefer hosted_llm)
			chosen = arb.choose(problem, ranked_proposals or [])
		except Exception:
			chosen = None

		if not chosen:
			chosen = ranked_proposals[0] if ranked_proposals else {}

		# Apply preference: if this looks like a knowledge question and hosted_llm
		# has a non-empty answer, prefer it.
		try:
			chosen = CognitiveIntegrationEngine._prefer_hosted_llm_if_knowledge(problem, ranked_proposals or [], chosen)
		except Exception:
			pass

		# If this looks like a knowledge question and we don't already have
		# a hosted LLM winner, try directly invoking a `hosted_llm` adapter
		# (if loaded) to get an extractive answer and return it immediately.
		try:
			if CognitiveIntegrationEngine._is_knowledge_question(problem):
				for a in getattr(self, 'adapters', []) or []:
					try:
						if getattr(a, 'name', '').lower() == 'hosted_llm':
							alt = None
							try:
								alt = a.infer(problem if isinstance(problem, dict) else {'question': str(problem)}, timeout_s=_safe_float(os.getenv('AGL_OLLAMA_CLI_TIMEOUT', '600')))
							except Exception:
								alt = None
							if alt and isinstance(alt, dict):
								ans2 = self._extract_answer_from_proposal(alt)
								if ans2:
									alt['content'] = {'answer': ans2}
									return alt
					except Exception:
						continue
		except Exception:
			pass

		# ensure content has 'answer' key if possible
		try:
			if isinstance(chosen.get('content'), dict) and 'answer' in chosen.get('content'):
				return chosen
			ans = self._extract_answer_from_proposal(chosen)
			if ans:
				c = dict(chosen)
				c['content'] = {'answer': ans}
				return c
		except Exception:
			pass

		return chosen

	def collaborative_solve(self, problem: dict, domains_needed=()):
		# allow routing to pick suitable engines for requested domains
		try:
			self._current_domains_needed = tuple(domains_needed or ())
		except Exception:
			self._current_domains_needed = tuple(domains_needed or ())
		# ensure adapters are (re)connected using the router logic
		try:
			self.connect_engines()
		except Exception:
			# swallow to preserve backward compatibility
			pass
		proposals = self._fanout_query(problem, timeout_s=_safe_float(os.getenv("AGL_ENGINE_TIMEOUT","3.5"), 3.5))
		# If this looks like a knowledge question, boost hosted_llm novelty
		# so it competes strongly in consensus scoring.
		try:
			if CognitiveIntegrationEngine._is_knowledge_question(problem):
				for p in (proposals or []):
					try:
						if (p.get('engine') or '').lower() == 'hosted_llm':
							p['novelty'] = max(_safe_float(p.get('novelty', 0.5)), 0.95)
					except Exception:
						continue
		except Exception:
			pass
		ranked = self._consensus_score(proposals)
		# allow meta-controller to inject strategies if needed
		ranked = self._inject_generative_strategy_if_needed(problem, ranked)
		# Post-process and final arbitration to ensure extractive final answer
		try:
			final_winner = self.postprocess_pipeline(problem, ranked)
		except Exception:
			final_winner = ranked[0] if ranked else None
		# build top list and ensure final_winner is present
		top = ranked[:5]
		if final_winner and final_winner not in top:
			# place final winner at front
			top.insert(0, final_winner)
		winner = final_winner or (ranked[0] if ranked else None)
		integration_id = self.integration_id
		try:
			with open("artifacts/collaboration_log.jsonl","a",encoding="utf-8") as f:
				f.write(json.dumps({"phase":"integrate",
									"payload":{"integration_id":integration_id,
											   "solutions_n": len(proposals),
											   "winner_engine": (winner or {}).get("engine"),
											   "avg_latency_ms": (sum(self.metrics["latency_ms"])/max(1,len(self.metrics["latency_ms"]))),
											   "invocations": self.metrics["invocations"],
											   "success": self.metrics["success"],
											   "fail": self.metrics["fail"]}}, ensure_ascii=False)+"\n")
		except Exception:
			pass

		try:
			with open("artifacts/collective_memory.jsonl","a",encoding="utf-8") as f:
				f.write(json.dumps({
					"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
					"source_engine": "cognitive_integration",
					"learning": {
						"problem": {"title": problem.get("title","task"), "signals": problem.get("signals",[])},
						"solutions_n": len(proposals),
						"integration_id": integration_id,
						"signals": {"diversity": len({p.get('engine') for p in proposals})},
						"winner_score": (winner or {}).get("score", 0.0)
					},
					"verified_by": []
				}, ensure_ascii=False)+"\n")
		except Exception:
			pass

		return {"integration_id": integration_id,
				"solutions": (len(proposals) if isinstance(proposals, list) else int(proposals or 0)),
				"winner": winner,
				"top": top}

# === [END PATCH] ===


# === [BEGIN PATCH :: AGI-Stage-1.0] ===
import time, json, os, uuid, math

# -------- Meta Controller (Self-Reflective Loop) --------
class MetaController:
    def __init__(self):
        self.interval = int(os.getenv("AGL_SELF_EVALUATION_INTERVAL", "3"))
        self.tie_eps  = _safe_float(os.getenv("AGL_TIE_EPS", "0.01"), 0.01)
        self.alpha    = _safe_float(os.getenv("AGL_ENGINE_EMA_ALPHA", "0.2"), 0.2)
        self.min_conf = _safe_float(os.getenv("AGL_META_MIN_CONF", "0.72"), 0.72)

    def evaluate_cycle(self, ranked_top):
        """
        ÙŠÙØ¹ÙŠØ¯ dict ÙÙŠÙ‡: confidence, diversity, need_alternative (bool)ØŒ ÙˆÙ…Ø¤Ø´Ø±Ø§Øª Ù…Ø³Ø§Ø¹Ø¯Ø©.
        """
        if not ranked_top:
            return {"confidence": 0.0, "diversity": 0, "need_alternative": True, "reason": "no_proposals"}
        # Ø«Ù‚Ø© Ù…Ø¨Ø³Ø·Ø© = score Ø§Ù„Ø£Ø¹Ù„Ù‰ â€“ Ù…ØªÙˆØ³Ø· Ø§Ù„ÙØ±Ù‚ Ø¶Ù…Ù† Ø­Ø²Ù…Ø© Ø§Ù„ØªØ³Ø§ÙˆÙŠ ØªÙ‚Ø±ÙŠØ¨Ù‹Ø§
        top_score = ranked_top[0].get("score", 0.0)
        near = [p for p in ranked_top if abs(p.get("score",0.0) - top_score) <= self.tie_eps]
        diversity = len({tuple(p.get("domains") or ()) for p in ranked_top})
        confidence = max(0.0, min(1.0, top_score - (0.5*len(near)/max(1,len(ranked_top)))) )
        need_alt = (confidence < self.min_conf)
        return {"confidence": confidence, "diversity": diversity, "need_alternative": need_alt, "reason": ("low_conf" if need_alt else "ok")}

    def update_priors(self, engine_stats_path, winner, latency_ms=0.0):
        try:
            stats = {}
            if os.path.exists(engine_stats_path):
                with open(engine_stats_path,"r",encoding="utf-8") as f:
                    stats = json.load(f) or {}
            name = (winner or {}).get("engine")
            qual = _safe_float((winner or {}).get("score", 0.5), 0.5)
            lat  = _safe_float(latency_ms, 0.0)
            if name:
                s = stats.get(name, {"quality_ma": 0.5, "latency_ma": 0.0})
                s["quality_ma"] = (1-self.alpha)*_safe_float(s.get("quality_ma",0.5),0.5) + self.alpha*qual
                s["latency_ma"] = (1-self.alpha)*_safe_float(s.get("latency_ma",0.0),0.0) + self.alpha*lat
                stats[name] = s
                # ensure parent dir exists
                try:
                    parent = os.path.dirname(engine_stats_path)
                    if parent:
                        os.makedirs(parent, exist_ok=True)
                except Exception:
                    pass
                with open(engine_stats_path,"w",encoding="utf-8") as f:
                    json.dump(stats,f,ensure_ascii=False,indent=2)
                return True
        except Exception:
            pass
        return False

# -------- Timeline + Contextualizer (Context Reasoning) --------
class TimelineAdapter(EngineAdapter):
    name = "timeline"; domains = ("context","temporal","causal")
    def infer(self, problem, context=None, timeout_s=3.0):
        # Ø§Ø³ØªØ®Ø±Ø§Ø¬ ØªØ¶Ø§Ø±ÙŠØ³ Ø²Ù…Ù†ÙŠØ© Ù…Ø®ØªØµØ±Ø© (ÙˆÙ‡Ù…ÙŠØ© Ø¢Ù…Ù†Ø© Ø§ÙØªØ±Ø§Ø¶ÙŠÙ‹Ø§)
        t0=_now_ms()
        events = [{"t":"t-2","note":"prior related fact"},
                  {"t":"t-1","note":"constraint observed"},
                  {"t":"t0","note":problem.get("title","task")}]
        edges  = [("t-2","t-1"),("t-1","t0")]
        return {
            "engine": self.name,
            "content": {"events": events, "edges": edges},
            "checks": {"constraints": True, "feasible": True},
            "novelty": 0.52,
            "meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
            "domains": self.domains,
        }

class ContextualizerAdapter(EngineAdapter):
    name = "contextualizer"; domains = ("context","semantic")
    def infer(self, problem, context=None, timeout_s=3.0):
        t0=_now_ms()
        hints = {"focus": problem.get("title","task"), "signals": problem.get("signals", [])}
        return {
            "engine": self.name,
            "content": {"context_hints": hints, "strength": 0.6},
            "checks": {"constraints": True, "feasible": True},
            "novelty": 0.5,
            "meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
            "domains": self.domains,
        }

# -------- Motivation / Reward Shaping --------
class MotivationAdapter(EngineAdapter):
    name = "motivation"; domains = ("meta","reward","policy")
    def infer(self, problem, context=None, timeout_s=3.0):
        t0=_now_ms()
        # Ù…ÙƒØ§ÙØ¢Øª Ø¯Ø§Ø®Ù„ÙŠØ© Ù…Ø¨Ø³Ø·Ø©: Ø¯Ù‚Ø©/ØªÙ†ÙˆØ¹/Ø³Ø±Ø¹Ø©/Ø§Ù„ØªØ²Ø§Ù…
        reward = {"accuracy_hint": 0.6, "diversity_hint": 0.7, "speed_hint": 0.5, "constraint_hint": 0.8}
        return {
            "engine": self.name,
            "content": {"reward_signals": reward, "policy":"encourage_diverse_accurate_fast"},
            "checks": {"constraints": True, "feasible": True},
            "novelty": 0.55,
            "meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
            "domains": self.domains,
        }

# ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ù…Ø­Ø±Ù‘ÙƒØ§Øª Ø§Ù„Ø¬Ø¯ÙŠØ¯Ø©
_BUILTIN_ADAPTERS.update({
    "timeline": TimelineAdapter,
    "contextualizer": ContextualizerAdapter,
    "motivation": MotivationAdapter,
})


# === Stage-8 helper: HostedStoryQAAdapter (mock) ===
class HostedStoryQAAdapter(EngineAdapter):
	"""Mock / lightweight hosted-style adapter that performs simple extractive
	answers from a story text. Intended as a fallback for StoryQA experiments.
	"""
	name = "hosted_storyqa"
	domains = ("language", "qa")

	def infer(self, problem, context=None, timeout_s=5.0):
		t0 = _now_ms()
		# Accept either signals list or flat keys
		story = None
		question = None
		if isinstance(problem, dict):
			sigs = problem.get('signals') or []
			if sigs and isinstance(sigs, list):
				for s in sigs:
					if isinstance(s, dict) and s.get('kind') == 'story':
						story = s.get('text')
					if isinstance(s, dict) and s.get('kind') == 'question':
						question = s.get('text')
			# fallback flat
			story = story or problem.get('story') or problem.get('text')
			question = question or problem.get('question') or problem.get('prompt')

		story = (story or "").strip()
		question = (question or "").strip()

		answer = ""
		# Naive extractive heuristic: split story into sentences and pick the one
		# with highest overlap / similarity to the question (or simple keyword lookup)
		try:
			sents = []
			if story:
				# split on Arabic/English sentence separators
				for part in [p.strip() for p in re.split(r'[\n\.?ØŒØŸ.!]', story) if p.strip()]:
					sents.append(part)
			best = ""
			best_score = 0.0
			from difflib import SequenceMatcher
			for s in sents:
				score = SequenceMatcher(None, s.lower(), question.lower()).ratio()
				if score > best_score:
					best_score = score
					best = s
			if best:
				answer = best
			else:
				# fallback simple methods
				# if question contains 'Ø£ÙŠÙ†' or 'where' pick phrase containing 'Ø®Ù„Ù' or 'behind'
				ql = question.lower()
				if 'Ø£ÙŠÙ†' in ql or 'where' in ql:
					if 'Ø®Ù„Ù' in story:
						m = re.search(r"[^.ØŒØŸ]*Ø®Ù„Ù[^.ØŒØŸ]*", story)
						if m:
							answer = m.group(0).strip()
				if not answer and ('ÙƒÙŠÙ' in ql or 'how' in ql):
					if 'Ø­Ù„ÙŠØ¨' in story or 'milk' in story:
						m = re.search(r"[^.ØŒØŸ]*Ø­Ù„ÙŠØ¨[^.ØŒØŸ]*", story)
						if m:
							answer = m.group(0).strip()
				if not answer and ('Ù…Ø§Ø°Ø§' in ql or 'what' in ql):
					# try returning sentence with 'Ø£Ù†Ù‚Ø°' or 'saved'
					if 'Ø£Ù†Ù‚Ø°' in story or 'saved' in story:
						m = re.search(r"[^.ØŒØŸ]*Ø£Ù†Ù‚Ø°[^.ØŒØŸ]*|[^.ØŒØŸ]*saved[^.ØŒØŸ]*", story)
						if m:
							answer = m.group(0).strip()
		except Exception:
			answer = ''

		# final fallback
		if not answer:
			answer = story.split('\n')[0] if story else ''

		return {
			'engine': self.name,
			'content': {'answer': answer},
			'checks': {'constraints': True, 'feasible': True},
			'novelty': 0.1,
			'meta': {'latency_ms': _now_ms() - t0, 'tokens': 0},
			'domains': self.domains,
			'score': 0.95,
		}


_BUILTIN_ADAPTERS.update({
	"hosted_storyqa": HostedStoryQAAdapter,
})

# Register hosted_llm adapter if available (non-fatal)
try:
	from agl.engines.self_improvement.Self_Improvement.hosted_llm_adapter import HostedLLMAdapter  # type: ignore
	_BUILTIN_ADAPTERS.update({"hosted_llm": HostedLLMAdapter})
except Exception:
	pass

# === Stage-7: HealthMonitor (metrics & snapshots) ===
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class EngineMetric:
	name: str
	calls: int = 0
	successes: int = 0
	fails: int = 0
	avg_latency_ms: float = 0.0
	avg_quality: float = 0.5


class HealthMonitor:
	"""Collect lightweight per-engine metrics and snapshot to a JSON file.

	- Uses a small EMA to update averages.
	- Writes to `path` on flush().
	"""
	def __init__(self, path: str = "artifacts/health_metrics.json", alpha: float = None):
		self.path = path or "artifacts/health_metrics.json"
		try:
			self.alpha = float(alpha) if alpha is not None else _safe_float(os.getenv("AGL_HEALTH_EMA_ALPHA","0.2"), 0.2)
		except Exception:
			self.alpha = 0.2
		self.metrics: Dict[str, EngineMetric] = {}

	def _ensure_parent(self):
		try:
			parent = os.path.dirname(self.path)
			if parent:
				os.makedirs(parent, exist_ok=True)
		except Exception:
			pass

	def record(self, engine_name: str, latency_ms: float = 0.0, success: bool = True, quality: float = 0.5):
		if not engine_name:
			engine_name = "unknown"
		m = self.metrics.get(engine_name)
		if m is None:
			m = EngineMetric(name=engine_name)
			self.metrics[engine_name] = m
		m.calls += 1
		if success:
			m.successes += 1
		else:
			m.fails += 1
		# EMA update for latency and quality
		try:
			m.avg_latency_ms = (1 - self.alpha) * float(m.avg_latency_ms) + self.alpha * float(latency_ms)
		except Exception:
			pass
		try:
			m.avg_quality = max(0.0, min(1.0, (1 - self.alpha) * float(m.avg_quality) + self.alpha * float(quality)))
		except Exception:
			pass

	def snapshot(self) -> Dict[str, Any]:
		out = {
			"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
			"engines": {}
		}
		for k, v in self.metrics.items():
			out["engines"][k] = {
				"calls": v.calls,
				"successes": v.successes,
				"fails": v.fails,
				"avg_latency_ms": round(float(v.avg_latency_ms or 0.0), 6),
				"avg_quality": round(float(v.avg_quality or 0.5), 6),
			}
		return out

	def flush(self):
		try:
			self._ensure_parent()
			with open(self.path, 'w', encoding='utf-8') as f:
				json.dump(self.snapshot(), f, ensure_ascii=False, indent=2)
			return True
		except Exception:
			return False


# === Stage-8: Research/Experiment scaffolding ===
class ResearchTaskAdapter(EngineAdapter):
	"""Minimal adapter that can represent an experiment-specific producer.
	This is a light-weight shim to allow experiments to inject controlled proposals.
	"""
	name = "research_adapter"
	domains = ("research", "experiment")

	def infer(self, problem, context=None, timeout_s=3.0):
		t0 = _now_ms()
		# Return a safe, low-novelty structured proposal reflecting the task
		return {
			"engine": self.name,
			"content": {"experiment_title": problem.get("title","exp"), "params": problem.get("signals", [])},
			"checks": {"constraints": True, "feasible": True},
			"novelty": 0.45,
			"meta": {"latency_ms": _now_ms() - t0, "tokens": 0},
			"domains": self.domains,
		}


class ExperimentRunner:
	"""Run simple experiments against a CognitiveIntegrationEngine and log results to JSONL.

	Example usage:
	  er = ExperimentRunner(engine)
	  er.run_compare([configA, configB], repeats=3)
	"""
	def __init__(self, engine: 'CognitiveIntegrationEngine', out_path: str = "artifacts/experiments.jsonl"):
		self.engine = engine
		self.out_path = out_path
		try:
			parent = os.path.dirname(self.out_path)
			if parent:
				os.makedirs(parent, exist_ok=True)
		except Exception:
			pass

	def _append(self, item: dict):
		try:
			with open(self.out_path, 'a', encoding='utf-8') as f:
				f.write(json.dumps(item, ensure_ascii=False) + "\n")
		except Exception:
			pass

	def run_once(self, problem: dict, domains_needed=()):
		t0 = time.time()
		res = self.engine.collaborative_solve(problem, domains_needed=domains_needed)
		dur = time.time() - t0
		rec = {
			"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
			"problem": problem.get("title","run"),
			"integration_id": res.get("integration_id"),
			"winner": (res.get("winner") or {}).get("engine"),
			"score": (res.get("winner") or {}).get("score"),
			"duration_s": round(dur, 4),
		}
		self._append(rec)
		return res

	def run_compare(self, problems: list, repeats: int = 1, domains_needed=()):
		results = []
		for r in range(repeats):
			for p in problems:
				res = self.run_once(p, domains_needed=domains_needed)
				results.append(res)
		return results


# -------- Ø±Ø¨Ø· Ø§Ù„Ù…ØªØ­ÙƒÙ‘Ù… Ø§Ù„ÙÙˆÙ‚ÙŠ Ù…Ø¹ CIE --------
try:
    _CIE_BASE = CognitiveIntegrationEngine
except NameError:
    class _CIE_BASE: 
        def __init__(self): pass

class CognitiveIntegrationEngine(_CIE_BASE):  # Ù†Ø¹ÙŠØ¯ ØªØ¹Ø±ÙŠÙÙ‡Ø§ Ø¨ØªÙˆØ³ÙŠØ¹Ø§Øª Ø¬Ø¯ÙŠØ¯Ø© Ø¯ÙˆÙ† ÙƒØ³Ø± Ù…Ø§ Ø³Ø¨Ù‚
	def __init__(self):
		super().__init__()
		self.meta = MetaController()
		self.engine_stats_path = os.getenv("AGL_ENGINE_STATS_PATH", "artifacts/engine_stats.json")
		self.generative_link = bool(int(os.getenv("AGL_GENERATIVE_LINK","1")))
		# ensure memory is attached in final CIE init (Stage-4)
		try:
			if os.getenv("AGL_MEMORY_ENABLE", "1") == "1":
				try:
					self.memory = MemorySystem(root=os.getenv("AGL_MEMORY_ROOT", "artifacts/memory"))
				except Exception:
					try:
						self.memory = MemoryLoop(root=os.getenv("AGL_MEMORY_ROOT", "artifacts/memory")) # type: ignore
					except Exception:
						self.memory = None
			else:
				self.memory = None
		except Exception:
			self.memory = None
		# Stage-5: attach perception bus
		try:
			self.pbus = PerceptionBus()
		except Exception:
			self.pbus = PerceptionBus()
		# Stage-7: attach HealthMonitor
		try:
			self.health = HealthMonitor(path=os.getenv("AGL_HEALTH_PATH", "artifacts/health_metrics.json"))
		except Exception:
			self.health = None
	# Ø§Ù„Ø¨Ù‚ÙŠØ© (self.adapters, self.metrics, Ø¥Ù„Ø®) Ù…ÙˆØ¬ÙˆØ¯Ø© Ù…Ø³Ø¨Ù‚Ù‹Ø§ ÙÙŠ Ù†Ø³Ø®ØªÙƒ

	def _inject_generative_strategy_if_needed(self, problem, ranked):
		if not self.generative_link:
			return ranked
		need_alt = self.meta.evaluate_cycle(ranked).get("need_alternative", False)
		if not need_alt:
			return ranked
		# Ø¥Ø¯Ø±Ø§Ø¬ Ø§Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠØ© ØªÙÙƒÙŠØ± Ø¨Ø¯ÙŠÙ„Ø© (shim Ø¢Ù…Ù†) Ø¯Ø§Ø®Ù„ Ø§Ù„Ø³Ø¨Ø§Ù‚
		try:
			idea = {"engine":"gen_creativity","content":{"idea":"alternative thinking strategy"}, 
				"checks":{"constraints":True,"feasible":True},"novelty":0.65,
				"meta":{"latency_ms":0,"tokens":0},"domains":("creativity","meta")}
			# give it a competitive score so it's included in the top set for low-confidence cases
			try:
				top_score = ranked[0].get("score", 0.5) if ranked else 0.5
			except Exception:
				top_score = 0.5
			injected = {**idea, "score": float(max(0.65, top_score + 0.05))}
			# insert at the front to increase chance of being in top results
			ranked.insert(0, injected)
		except Exception:
			pass
		return ranked

	def collaborative_solve(self, problem: dict, domains_needed=()):
		proposals = self._fanout_query(problem, timeout_s=_safe_float(os.getenv("AGL_ENGINE_TIMEOUT","3.5"), 3.5))
		ranked = self._consensus_score(proposals)
		ranked = self._inject_generative_strategy_if_needed(problem, ranked)

		top = ranked[:5]
		winner = ranked[0] if ranked else None

		# ØªØ­Ø¯ÙŠØ« priors Ø¹Ø¨Ø± Ø§Ù„Ù…ØªØ­ÙƒÙ‘Ù… Ø§Ù„ÙÙˆÙ‚ÙŠ
		if os.getenv("AGL_META_REFLECTION","1") == "1":
			try:
				latency = _safe_float((winner or {}).get("meta",{}).get("latency_ms",0.0), 0.0)
				self.meta.update_priors(self.engine_stats_path, winner, latency_ms=latency)
			except Exception:
				pass

		# Ø§Ù„Ø³Ø¬Ù„Ø§Øª ÙˆØ§Ù„Ø°Ø§ÙƒØ±Ø© ÙƒÙ…Ø§ ÙƒØ§Ù†Øª Ù„Ø¯ÙŠÙƒ Ù…Ø³Ø¨Ù‚Ù‹Ø§ (collaboration_log.jsonl, collective_memory.jsonl)
		# ... (Ù†Ø­ØªÙØ¸ Ø¨ÙƒØªØ§Ø¨Ø§ØªÙƒ Ø§Ù„Ø³Ø§Ø¨Ù‚Ø© ÙƒÙ…Ø§ Ù‡ÙŠ)

		return {"integration_id": self.integration_id,
				"solutions": (len(proposals) if isinstance(proposals, list) else int(proposals or 0)),
				"winner": winner,
				"top": top}

	def answer_question(self, question: str, context: Optional[str] = None, language: str = "ar", domains: Optional[tuple] = None, fanout_all: bool = True, **kwargs) -> Dict[str, Any]:
		"""
		High-level helper: build a standard `qa_single` problem, run collaborative_solve across engines,
		and format the final answer using the legacy formatter if available.

		Returns a bundle with `formatted_answer`, `problem`, `cie_result`, and `health_snapshot`.
		"""
		# optionally force fanout-all via env so connect_engines will include all adapters
		try:
			if fanout_all:
				os.environ["AGL_FANOUT_ALL"] = "1"
		except Exception:
			pass

		prob = {
			"task_type": "qa_single",
			"language": language,
			"question": question,
			"context": context or "",
			"constraints": kwargs.get("constraints", {"style": "Ù…Ù†Ø³Ù‚/ÙˆØ§Ø¶Ø­", "max_tokens": 400}),
		}

		if domains is None:
			domains_needed = ("language", "analysis", "knowledge", "reasoning")
		else:
			domains_needed = tuple(domains)

		# run the collaborative solver
		res = self.collaborative_solve(prob, domains_needed=domains_needed)

		# health snapshot if available
		health_snapshot = None
		try:
			if hasattr(self, 'health') and callable(getattr(self.health, 'snapshot', None)):
				health_snapshot = self.health.snapshot()
		except Exception:
			health_snapshot = None

		# format final answer using legacy pipeline if possible
		formatted = self.format_final_answer(prob, res, system_prompt=kwargs.get('system_prompt'))

		return {
			"formatted_answer": formatted,
			"problem": prob,
			"cie_result": res,
			"health": health_snapshot,
		}

	def format_final_answer(self, problem: dict, result: dict, system_prompt: Optional[str] = None, rag_kwargs: Optional[Dict[str, Any]] = None) -> Any:
		"""
		Adapter that takes a CIE `result` (winner/top/memory) and calls the legacy
		Answer Formatter (if present) to produce a polished final answer.

		If the legacy formatter `Integration_Layer.rag_wrapper.rag_answer` is not
		available, falls back to a simple synthesized answer from the winner/top.
		"""
		# build a lightweight context string from winner/top
		parts: List[str] = []
		parts.append("### Ø§Ù„Ø³Ø¤Ø§Ù„\n")
		parts.append(str(problem.get('question') or problem.get('title') or ''))
		winner = (result or {}).get('winner') or {}
		if winner:
			parts.append("\n\n### Ø§Ù„ÙØ§Ø¦Ø² (winner)\n")
			parts.append(f"- engine: {winner.get('engine')}")
			parts.append(f"- score: {winner.get('score')}")
			parts.append("Ù…Ø­ØªÙˆÙ‰ Ø§Ù„ÙØ§Ø¦Ø²:\n")
			parts.append(str(winner.get('content')))
		top = (result or {}).get('top') or []
		if top:
			parts.append("\n\n### Ø£ÙØ¶Ù„ Ø§Ù„Ù…Ù‚ØªØ±Ø­Ø§Øª (top)\n")
			for i, p in enumerate(top, start=1):
				parts.append(f"Proposal #{i} - engine={p.get('engine')} score={p.get('score')}")
				parts.append(str(p.get('content')))
		context_text = "\n".join(parts)

		# attempt to call legacy rag_answer
		try:
			from Integration_Layer.rag_wrapper import rag_answer as _rag
		except Exception:
			_rag = None

		if _rag is None:
			# fallback: return winner content or synthesized summary
			try:
				ans = winner.get('content') if winner and winner.get('content') else None
				if isinstance(ans, dict):
					# try extract short answer
					short = self._extract_answer_from_proposal({'content': ans})
					if short:
						return short
					return json.dumps(ans, ensure_ascii=False)
				if ans:
					return str(ans)
			except Exception:
				pass
			# final fallback: synthesize from top
			if top:
				lines = []
				for p in top[:3]:
					lines.append(f"[{p.get('engine')}] {str(p.get('content'))[:200]}")
				return "\n".join(lines)
			return "Ù„Ø§ ØªÙˆØ¬Ø¯ Ù†ØªØ§Ø¦Ø¬ Ù…ØªØ§Ø­Ø©"

		# call rag with flexible signature
		if system_prompt is None:
			system_prompt = "Answer as final formatter."
		if rag_kwargs is None:
			rag_kwargs = {}

		# call rag and robustly handle error-shaped responses
		rag_res = None
		try:
			rag_res = _rag(question=problem.get('question'), context=context_text, system_prompt=system_prompt, **(rag_kwargs or {}))
		except TypeError:
			# try positional signature
			try:
				rag_res = _rag(problem.get('question'), context_text)
			except Exception:
				rag_res = None
		except Exception:
			rag_res = None

		# If rag produced something, inspect for error indicators
		if isinstance(rag_res, dict):
			# common pattern: {'answer': '...json with _error...'} or {'_error': '...'}
			ans_field = rag_res.get('answer') if 'answer' in rag_res else None
			err_field = rag_res.get('_error') or rag_res.get('error')
			if isinstance(ans_field, str) and ('"_error"' in ans_field or "'_error'" in ans_field or 'cannot produce json' in ans_field.lower()):
				# fallback to winner/text
				ans = winner.get('content') if winner and winner.get('content') else None
				if isinstance(ans, dict):
					short = self._extract_answer_from_proposal({'content': ans})
					if short:
						return short
					return json.dumps(ans, ensure_ascii=False)
				if ans:
					return str(ans)
				# else return raw answer field as last resort
				return ans_field
			# if explicit error field present
			if err_field:
				ans = winner.get('content') if winner and winner.get('content') else None
				if ans:
					if isinstance(ans, dict):
						short = self._extract_answer_from_proposal({'content': ans})
						if short:
							return short
						return json.dumps(ans, ensure_ascii=False)
					return str(ans)
				# final fallback
				return str(rag_res)

		# if rag returned a plain string, return it
		if isinstance(rag_res, str):
			return rag_res

		# else if rag produced something unexpected, fallback to winner
		ans = winner.get('content') if winner and winner.get('content') else None
		if isinstance(ans, dict):
			short = self._extract_answer_from_proposal({'content': ans})
			if short:
				return short
			return json.dumps(ans, ensure_ascii=False)
		if ans:
			return str(ans)

		# last resort
		return "[formatter-error] no valid formatted answer produced"


# === Phase-13: SubAgentManager (internal specialized agents) ===
class SubAgentManager:
	"""Manage simple domain-specialized sub-agents that route prompts to hosted LLM with specialized system prompts."""
	def __init__(self, hosted_llm_adapter=None):
		self.hosted_llm = hosted_llm_adapter
		self.agents = {
			"medical": {
				"name": "MedicalAgent",
				"system_prompt": "Ø£Ù†Øª Ø®Ø¨ÙŠØ± Ø·Ø¨Ù‘ÙŠ Ø¯Ù‚ÙŠÙ‚ØŒ ØªØ¬ÙŠØ¨ Ø¨Ø¥ÙŠØ¬Ø§Ø² ÙˆÙˆØ¶ÙˆØ­ ÙˆØ¨Ø£Ø³Ø§Ø³ Ø¹Ù„Ù…ÙŠ.",
				"prefer_engines": ["hosted_llm", "retriever"]
			},
			"math": {
				"name": "MathAgent",
				"system_prompt": "Ø£Ù†Øª Ø®Ø¨ÙŠØ± Ø±ÙŠØ§Ø¶ÙŠØ§ØªØŒ ØªØ­Ù„ Ø§Ù„Ù…Ø³Ø§Ø¦Ù„ Ø¨Ø®Ø·ÙˆØ§Øª ÙˆØ§Ø¶Ø­Ø©.",
				"prefer_engines": ["math", "proof", "hosted_llm"]
			},
			"planning": {
				"name": "PlannerAgent",
				"system_prompt": "Ø£Ù†Øª Ù…Ø®Ø·Ù‘Ø· Ù…Ø´Ø§Ø±ÙŠØ¹ØŒ ØªØ­ÙˆÙ‘Ù„ Ø§Ù„Ø£Ù‡Ø¯Ø§Ù Ø¥Ù„Ù‰ Ø®Ø·ÙˆØ§Øª Ø¹Ù…Ù„ÙŠØ©.",
				"prefer_engines": ["planner", "deliberation", "hosted_llm"]
			},
		}

	def detect_domain(self, question: str) -> str:
		q = (question or "")
		ql = q.lower()
		if any(w in ql for w in ["Ø¶ØºØ· Ø§Ù„Ø¯Ù…", "Ø§Ù„Ø³ÙƒØ±ÙŠ", "ÙƒÙ„ÙˆÙŠ", "Ø¯ÙˆØ§Ø¡", "Ù…Ø¶Ø§Ø¯Ø§Øª", "Ø£Ø¹Ø±Ø§Ø¶", "Ø¹Ù„Ø§Ø¬"]):
			return "medical"
		if any(w in ql for w in ["Ù…Ø¹Ø§Ø¯Ù„Ø©", "ØªÙƒØ§Ù…Ù„", "Ù…ØµÙÙˆÙØ©", "Ø§Ø­ØªÙ…Ø§Ù„", "probability", "matrix"]):
			return "math"
		if any(w in ql for w in ["Ø®Ø·Ø©", "Ù…Ø´Ø±ÙˆØ¹", "Ù…Ø±Ø§Ø­Ù„", "Ø®Ø·ÙˆØ§Øª", "schedule", "plan"]):
			return "planning"
		return "generic"

	def ask(self, question: str, context: str = "", timeout_s: float = 30.0) -> Dict[str, Any]:
		domain = self.detect_domain(question)
		cfg = self.agents.get(domain, {
			"name": "GenericAgent",
			"system_prompt": "Ø£Ù†Øª Ù…Ø³Ø§Ø¹Ø¯ Ø°ÙƒÙŠ Ø¹Ø§Ù….",
			"prefer_engines": ["hosted_llm"]
		})
		prompt = f"{cfg['system_prompt']}\n\nØ§Ù„Ø³Ø¤Ø§Ù„: {question}\nØ§Ù„Ø³ÙŠØ§Ù‚: {context}\n\nØ£Ø¬Ø¨ Ø¨Ø¯Ù‚Ø©."
		# If a hosted_llm adapter instance is available, try to call it with a safe inference API
		try:
			adapter = self.hosted_llm
			if adapter is None:
				# try to find a hosted_llm adapter from builtins if present
				for a in (getattr(globals().get('CognitiveIntegrationEngine')(), 'adapters', []) or []):
					if getattr(a, 'name', '').lower() == 'hosted_llm':
						adapter = a
						break
			if adapter is not None and hasattr(adapter, 'infer'):
				out = adapter.infer({'question': question, 'context': context, 'system_prompt': cfg['system_prompt']}, timeout_s=timeout_s)
				# normalize to expected dict
				if isinstance(out, dict):
					return {"domain": domain, "agent": cfg['name'], "answer": out}
				return {"domain": domain, "agent": cfg['name'], "answer": {"engine": getattr(adapter, 'name', 'hosted_llm'), 'content': str(out)}}
		except Exception as e:
			return {"domain": domain, "agent": cfg['name'], "answer": {"error": str(e)}}
		return {"domain": domain, "agent": cfg['name'], "answer": {"answer": "no-hosted-adapter"}}


# === Phase-14: Thinking Policy (dynamic switching) ===
def choose_thinking_policy(problem: Dict[str, Any], self_model: Optional[object], session_state: Dict[str, Any], strategic_hints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
	"""Return policy: domain, reliability, mode, cot_samples, use_verification"""
	try:
		question = (problem.get('question') or problem.get('title') or '') if isinstance(problem, dict) else str(problem)
	except Exception:
		question = str(problem or '')
	ql = question.lower()
	# basic domain detect
	domain = 'generic'
	if any(t in ql for t in ('Ø³ÙƒØ±', 'Ø¶ØºØ· Ø§Ù„Ø¯Ù…', 'Ø¯ÙˆØ§Ø¡', 'Ø¹Ù„Ø§Ø¬', 'Ø£Ø¹Ø±Ø§Ø¶', 'medical', 'pharmacy')):
		domain = 'medical'
	elif any(t in ql for t in ('Ù…Ø¹Ø§Ø¯Ù„Ø©', 'ØªÙƒØ§Ù…Ù„', 'matrix', 'probability', 'Ø§Ø­ØªÙ…Ø§Ù„')):
		domain = 'math'
	elif any(t in ql for t in ('Ø®Ø·Ø©', 'Ù…Ø´Ø±ÙˆØ¹', 'steps', 'plan', 'schedule')):
		domain = 'planning'
	# fallback to self_model if available
	reliability = 0.5
	try:
		if self_model is not None and hasattr(self_model, 'reliability'):
			reliability = float(self_model.reliability(domain) or 0.5)
	except Exception:
		reliability = 0.5
	mode = 'fast'
	cot_samples = 1
	use_verification = False
	if reliability >= 0.75:
		mode = 'fast'; cot_samples = 1; use_verification = False
	elif reliability >= 0.5:
		mode = 'cot_short'; cot_samples = 2; use_verification = True
	elif reliability >= 0.3:
		mode = 'cot_long'; cot_samples = 3; use_verification = True
	else:
		mode = 'rag_heavy'; cot_samples = 3; use_verification = True
	# allow strategic hints to override
	try:
		if strategic_hints and isinstance(strategic_hints, dict):
			if 'mode' in strategic_hints:
				mode = strategic_hints.get('mode')
			if 'cot_samples' in strategic_hints:
				cot_samples = int(strategic_hints.get('cot_samples') or cot_samples)
			if 'use_verification' in strategic_hints:
				use_verification = bool(strategic_hints.get('use_verification'))
	except Exception:
		pass
	return {"domain": domain, "reliability": reliability, "mode": mode, "cot_samples": cot_samples, "use_verification": use_verification}


def run_multi_step_qa(problem: Dict[str, Any], engines: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Ø§Ù„Ù…Ø±Ø­Ù„Ø© 4: Ø­Ù„ Ù…Ù‡Ø§Ù… Ù…ØªØ¹Ø¯Ø¯Ø© Ø§Ù„Ø®Ø·ÙˆØ§Øª.
	- ÙŠØ³ØªØ®Ø¯Ù… planner Ø¨Ø³ÙŠØ· (simple_step_split) + hosted_llm
	- ÙŠØ³Ø¬Ù„ ØªØ³Ù„Ø³Ù„ Ø§Ù„ØªÙ†ÙÙŠØ° ÙÙŠ timeline Ø¨Ø³ÙŠØ· Ø¯Ø§Ø®Ù„ Ø§Ù„Ù†ØªÙŠØ¬Ø©.
	"""
	question = problem.get("question") or problem.get("title", "")
	if not question:
		raise ValueError("run_multi_step_qa: missing question in problem")

	# 1) ØªÙˆÙ„ÙŠØ¯ Ø§Ù„Ø®Ø·ÙˆØ§Øª (Ø¨Ø¯ÙŠÙ„ planner Ø§Ù„Ø®Ø§Ø±Ø¬ÙŠ Ø£Ùˆ Ù…ÙƒÙ…Ù„ Ù„Ù‡)
	steps = simple_step_split(question)

	hosted = engines.get("hosted_llm")
	if hosted is None:
		# try to find any adapter with name hosted_llm in engines
		for k, v in (engines or {}).items():
			if str(k).lower() == 'hosted_llm':
				hosted = v; break

	if hosted is None:
		raise RuntimeError("run_multi_step_qa: hosted_llm engine is required")

	sub_answers = []
	events = []
	t0 = time.time()

	for i, step in enumerate(steps, start=1):
		ts = time.time()
		# Ù†Ù…Ø±Ø± Ø®Ø·ÙˆØ© ÙØ±Ø¹ÙŠØ© Ù„Ù„Ù€ hosted_llm
		llm_task = {
			"question": step,
			"task_type": "qa_single",
			"use_cot": True,
		}
		try:
			# Prefer process_task if available
			if hasattr(hosted, 'process_task'):
				llm_result = hosted.process_task(llm_task)
			elif hasattr(hosted, 'infer'):
				llm_result = hosted.infer({'question': step}, timeout_s=10.0)
			else:
				raise RuntimeError('no-processable-method')

			content = llm_result.get("content", llm_result) if isinstance(llm_result, dict) else llm_result
			raw_answer = content.get("answer", content) if isinstance(content, dict) else content
			plain_answer = extract_plain_answer(raw_answer).strip()
			if not plain_answer or len(plain_answer) < 20:
				plain_answer = f"Ø¥Ø¬Ø§Ø¨Ø© Ù…ÙˆØ¬Ø²Ø©: {plain_answer or step}"
		except Exception as e:
			plain_answer = f"(ØªØ¹Ø°Ø± Ø§Ù„Ø­ØµÙˆÙ„ Ø¹Ù„Ù‰ Ø¥Ø¬Ø§Ø¨Ø© Ù„Ù‡Ø°Ù‡ Ø§Ù„Ø®Ø·ÙˆØ©: {e})"

		sub_answers.append({
			"step": step,
			"answer": plain_answer,
		})
		events.append({
			"t": f"step_{i}",
			"ts": ts,
			"note": step[:80],
		})

	# 2) Ø¯Ù…Ø¬ Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø§Øª
	merged = ["Ø¥Ø¬Ø§Ø¨Ø© Ù…Ø±ÙƒÙ‘Ø¨Ø© Ù„Ù„Ø³Ø¤Ø§Ù„:", f"Â«{question}Â»", ""]
	for idx, sa in enumerate(sub_answers, start=1):
		merged.append(f"{idx}. {sa['answer']}")
	final_answer = "\n".join(merged)

	# 3) ØªØ¬Ù…ÙŠØ¹ Ø§Ù„Ù†ØªÙŠØ¬Ø© Ø¨Ù†ÙØ³ Ø£Ø³Ù„ÙˆØ¨ agl_pipeline Ø§Ù„Ù…Ø¹ØªØ§Ø¯ Ù‚Ø¯Ø± Ø§Ù„Ø¥Ù…ÙƒØ§Ù†
	total_time = time.time() - t0
	result = {
		"answer": final_answer,
		"sub_answers": sub_answers,
		"provenance": {
			"engine": "multi_step_qa_v1",
			"steps": steps,
			"events": events,
			"latency_s": round(total_time, 3),
		},
	}
	result["task_type"] = "qa_multi"
	return result


def agl_pipeline(question: str, *, mode: str = "default", cie: Optional[CognitiveIntegrationEngine] = None, session_state: Optional[SessionState] = None, **kwargs) -> dict:
	"""
	Central AGL pipeline wrapper that unifies safety, memory recall, collaborative solving,
	final formatting and memory writeback.

	Returns dict: {"answer": str, "provenance": dict, "raw": dict}
	"""
	# 0) prepare CIE
	created = False
	if cie is None:
		cie = CognitiveIntegrationEngine()
		created = True
	try:
		cie.connect_engines()
	except Exception:
		pass

	# 0.5) session state management: attach or create
	try:
		if session_state is None:
			session_state = SessionState(session_id=str(uuid.uuid4())[:8])
		# attach minimal problem record
		try:
			session_state.current_problem = {"title": question, "question": question}
		except Exception:
			pass
		# mark initial stage and attach to CIE so internal methods can update used_engines
		try:
			session_state.stage = "fanout"
			setattr(cie, 'session_state', session_state)
		except Exception:
			pass
	except Exception:
		session_state = None

	# runtime context helper + initialize runtime context for situational awareness (Phase-9)
	def _new_runtime_context(problem_title: str) -> dict:
		return {
			"problem_id": str(uuid.uuid4())[:8],
			"title": problem_title,
			"stage": "init",
			"progress": 0.0,
			"attempts": 0,
			"last_error": None,
			"started_at": time.time(),
			"finished_at": None,
		}

	# initialize or increment runtime context attempts
	runtime_ctx = None
	try:
		runtime_ctx = getattr(session_state, 'runtime_context', None) or _new_runtime_context(question)
		runtime_ctx['attempts'] = int(runtime_ctx.get('attempts', 0) or 0) + 1
		runtime_ctx['stage'] = 'analysis'
		# persist back to session_state and cie where possible
		if session_state is not None:
			session_state.runtime_context = runtime_ctx
			setattr(cie, 'session_state', session_state)
	except Exception:
		try:
			runtime_ctx = _new_runtime_context(question)
		except Exception:
			runtime_ctx = {"problem_id": "", "title": question}

	# >>> PHASE-4: detect multi-step questions and route to run_multi_step_qa
	try:
		# wrap main execution so we can record runtime errors and attempts
		# any exception raised here will be captured and reflected in runtime_ctx
		# (Phase-9 situational awareness)
		# infer task type using simple heuristic unless caller provided it
		task_type = None
		if isinstance(kwargs.get('context'), dict):
			task_type = kwargs.get('context', {}).get('task_type')
		if not task_type:
			task_type = infer_task_type(question)
		if task_type == 'qa_multi':
			# prepare problem object
			problem = {"title": question, "question": question, "context": kwargs.get('context') or {}, "task_type": task_type}
			# build engines map from connected CIE adapters
			engines_map = {}
			try:
				for a in getattr(cie, 'adapters', []) or []:
					name = getattr(a, 'name', None) or str(type(a).__name__)
					engines_map[name] = a
			except Exception:
				pass
			# ensure hosted_llm fallback if missing
			if 'hosted_llm' not in engines_map:
				try:
					from agl.engines.self_improvement.Self_Improvement.hosted_llm_adapter import HostedLLMAdapter
					engines_map['hosted_llm'] = HostedLLMAdapter()
				except Exception:
					# simple shim adapter
					class _Shim:
						name = 'hosted_llm'
						def process_task(self, task):
							q = task.get('question') if isinstance(task, dict) else str(task)
							return {'content': {'answer': f'Ø¥Ø¬Ø§Ø¨Ø© Ù…Ø¨Ø³Ø·Ø© Ù…Ø¤Ù‚ØªØ© Ø¹Ù„Ù‰: {q}'}}
					engines_map['hosted_llm'] = _Shim()
			try:
				multi_res = run_multi_step_qa(problem, engines_map)
				multi_res['task_type'] = 'qa_multi'
				# attach runtime context into provenance for situational awareness
				try:
					prov = multi_res.get('provenance') or {}
					prov['runtime_context'] = runtime_ctx
					multi_res['provenance'] = prov
				except Exception:
					pass
				return multi_res
			except Exception:
				# fail and continue to normal pipeline
				pass

	except Exception as _pipeline_exc:
		# record top-level pipeline exception into runtime context and return friendly message
		try:
			runtime_ctx['stage'] = 'analysis_retry'
			runtime_ctx['last_error'] = str(_pipeline_exc)
			runtime_ctx['finished_at'] = time.time()
		except Exception:
			pass
		# prepare safe fallback provenance/answer
		fallback_prov = {"engine": "agl_pipeline", "note": "exception_during_pipeline"}
		try:
			fallback_prov['runtime_context'] = runtime_ctx
		except Exception:
			pass
		fallback_answer = "Ø¹Ø°Ø±Ø§Ù‹ØŒ Ø­Ø¯Ø« Ø®Ø·Ø£ Ø£Ø«Ù†Ø§Ø¡ Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø·Ù„Ø¨ ÙÙŠ Ø§Ù„ÙˆÙ‚Øª Ø§Ù„Ø­Ø§Ù„ÙŠ."
		return {"answer": fallback_answer, "provenance": fallback_prov, "raw": {}}
	# 1) safety pre-check (keyword heuristics + critic if available) and logging
	try:
		# local safe import for the logger (best-effort)
		try:
			from agl.engines.self_improvement.Self_Improvement.safety_log import log_safety_event # type: ignore
		except Exception:
			def log_safety_event(source, level, message, extra=None):
				return None

		text = (question or "").lower()
		blocked_keywords = [
			"Ø§Ù†ØªØ­Ø§Ø±", "ØªÙØ¬ÙŠØ±", "ÙƒÙŠÙÙŠØ© ØµÙ†Ø¹ Ù‚Ù†Ø¨Ù„Ø©",
			"suicide", "bomb", "detonate", "how to make a bomb",
		]
		blocked = any(kw in text for kw in blocked_keywords)

		critic_flag = False
		crit = None
		critic_available = 'critic' in (getattr(cie, 'engines_registry', {}) or {})
		if critic_available:
			try:
				crit = cie.query_engine('critic', {'title': question})
				crit_txt = json.dumps(crit.get('result') or crit, ensure_ascii=False) if isinstance(crit, dict) else str(crit)
				low = crit_txt.lower()
				critic_flag = any(k in low for k in ('risk', 'unsafe', 'forbid', 'danger', 'illegal'))
			except Exception:
				critic_flag = False

		if blocked or critic_flag:
			if blocked and critic_flag:
				msg = "blocked by safety gate (keywords+critic)"
			elif blocked:
				msg = "blocked by safety gate (keywords)"
			else:
				msg = "blocked by safety gate (critic)"
			# record event
			try:
				log_safety_event("agl_pipeline", "block", msg, {"question": question, "keywords_blocked": blocked, "critic_flag": critic_flag, "critic": crit})
			except Exception:
				pass
			safe_answer = (
				"Ø¹Ø°Ø±Ø§Ù‹ØŒ Ù„Ø§ ÙŠÙ…ÙƒÙ†Ù†ÙŠ Ø§Ù„Ù…Ø³Ø§Ø¹Ø¯Ø© ÙÙŠ Ù‡Ø°Ø§ Ø§Ù„Ù†ÙˆØ¹ Ù…Ù† Ø§Ù„Ø·Ù„Ø¨Ø§Øª Ø­Ø±ØµÙ‹Ø§ Ø¹Ù„Ù‰ Ø§Ù„Ø³Ù„Ø§Ù…Ø© "
				"ÙˆØ§Ù„Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ù…Ø³Ø¤ÙˆÙ„ Ù„Ù„Ù†Ø¸Ø§Ù…."
			)
			# include runtime context in provenance when returning due to safety
			try:
				prov = {"safety": msg}
				prov['runtime_context'] = runtime_ctx
			except Exception:
				prov = {"safety": msg}
			return {"answer": safe_answer, "provenance": prov, "raw": {"answer": safe_answer, "engine": "safety-gate"}}


		# passed safety
		try:
			log_safety_event("agl_pipeline", "info", "passed safety check", {"question": question})
		except Exception:
			pass
	except Exception:
		# swallow any unexpected safety-check errors
		pass

	# 2) RAG-lite memory recall to build context_text (prefer semantic index)
	context_text = ""
	try:
		try:
			from agl.engines.self_improvement.Self_Improvement.rag_lite import build_rag_context # type: ignore
		except Exception:
			build_rag_context = None

		mem_sys = getattr(cie, 'memory', None) or getattr(cie, 'collective', None)
		if build_rag_context is not None and mem_sys is not None:
			try:
				context_text = build_rag_context(question, memory_system=mem_sys, max_items=5) or ""
			except Exception:
				context_text = ""
		else:
			# fallback to previous behavior using collective if available
			try:
				coll = getattr(cie, 'collective', None)
				if coll is not None:
					words = [w for w in re.split(r"\W+", question) if len(w) > 3]
					keywords = words[:6]
					mem = coll.query_shared_memory(keywords=keywords, limit=10)
					if mem:
						synth = coll.synthesize(mem)
						context_text = json.dumps(synth, ensure_ascii=False)
			except Exception:
				context_text = ""
	except Exception:
		context_text = ""

	# EmergencyRetrieval fallback: if RAG-lite produced no context, try the emergency retriever
	try:
		if (not context_text) and EmergencyRetrieval is not None and hasattr(cie, 'engines_registry'):
			try:
				# conservative domain inference: try global infer function if available, else default
				domain = "general"
				try:
					if 'infer_domains_from_question' in globals() and callable(globals().get('infer_domains_from_question')):
						doms = globals().get('infer_domains_from_question')(question)
						if doms:
							domain = doms[0]
				except Exception:
					pass

				er = EmergencyRetrieval(cie)
				er_res = er.retrieve(question, domain)
				merged = None
				if isinstance(er_res, dict):
					merged = er_res.get('merged')
				else:
					merged = er_res

				if isinstance(merged, dict):
					emergency_ctx = merged.get('merged', "")
				else:
					emergency_ctx = str(merged or "")

				if emergency_ctx:
					tag = "[EMERGENCY_CONTEXT]"
					if context_text:
						context_text = f"{context_text}\n\n{tag}\n{emergency_ctx}"
					else:
						context_text = f"{tag}\n{emergency_ctx}"
			except Exception:
				# swallow emergency retriever exceptions; keep pipeline resilient
				pass
	except Exception:
		pass

	# 3) run collaborative solver
	# --- Phase-10: StrategicMemory integration (advanced strategic memory)
	try:
		from agl.engines.self_improvement.Self_Improvement.strategic_memory import StrategicMemory
		sm = StrategicMemory.default()
	except Exception:
		sm = None
	# infer domains from the question unless the caller provided explicit domains
	def infer_domains_from_question(q: str):
		"""Lightweight domain inference from question text.
		Returns a list/tuple of domain tags used by the routing layer.
		This is intentionally conservative and editable; add keywords as needed.
		"""
		if not q or not isinstance(q, str):
			return ("general",)
		q_strip = q.strip()
		q_low = q_strip.lower()

		# Study / definition / explain-type questions
		# Enhanced knowledge triggers (Arabic + English)
		knowledge_keywords_ar = [
			'Ù…Ø§ Ù‡ÙŠ', 'ÙƒÙŠÙ', 'Ù„Ù…Ø§Ø°Ø§', 'Ù…ØªÙ‰', 'Ø£ÙŠÙ†', 'Ù…Ø§Ø°Ø§',
			'Ø£Ø¹Ø±Ø§Ø¶', 'Ø¹Ù„Ø§Ø¬', 'Ø£Ø³Ø¨Ø§Ø¨', 'Ù†ØªÙŠØ¬Ø©', 'ØªØ¹Ø±ÙŠÙ',
			'Ø´Ø±Ø­', 'ØªÙØ³ÙŠØ±', 'Ù…Ø¹Ù„ÙˆÙ…Ø§Øª', 'Ø¨Ø­Ø«', 'Ø¯Ø±Ø§Ø³Ø©'
		]
		knowledge_keywords_en = [
			'what is', 'how to', 'why', 'when', 'where',
			'symptoms', 'treatment', 'causes', 'explain',
			'definition', 'information', 'research'
		]
		# Check enhanced knowledge keywords first
		ql = q_low
		try:
			if any(kw in ql for kw in knowledge_keywords_ar + knowledge_keywords_en):
				return ("knowledge", "analysis")
		except Exception:
			pass

		# Study / definition / explain-type questions (fallback)
		study_triggers = ["Ø§Ø´Ø±Ø­", "Ù…Ø§ Ù‡Ùˆ", "Ù…Ø§ Ù‡ÙŠ", "Ø¹Ø±Ù", "Ø¹Ø±Ù‘Ù", "explain", "what is", "define"]
		if any(t in q_strip for t in study_triggers) or any(t in q_low for t in study_triggers):
			return ("analysis", "knowledge", "science")

		# Health / pharmacy-related
		health_triggers = ["Ø¯ÙˆØ§Ø¡", "Ø§Ù„Ø£Ø¯ÙˆÙŠØ©", "ÙˆØµÙØ§Øª", "ØµÙŠØ¯Ù„ÙŠØ§Øª", "ØªÙ‡Ø±ÙŠØ¨ Ø§Ù„Ø£Ø¯ÙˆÙŠØ©", "Ù…Ø£Ø±Ø¨", "medical", "pharmacy", "clinical"]
		if any(t in q_strip for t in health_triggers) or any(t in q_low for t in health_triggers):
			return ("health", "pharmacy", "analysis")

		# Math / probability / linear algebra
		math_triggers = ["Ø§Ø­ØªÙ…Ø§Ù„", "ÙØ¶Ø§Ø¡ Ø§Ù„Ø¹ÙŠÙ†Ø©", "Ù…ØµÙÙˆÙØ©", "Ù…ØµÙÙˆÙØ§Øª", "probability", "matrix", "linear algebra"]
		if any(t in q_strip for t in math_triggers) or any(t in q_low for t in math_triggers):
			return ("math", "analysis")

		# Creativity / brainstorming
		creative_triggers = ["Ø£ÙÙƒØ§Ø±", "Ø§Ø¨ØªÙƒØ§Ø±", "ÙÙƒØ±Ø© Ø¬Ø¯ÙŠØ¯Ø©", "ideas", "brainstorm", "creative"]
		if any(t in q_strip for t in creative_triggers) or any(t in q_low for t in creative_triggers):
			return ("creativity", "synthesis")

		# Default
		raw = ("general",)
		# canonicalize against known capability domain tags to help routing
		_allowed = set()
		try:
			for v in ENGINE_CAPABILITIES.values():
				for d in (v.get("domains") or []):
					_allowed.add(d)
		except Exception:
			_allowed = set()

		# synonyms mapping to preferred capability tags
		synonyms = {
			"health": ["knowledge", "analysis", "governance"],
			"pharmacy": ["knowledge", "analysis"],
			"science": ["analysis", "math"],
			"general": ["language", "analysis", "knowledge"],
			"creativity": ["creativity", "synthesis"],
			"math": ["math", "analysis"],
		}

		out = []
		for d in raw:
			if d in _allowed:
				out.append(d)
			else:
				cands = synonyms.get(d, [])
				for c in cands:
					if c in _allowed:
						out.append(c); break

		if out:
			return tuple(dict.fromkeys(out))
		# fallback to a safe set
		return ("language", "analysis", "knowledge")

	# Attempt to enrich the question with learned facts and RAG context.
	# When FAST_MODE is active we must not load or inject any memory or RAG
	# context to avoid cross-question contamination during tests.
	question_for_engines = question
	learned_ctx = ""
	rag_ctx = ""
	try:
		FAST_MODE = os.getenv("AGL_FAST_MODE", "0") == "1"
	except Exception:
		FAST_MODE = False
	if not FAST_MODE:
		try:
			learned_ctx = load_learned_facts_as_context(max_items=20) or ""
		except Exception:
			learned_ctx = ""
		try:
			if learned_ctx:
				# prepend learned facts to the question for downstream engines to use
				question_for_engines = (
					question
					+ "\n\n" + "Ù…Ù‚ØªØ·ÙØ§Øª Ù…Ù† Ù…Ø¹Ø±ÙØ© Ù…ÙƒØªØ³ÙŽØ¨Ø© Ø³Ø§Ø¨Ù‚Ù‹Ø§ (Ù‚Ø¯ ØªØ³Ø§Ø¹Ø¯ ÙÙŠ Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø©):\n"
					+ learned_ctx
				)
		except Exception:
			question_for_engines = question
		# RAG (vector) retrieval integration: retrieve docs and attach to prob/rag_context
		try:
			rag_ctx = retrieve_context(question, k=5) if callable(retrieve_context) else ""
		except Exception:
			rag_ctx = ""
		try:
			if rag_ctx:
				# prepend RAG docs above learned facts to give retrieved evidence priority
				question_for_engines = (str(rag_ctx) + "\n\n---\n\n" + question_for_engines)
		except Exception:
			pass

	prob = {"title": question, "question": question_for_engines, "context": context_text or "", "task_type": "qa_single", "rag_context": rag_ctx}
	# attach strategic hints if available (Phase-10 StrategicMemory)
	try:
		if sm is not None:
			try:
				if hasattr(sm, 'suggest_for'):
					hints = sm.suggest_for(prob)
				else:
					hints = sm.suggest_strategy(task_type=prob.get('task_type'), title=prob.get('title'))
				prob['hints'] = hints
				try:
					runtime_ctx['strategy'] = hints
				except Exception:
					pass
			except Exception:
				pass
	except Exception:
		pass
	# allow explicit override via kwargs['domains'] (list/tuple)
	domains_needed = kwargs.get('domains')
	if not domains_needed:
		domains_needed = infer_domains_from_question(question)

	# Quick protective filter: if the inferred domains are not creative, remove generative adapters early
	try:
		if 'creativity' not in (domains_needed or ()): 
			try:
				cie.adapters = [a for a in (getattr(cie, 'adapters', []) or []) if getattr(a, 'name', None) != 'gen_creativity']
			except Exception:
				pass
	except Exception:
		pass

	# If CIE already connected adapters earlier, reorder adapters to prefer engines
	# that match the inferred domains. This is a lightweight, local routing override
	# that biases which adapters are queried first without changing global logic.
	try:
		if getattr(cie, 'adapters', None):
			# mapping from domain -> preferred engine names (order matters)
			_pref_map = {
				'knowledge': ['hosted_llm', 'retriever', 'hosted_storyqa', 'reason', 'analysis'],
				'analysis': ['reason', 'analysis', 'summarize', 'critic'],
				'math': ['math', 'proof'],
				'creativity': ['gen_creativity'],
				'creative': ['gen_creativity', 'vision', 'audio'],
				'pharmacy': ['hosted_llm', 'retriever', 'hosted_storyqa'],
				'health': ['hosted_llm', 'retriever'],
				'general': ['hosted_llm', 'retriever', 'summarize'],
				'strategic': ['planner', 'deliberation'],
			}
			preferred_names = []
			for d in (domains_needed or ()): 
				for name in _pref_map.get(d, []):
					if name not in preferred_names:
						preferred_names.append(name)

			# stable reorder: preferred adapters first in same relative order
			if preferred_names:
				new_adapters = []
				remaining = []
				for a in list(getattr(cie, 'adapters') or []):
					an = getattr(a, 'name', None) or str(type(a).__name__)
					if an in preferred_names:
						new_adapters.append(a)
					else:
						remaining.append(a)
				# preserve order: preferred then remaining
				cie.adapters = new_adapters + remaining

			# simple protective filter: if the inferred domains do not include creativity,
			# remove generative creativity adapters so they don't dominate factual Q&A.
			try:
				if 'creativity' not in (domains_needed or ()): 
					cie.adapters = [a for a in cie.adapters if getattr(a, 'name', None) != 'gen_creativity']
			except Exception:
				pass
				# also update engines_registry metadata ordering if present
				try:
					order_map = {getattr(a,'name',None): idx for idx,a in enumerate(cie.adapters)}
					cie.engines_registry = {n: cie.engines_registry.get(n,{}) for n in sorted(cie.engines_registry.keys(), key=lambda x: order_map.get(x, 999999))}
				except Exception:
					pass
		# temporarily disable automatic connect_engines() to preserve our adapter ordering
		_res = None
		_orig_connect = getattr(cie, 'connect_engines', None)
		try:
			# replace with no-op
			if _orig_connect:
				setattr(cie, 'connect_engines', lambda: None)
				_res = cie.collaborative_solve(prob, domains_needed=domains_needed)
			else:
				_res = cie.collaborative_solve(prob, domains_needed=domains_needed)
		finally:
			# restore
			if _orig_connect:
				setattr(cie, 'connect_engines', _orig_connect)
		res = _res
		# Enforce hosted_llm preference for knowledge-like questions: check the
		# raw question text for knowledge triggers (fallback when _is_knowledge_question
		# heuristics don't match). If matched, invoke hosted_llm and promote its
		# answer when substantial.
		try:
			q_text = (prob.get('question') if isinstance(prob, dict) else str(prob)) or ""
			q_low = str(q_text).lower()
			knowledge_triggers = ['Ù…Ø§ Ù‡ÙŠ', 'Ù…Ø§Ù‡ÙŠ', 'Ù…Ø§ Ù‡Ùˆ', 'Ù…Ø§Ù‡Ùˆ', 'Ø§Ø¹Ø±Ø§Ø¶', 'Ø£Ø¹Ø±Ø§Ø¶', 'symptoms', 'treatment', 'what is', 'define', 'explain']
			is_knowledge_q = any(t in q_low for t in knowledge_triggers)
			# Diagnostic prints requested by user: show arbiter/problem/candidates state
			try:
				cands = []
				for p in (res.get('top') or []):
					eng = p.get('engine')
					cont = p.get('content') or {}
					has_ans = False
					if isinstance(cont, dict):
						has_ans = bool(str(cont.get('answer') or '').strip())
					elif isinstance(cont, str):
						has_ans = bool(cont.strip())
					cands.append((eng, has_ans))

				# Prefer RAG proposals for knowledge-like queries or when learned facts exist
				try:
					rag_prop = None
					for p in (res.get('top') or []):
						if (p.get('engine') or '').lower() == 'rag':
							rag_prop = p; break
					if rag_prop is not None:
						promote = False
						try:
							if 'knowledge' in (domains_needed or ()): promote = True
						except Exception:
							pass
						try:
							# if learned facts were prepended earlier, prefer RAG evidence
							if learned_ctx and learned_ctx.strip():
								promote = True
						except Exception:
							pass
						if promote:
							try:
								rag_prop['score'] = max(float(rag_prop.get('score', 0.0) or 0.0), 0.9)
								res = res or {}
								res['winner'] = rag_prop
								top_list = [rag_prop] + [p for p in (res.get('top') or []) if p is not rag_prop]
								res['top'] = top_list
							except Exception:
								pass
				except Exception:
					pass
				# also include adapters list presence for hosted_llm
				hosted_adapter_present = any((getattr(a, 'name', '') or '').lower() == 'hosted_llm' for a in (getattr(cie, 'adapters', []) or []))
				print("[ARBITER] problem:", repr(prob))
				print("[ARBITER] is_knowledge:", is_knowledge_q)
				print("[ARBITER] candidates:", cands)
				print("[ARBITER] hosted_adapter_present:", hosted_adapter_present)
			except Exception:
				pass
			# Determine if RAG already provided a strong extractive answer; if so,
			# skip promoting hosted_llm to avoid overriding factual evidence.
			try:
				rag_prop = None
				for p in (res.get('top') or []):
					if (p.get('engine') or '').lower() == 'rag':
						rag_prop = p; break
				rag_has_ans = False
				try:
					if rag_prop is not None:
						cont = rag_prop.get('content') or {}
						rag_has_ans = bool((cont.get('answer') or '').strip()) if isinstance(cont, dict) else bool(str(cont).strip())
				except Exception:
					rag_has_ans = False
			except Exception:
				rag_prop = None; rag_has_ans = False

			if (('knowledge' in (domains_needed or ())) or is_knowledge_q) and not (rag_prop and rag_has_ans):
				for a in getattr(cie, 'adapters', []) or []:
					try:
						if getattr(a, 'name', '').lower() == 'hosted_llm':
							alt = None
							try:
								alt = a.infer(prob if isinstance(prob, dict) else {'question': str(prob)}, timeout_s=_safe_float(os.getenv('AGL_OLLAMA_CLI_TIMEOUT', '600')))
							except Exception:
								alt = None
							if alt and isinstance(alt, dict):
								ans = None
								try:
									ans = CognitiveIntegrationEngine._extract_answer_from_proposal(alt)
								except Exception:
									ans = None
								if ans:
									# promote alt to winner/top
									res = res or {}
									res['winner'] = alt
									res['top'] = [alt] + (res.get('top') or [])
									break
					except Exception:
						continue
		except Exception:
			pass
	except Exception:
		# fallback to using answer_question convenience if available
		try:
			out = cie.answer_question(question, context=context_text or "", language=kwargs.get('language', 'ar'))
			return {"answer": out.get('formatted_answer'), "provenance": out.get('cie_result'), "raw": out.get('cie_result')}
		except Exception as e:
			# include runtime_context in fallback provenance when available
			# annotate runtime context with the error
			try:
				runtime_ctx['stage'] = 'analysis_retry'
				runtime_ctx['last_error'] = str(e)
				runtime_ctx['finished_at'] = time.time()
			except Exception:
				pass
			try:
				prov = {}
				prov['runtime_context'] = runtime_ctx
			except Exception:
				prov = {}
			return {"answer": f"Ø®Ø·Ø£ Ø¯Ø§Ø®Ù„ÙŠ: {e}", "provenance": prov, "raw": {}}

	# 4) final formatting with fallback
	try:
		final = cie.format_final_answer(prob, res, system_prompt=kwargs.get('system_prompt'))
	except Exception:
		final = None

	# improved pretty-formatting for gen_creativity ideas
	try:
		# if final is JSON-like string, try parse
		parsed = None
		if isinstance(final, str):
			try:
				parsed = json.loads(final)
			except Exception:
				parsed = None
		elif isinstance(final, dict):
			parsed = final

		if isinstance(parsed, dict) and parsed.get('ideas') and isinstance(parsed.get('ideas'), list):
			lines = ["Ø£Ù†ØªØ¬ Ø§Ù„Ù†Ø¸Ø§Ù… Ø§Ù„Ø£ÙÙƒØ§Ø± Ø§Ù„ØªØ§Ù„ÙŠØ©:"]
			for it in parsed.get('ideas'):
				txt = it.get('idea') if isinstance(it, dict) else str(it)
				lines.append(f"- {txt}")
			final = "\n".join(lines)
	except Exception:
		pass

	# 5) write memory/experience
	try:
		# write to collective memory
		try:
			if getattr(cie, 'collective', None) is not None:
				cie.collective.share_learning('agl_pipeline', {'question': question, 'winner': res.get('winner'), 'top': res.get('top')}, verified_by=[])
		except Exception:
			pass
		# write STM if memory present
		try:
			if getattr(cie, 'memory', None) is not None and hasattr(cie.memory, 'write_stm'):
				cie.memory.write_stm({'question': question, 'winner': res.get('winner'), 'ts': _ts()})
		except Exception:
			pass
	except Exception:
		pass

	# update session_state to final and persist
	try:
		ss = getattr(cie, 'session_state', None) or session_state
		if ss is not None:
			try:
				ss.stage = "final_answer"
				_save_session_state(ss)
			except Exception:
				pass
	except Exception:
		pass
	# detect adapter-level error markers inside result/provenance and map them to runtime_ctx
	try:
		_serialized = json.dumps(res or {}, ensure_ascii=False)
		if 'simulated failure' in _serialized or 'simulated failure for testing' in _serialized:
			try:
				runtime_ctx['stage'] = 'analysis_retry'
				runtime_ctx['last_error'] = 'simulated failure for testing'
				runtime_ctx['finished_at'] = time.time()
			except Exception:
				pass
	except Exception:
		pass

	# attach runtime_context into the provenance before returning
	try:
		# mark successful execution in runtime context
		try:
			runtime_ctx['stage'] = 'execution'
			runtime_ctx['progress'] = 1.0
			runtime_ctx['last_error'] = None
			runtime_ctx['finished_at'] = time.time()
		except Exception:
			pass
		# record outcome into StrategicMemory if available
		if sm is not None:
			try:
				title = (prob.get('title') if isinstance(prob, dict) else question) if 'prob' in locals() else question[:120]
				prov = res if isinstance(res, dict) else {}
				fallback_marker = "Ø¹Ø°Ø±Ø§ØŒ Ù„Ø§ Ø£Ø³ØªØ·ÙŠØ¹ ØªÙˆÙÙŠØ± Ø¥Ø¬Ø§Ø¨Ø© Ù…Ø¤ÙƒØ¯Ø©"
				answer_text = final or ""
				# basic success heuristic for QA
				success = None
				try:
					if (task_type or '').startswith('qa_'):
						success = bool(answer_text and fallback_marker not in answer_text)
				except Exception:
					success = None
				# determine score if available
				score = None
				try:
					if isinstance(prov.get('winner', {}), dict):
						score = prov.get('winner', {}).get('score')
					elif isinstance(prov.get('score'), dict) and 'overall' in prov.get('score'):
						score = prov.get('score').get('overall')
					else:
						score = prov.get('score')
				except Exception:
					score = None
				# record (best-effort)
				try:
					sm.record_outcome(
						title=title,
						task_type=(task_type or 'qa_single'),
						score=score,
						success=success,
						meta={"engine": prov.get('engine') or (prov.get('winner') or {}).get('engine')},
						strategy=runtime_ctx.get('strategy') if isinstance(runtime_ctx, dict) else None,
					)
				except Exception:
					pass
			except Exception:
				pass
		if isinstance(res, dict):
			# embed runtime_context under provenance
			res['runtime_context'] = runtime_ctx
	except Exception:
		pass
	return {"answer": final, "provenance": res, "raw": res}
# Stage-5: perception tick (embodied perception step)

	def tick(self, goal=None):
		"""Minimal perceptionâ†’actâ†’learn step."""
		obs = {
			"vision": getattr(self, 'pbus', None) and self.pbus.latest("vision"),
			"audio":  getattr(self, 'pbus', None) and self.pbus.latest("audio"),
			"sensor": getattr(self, 'pbus', None) and self.pbus.latest("sensor"),
		}
		res = self.collaborative_solve(
			{"title": "perception-act", "obs": obs, "goal": goal or {}},
			domains_needed=("planning", "analysis"),
		)
		# quick STM effect + consolidation attempt
		try:
			mem = getattr(self, 'memory', None)
			if mem is not None:
				if hasattr(mem, 'write_stm'):
					mem.write_stm({"tick": {"obs": obs, "result": res}})
				elif hasattr(mem, 'stm_write'):
					mem.stm_write({"tick": {"obs": obs, "result": res}})
		except Exception:
			pass
		return res
# === [END PATCH :: AGI-Stage-1.0] ===


# Re-attach memory/hub hooks to the final CognitiveIntegrationEngine.collaborative_solve
_final_collab = getattr(CognitiveIntegrationEngine, 'collaborative_solve', None)
def _collab_with_memory_final(self, problem: dict, domains_needed=()):
	res = _final_collab(self, problem, domains_needed) if _final_collab else {"winner": None, "top": []}
	# ensure memory exists
	try:
		mem = getattr(self, 'memory', None)
		if mem and res.get('winner'):
			try:
				# Build MemoryItem
				mi = MemoryItem(
					ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
					task={"title": problem.get("title"), "domains": list(domains_needed or [])},
					winner=res.get('winner') or {},
					confidence=float((res.get('winner') or {}).get('score', 0.0) or 0.0),
					features={"percept": res.get('percept', {}), "meta": res.get('winner', {}).get('meta', {})}
				)
				# write to STM
				try:
					if hasattr(mem, 'write_stm'):
						mem.write_stm(mi)
					elif hasattr(mem, 'remember'):
						mem.remember({"content": res['winner'].get('content'), "summary": f"win:{res['winner'].get('engine')}", "score": res['winner'].get('score',0.0)})
				except Exception:
					pass
			except Exception:
				pass
			try:
				moved = 0
				try:
					min_conf = float(os.getenv("AGL_LTM_PROMOTE_MIN", "0.78"))
				except Exception:
					min_conf = 0.78
				if hasattr(mem, 'consolidate_ltm'):
					moved = mem.consolidate_ltm()
				elif hasattr(mem, 'consolidate'):
					moved = mem.consolidate(min_conf=min_conf)
				res['memory_consolidated'] = moved
			except Exception:
				pass
	except Exception:
		pass

	# reinject perceptual hub if perceptions present but hub not in top
	try:
		names_top = [t.get('engine') for t in res.get('top', [])]
		if any(n in names_top for n in ("vision", "audio", "sensor")) and "perceptual_hub" not in names_top:
			# try to find adapter instance in self.adapters
			hub_adapter = None
			for a in getattr(self, 'adapters', []) or []:
				if getattr(a, 'name', None) == 'perceptual_hub':
					hub_adapter = a
					break
			if hub_adapter:
				try:
					hub_prop = hub_adapter.infer(problem, context=res.get('top', []))
					res['percept'] = hub_prop.get('content', {})
					hub_prop['novelty'] = max(hub_prop.get('novelty', 0.6), 0.62)
					scored = self._consensus_score(res.get('top', []) + [hub_prop])
					res['top'] = scored[:5]
					res['winner'] = scored[0]
				except Exception:
					pass
		else:
			# if hub present in adapters, also populate percept
			for a in getattr(self, 'adapters', []) or []:
				if getattr(a, 'name', None) == 'perceptual_hub':
					try:
						hub_prop = a.infer(problem, context=res.get('top', []))
						res['percept'] = hub_prop.get('content', {})
					except Exception:
						pass
					break
	except Exception:
		pass

	# optional: write a tiny self-model file if requested by env
	try:
		if os.getenv("AGL_SELF_MODEL", "0") == "1":
			p = os.getenv("AGL_SELF_MODEL_PATH", "")
			if p:
				_sm = {
					"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
					"integration_id": getattr(self, 'integration_id', None),
					"adapters": [getattr(a, 'name', type(a).__name__) for a in getattr(self, 'adapters', [])],
					"last_winner": res.get('winner'),
					"recent_winner": res.get('winner'),
					"metrics": getattr(self, 'metrics', {}),
				}
				try:
					_ensure_dir(os.path.dirname(p) or p)
					with open(p, 'w', encoding='utf-8') as f:
						json.dump(_sm, f, ensure_ascii=False, indent=2)
				except Exception:
					pass
	except Exception:
		pass
	# Stage-7: record health metrics (winner + top proposals) if HealthMonitor attached
	try:
		h = getattr(self, 'health', None)
		if h:
			win = res.get('winner') or {}
			eng = win.get('engine')
			lat = _safe_float(win.get('meta', {}).get('latency_ms', 0.0), 0.0)
			success = bool(win)
			quality = _safe_float(win.get('score', 0.0), 0.0)
			try:
				h.record(engine_name=eng or 'unknown', latency_ms=lat, success=success, quality=quality)
			except Exception:
				pass
			# also record the top proposals (best-effort)
			for p in (res.get('top') or []):
				try:
					pe = p.get('engine')
					pl = _safe_float(p.get('meta', {}).get('latency_ms', 0.0), 0.0)
					pq = _safe_float(p.get('score', 0.0), 0.0)
					h.record(engine_name=pe or 'unknown', latency_ms=pl, success=True, quality=pq)
				except Exception:
					pass
			try:
				h.flush()
			except Exception:
				pass
	except Exception:
		pass
	return res

CognitiveIntegrationEngine.collaborative_solve = _collab_with_memory_final

# === [BEGIN :: Self-Evolution / Stage-3 lightweight controller] ===
from dataclasses import dataclass
import shutil, tempfile, subprocess


@dataclass
class EvoResult:
	ok: bool
	notes: str
	fitness: float = 0.0
	files_changed: int = 0
	patch_path: str | None = None
	sandbox_dir: str | None = None
	test_output: str | None = None
	duration_s: float = 0.0


_DANGEROUS_PATTERNS = [
	r'\bos\.remove\(', r'\bos\.rmdir\(', r'\bshutil\.rmtree\(',
	r"\bsubprocess\.run\([^)]*shell\s*\=\s*True", r'open\([^)]*w[bt]?\)'
]

class SafetyGate:
	"""Strict gate: checks unified-diff targets, size, block/allow lists, and bad patterns."""
	def __init__(self, blocklist=None, allowlist=None, max_lines: int = None, timeout_s: int = None):
		self.blocklist = set(b.strip() for b in (blocklist or os.getenv('AGL_EVOLVE_BLOCKLIST','tests/,artifacts/,*.json').split(',')) if b and b.strip())
		self.allowlist = set(a.strip() for a in (allowlist or os.getenv('AGL_EVOLVE_ALLOWLIST','').split(',')) if a and a.strip())
		self.max_lines = int(max_lines if max_lines is not None else os.getenv('AGL_EVOLVE_MUT_MAX_LINES','120'))
		try:
			self.timeout_s = int(timeout_s if timeout_s is not None else os.getenv('AGL_EVOLVE_TIMEOUT_S','60'))
		except Exception:
			self.timeout_s = 60

	@staticmethod
	def _norm_path(p: str) -> str:
		return os.path.normpath(p).replace('\\', '/')

	def _extract_files_from_unified_diff(self, patch_text: str):
		files = []
		for line in patch_text.splitlines():
			if line.startswith('+++ ') or line.startswith('--- '):
				parts = line.split(None, 1)
				if len(parts) == 2:
					path = parts[1]
					if path.startswith('a/') or path.startswith('b/'):
						path = path[2:]
					files.append(self._norm_path(path))
		return list(dict.fromkeys(files))

	def _count_delta_lines(self, patch_text: str) -> int:
		added = sum(1 for ln in patch_text.splitlines() if ln.startswith('+') and not ln.startswith('+++'))
		removed = sum(1 for ln in patch_text.splitlines() if ln.startswith('-') and not ln.startswith('---'))
		return added + removed

	def _contains_danger(self, patch_text: str) -> bool:
		for rx in _DANGEROUS_PATTERNS:
			try:
				if re.search(rx, patch_text):
					return True
			except Exception:
				continue
		return False

	def approve(self, patch_text: str):
		# size
		delta = self._count_delta_lines(patch_text)
		if delta > self.max_lines:
			return False, f"PATCH_TOO_LARGE({delta}>{self.max_lines})"

		# files
		targets = self._extract_files_from_unified_diff(patch_text)
		if self.allowlist and any(self._norm_path(t) not in self.allowlist for t in targets):
			return False, "TARGET_NOT_IN_ALLOWLIST"
		if self.blocklist and any(self._norm_path(t) in self.blocklist for t in targets):
			return False, "TARGET_IN_BLOCKLIST"

		# dangerous content
		if self._contains_danger(patch_text):
			return False, "DANGEROUS_PATTERN"

		return True, "OK"


class FitnessBoard:
	def __init__(self):
		self.last = {}

	def score(self, tests_ok: bool, time_s: float, extra: dict) -> float:
		base = 0.0
		base += 0.7 if tests_ok else -1.0
		base += max(0.0, min(0.3, float(extra.get("quality_gain", 0.0))))
		base -= min(0.2, max(0.0, float(time_s) - 10.0) / 100.0)
		return round(float(base), 3)


class RewriteSandbox:
	def __init__(self, sandbox_dir: str):
		self.sbx = Path(sandbox_dir)
		# run-id will be appended when materializing
		self.run_dir = None

	def reset(self):
		if self.sbx.exists():
			try:
				shutil.rmtree(self.sbx)
			except Exception:
				pass
		self.sbx.mkdir(parents=True, exist_ok=True)

	def materialize(self, src_root="."):
		# Prefer git worktree if git available; otherwise fallback to copy
		run_id = str(int(time.time() * 1000))
		wt = self.sbx / run_id
		self.run_dir = wt
		try:
			# create worktree directory by invoking git worktree add
			subprocess.run(["git", "worktree", "add", str(wt), "HEAD"], check=True, cwd=str(Path(src_root)))
		except Exception:
			# fallback to filesystem copy
			wt.mkdir(parents=True, exist_ok=True)
			for item in os.listdir(src_root):
				if item in (".venv", ".git"): continue
				if item == self.sbx.name: continue
				s = Path(src_root) / item
				d = wt / item
				try:
					if s.is_dir():
						shutil.copytree(s, d)
					else:
						shutil.copy2(s, d)
				except Exception:
					pass

	def apply_patch(self, patch_text: str) -> int:
		"""
		Apply a patch in the worktree. Supports two modes:
		- Simple FILE: header: writes content directly to target file and stages it (git add)
		- Unified diff: writes patch to __candidate.patch and runs git apply --index
		Returns: number of affected lines (approx added + removed) or raises RuntimeError on apply failure.
		"""
		if not self.run_dir:
			raise RuntimeError("sandbox not materialized")
		candidate = self.run_dir / "__candidate.patch"
		txt = patch_text or ""
		# Detect FILE: header
		if txt.strip().startswith("FILE:"):
			# parse FILE:<path> then optional '---' separator
			lines = txt.splitlines()
			header = lines[0]
			_, _, rel = header.partition(":")
			target = rel.strip()
			body_idx = 1
			# find separator '---'
			for i in range(1, len(lines)):
				if lines[i].strip().startswith("---"):
					body_idx = i + 1
					break
			body = "\n".join(lines[body_idx:])
			target_path = self.run_dir / target
			_ensure_dir(target_path.parent)
			with open(target_path, "w", encoding="utf-8") as f:
				f.write(body)
			# stage file if git repository
			try:
				subprocess.run(["git", "-C", str(self.run_dir), "add", str(target)], check=True)
			except Exception:
				# ignore if git staging fails
				pass
			# approximate diff lines as number of non-empty lines in body
			added = sum(1 for l in body.splitlines() if l.strip())
			return added

		# Otherwise assume unified diff
		try:
			with open(candidate, "w", encoding="utf-8") as f:
				f.write(txt)
			# apply patch
			proc = subprocess.run(["git", "-C", str(self.run_dir), "apply", "--index", str(candidate)], capture_output=True, text=True)
			if proc.returncode != 0:
				# remove candidate and raise
				try:
					candidate.unlink()
				except Exception:
					pass
				raise RuntimeError(f"git-apply-failed: {proc.stderr.strip()}")
			# crude line count from patch file
			added = sum(1 for l in txt.splitlines() if l.startswith("+") and not l.startswith("+++"))
			removed = sum(1 for l in txt.splitlines() if l.startswith("-") and not l.startswith("---"))
			return added + removed
		except RuntimeError:
			raise
		except Exception as e:
			raise RuntimeError(f"apply-error:{repr(e)}")

	def run_tests(self, timeout_s: int) -> tuple[bool, float, str]:
		t0 = time.time()
		try:
			out = subprocess.run(
				[os.getenv("PYTHON", "python"), "-m", "pytest", "-q", "tests/test_result_guard.py"],
				cwd=str(self.run_dir), capture_output=True, timeout=timeout_s, text=True
			)
			ok = out.returncode == 0
			return ok, time.time() - t0, (out.stdout or "") + (out.stderr or "")
		except subprocess.TimeoutExpired:
			return False, time.time() - t0, "timeout"


class MutationLibrary:
	@staticmethod
	def micro_refactor_hint(*args, **kwargs) -> str:
		"""Return a tiny default patch when called without a test-provided stub.
		Tests often monkeypatch this method; this default ensures evolve_once() can
		generate a non-empty patch for safety checks.
		"""
		return "FILE:Self_Improvement/_evo_auto.txt\n---\nauto-evo-line-1\nauto-evo-line-2\n"


# ==== Stage-6: Safety hardening (drop-in) ====
MAX_PATCH_LINES = 120
BLOCKLIST_PATH_HINTS = (
	"Self_Improvement/Knowledge_Graph.py:registry_core",
	"AGL.Core_Engines.py",
	"Safety_Control/",
)

def _count_lines(text: str) -> int:
	return 0 if text is None else text.count("\n") + (1 if text and not text.endswith("\n") else 0)

def validate_patch_text_for_safety(patch_text: str):
	if not patch_text or not patch_text.strip():
		return False, "empty_patch"
	# honor env override for max lines budget
	try:
		max_allowed = int(os.getenv('AGL_EVOLVE_MUT_MAX_LINES', str(MAX_PATCH_LINES)))
	except Exception:
		max_allowed = MAX_PATCH_LINES
	if _count_lines(patch_text) > max_allowed:
		return False, "diff too large"
	for hint in BLOCKLIST_PATH_HINTS:
		if hint in patch_text:
			return False, f"path_blocked:{hint}"
	return True, "ok"
# =============================================

def _artifacts_present(paths):
	import os
	for p in paths:
		if not os.path.exists(p):
			return False
	return True

def _tests_passed_in_sandbox():
	# Look for a recent 'evolve_success' event in artifacts/evolution_log.jsonl
	try:
		p = Path("artifacts/evolution_log.jsonl")
		if not p.exists():
			return False
		last = None
		with p.open("r", encoding="utf-8") as f:
			for ln in f:
				ln = ln.strip()
				if not ln:
					continue
				try:
					j = json.loads(ln)
					last = j
				except Exception:
					continue
		if not last:
			return False
		# success if last event is evolve_success within recent window
		if last.get("event") == "evolve_success":
			return True
	except Exception:
		pass
	return False

def _last_patch_ok():
	# placeholder for last-patch validation
	return True

def premerge_ok():
	must = [
		_tests_passed_in_sandbox(),
		_last_patch_ok(),
		_artifacts_present(["artifacts/engine_stats.json", "artifacts/memory/stm.json", "artifacts/memory/ltm.json"]),
	]
	return all(must)



class EvolutionController:
	def __init__(self, gate: SafetyGate = None, sandbox_root=None, max_runtime_s: int = None, root: str = None):
		# Accept legacy 'root' kw for tests that pass EvolutionController(root=".")
		self.gate = gate or SafetyGate()
		# precedence: explicit sandbox_root -> root -> env var -> default
		self.sandbox_root = sandbox_root or root or os.getenv('AGL_EVOLVE_SANDBOX', '.aglsbx')
		self.max_runtime_s = int(os.getenv('AGL_EVOLVE_MAX_RUNTIME', '120')) if max_runtime_s is None else max_runtime_s
		_ensure_dir(self.sandbox_root)

	def _make_sandbox(self):
		# copy working tree minimally (fast copy of repo root)
		sbx = os.path.join(self.sandbox_root, str(int(time.time()*1000)))
		try:
			shutil.copytree('.', sbx, dirs_exist_ok=False, ignore=shutil.ignore_patterns('.venv', '.git', '__pycache__', '*.pyc'))
		except Exception:
			os.makedirs(sbx, exist_ok=True)
		return sbx # type: ignore

	def _write_patch(self, sbx: str, patch_text: str) -> str:
		p = os.path.join(sbx, '_last_patch.diff')
		with open(p, 'w', encoding='utf-8') as f:
			f.write(patch_text)
		return p

	def _apply_patch_gitstyle(self, sbx: str, patch_path: str) -> (bool, str): # type: ignore
		# try git apply if .git exists in parent, else fallback to reject (safer)
		if os.path.isdir(os.path.join(sbx, '.git')):
			try:
				cp = subprocess.run(['git', 'apply', patch_path], cwd=sbx, capture_output=True, text=True, timeout=30)
				if cp.returncode == 0:
					return True, "git-apply:OK"
				return False, f"git-apply:FAIL {cp.stderr[:500]}"
			except Exception as e:
				return False, f"git-apply:EXC {e}"
		# fallback: reject here (safer than naive text replace)
		return False, "NO_GIT_APPLY_FALLBACK"

	def _run_tests(self, sbx: str) -> (bool, str): # type: ignore
		try:
			cp = subprocess.run(
				[sys.executable, '-m', 'pytest', '-q', 'tests/test_result_guard.py'],
				cwd=sbx, capture_output=True, text=True, timeout=self.max_runtime_s
			)
			ok = (cp.returncode == 0)
			out = (cp.stdout or "") + "\n" + (cp.stderr or "")
			return ok, out[-4000:]
		except subprocess.TimeoutExpired:
			return False, "PYTEST_TIMEOUT"
		except Exception as e:
			return False, f"PYTEST_EXC {e}"

	def evolve_once(self, patch_text: str = None) -> EvoResult:
		"""Perform one evolution attempt. If patch_text is None, request MutationLibrary.micro_refactor_hint()."""
		t0 = time.time()
		# if no explicit patch_text provided, ask MutationLibrary to propose one
		try:
			if not patch_text:
				try:
					patch_text = MutationLibrary.micro_refactor_hint()
				except Exception:
					patch_text = ""
		except Exception:
			patch_text = patch_text or ""

		rv = self.gate.inspect_patch(patch_text) if hasattr(self.gate, 'inspect_patch') else (True, "ok")
		# normalize return to first two values (ok, why)
		try:
			if isinstance(rv, (list, tuple)):
				ok, why = rv[0], rv[1] if len(rv) > 1 else (rv[0] if len(rv) == 1 else True)
			else:
				ok, why = bool(rv), "ok"
		except Exception:
			ok, why = True, "ok"
		# approve via SafetyGate.approve if present
		try:
			if hasattr(self.gate, 'approve'):
				approved, reason = self.gate.approve(patch_text)
				if not approved:
					# map legacy reason into expected test-friendly messages
					if isinstance(reason, str) and "PATCH_TOO_LARGE" in reason:
						return EvoResult(False, "diff too large", duration_s=time.time()-t0)
					return EvoResult(False, f"REJECTED:{reason}", duration_s=time.time()-t0)
		except Exception:
			return EvoResult(False, "GATE_ERROR", duration_s=time.time()-t0)
		# validate patch text for quick rejections before sandboxing
		try:
			okv, reason_v = validate_patch_text_for_safety(patch_text)
			if not okv:
				_append_jsonl('artifacts/evolution_log.jsonl', {"ts": _ts(), "event": "evolve_reject", "reason": reason_v})
				return EvoResult(False, reason_v, fitness=0.0, files_changed=0, duration_s=time.time()-t0)
		except Exception:
			_append_jsonl('artifacts/evolution_log.jsonl', {"ts": _ts(), "event": "validate_error"})
			return EvoResult(False, "validate_error", fitness=0.0, files_changed=0, duration_s=time.time()-t0)

		# premerge enforcement (opt-in via env)
		try:
			if os.getenv("AGL_PREMERGE_ENFORCE", "0") == "1" and not premerge_ok():
				_append_jsonl('artifacts/evolution_log.jsonl', {"ts": _ts(), "event": "evolve_blocked", "reason": "premerge_failed"})
				return EvoResult(False, "premerge_failed", fitness=0.0, files_changed=0, duration_s=time.time()-t0)
		except Exception:
			# if premerge check fails unexpectedly, block evolution
			_append_jsonl('artifacts/evolution_log.jsonl', {"ts": _ts(), "event": "premerge_error"})
			return EvoResult(False, "premerge_error", fitness=0.0, files_changed=0, duration_s=time.time()-t0)

		sbx = self._make_sandbox()
		patch_path = self._write_patch(sbx, patch_text)
		ok_apply, msg_apply = self._apply_patch_gitstyle(sbx, patch_path)
		if not ok_apply:
			return EvoResult(False, f"APPLY_FAIL:{msg_apply}", patch_path=patch_path, sandbox_dir=sbx, duration_s=time.time()-t0)

		ok_test, out = self._run_tests(sbx)
		if not ok_test:
			return EvoResult(False, f"TEST_FAIL", patch_path=patch_path, sandbox_dir=sbx, test_output=out, duration_s=time.time()-t0)

		# Log success
		_append_jsonl('artifacts/evolution_log.jsonl', {
			'ts': datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
			'event': 'evolve_success',
			'sandbox': sbx,
			'patch': os.path.basename(patch_path),
			'duration_s': round(time.time()-t0, 3)
		})
		return EvoResult(True, "OK", patch_path=patch_path, sandbox_dir=sbx, test_output=out, duration_s=time.time()-t0)

	def run(self, max_steps: int = 1, accept_min: float = 0.0):
		"""Run up to max_steps evolution iterations and return list of EvoResult.
		Stops early if any result.fitness >= accept_min (if fitness numeric).
		"""
		results = []
		for i in range(max_steps):
			try:
				res = self.evolve_once()
			except Exception as e:
				res = EvoResult(False, f"exception:{e}")
			results.append(res)
			# if accepted by fitness threshold
			try:
				if isinstance(res.fitness, (int, float)) and res.fitness >= float(accept_min):
					break
			except Exception:
				pass
		return results


# expose a compatibility symbol used in suggested tests
Self_Evolution = EvolutionController
# === [END :: Self-Evolution] ===



