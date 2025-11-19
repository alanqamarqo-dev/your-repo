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
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional


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
	spec شكل مقبول:
	  - "pkg.mod:ClassName"
	  - "pkg.mod#ClassName"
	يرجع (cls, err) حيث cls صنف قابل للإنشاء، وإلا None مع نص الخطأ.
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
	يدعم شكلين:
	  1) JSON dict: {"planner":"pkg.mod:Class", "math":"x.y:Z"}
	  2) comma pairs: "planner=pkg.mod:Class, math=x.y:Z"
	يعيد dict name -> spec
	"""
	if not env_val:
		return {}
	env_val = env_val.strip()
	# JSON؟
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
			inst = cls()  # نتوقّع صنف Adapter متوافق
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
	"""ذاكرة جماعية بسيطة: JSONL + استعلام فلترة نصيّة خفيفة."""
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
		"""دمج بسيط: دمج مفاهيم وتلخيص نصي سريع."""
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
	ربط «محركات» متعدّدة عبر سجل بسيط + حافلة معرفة + سجل تعاون.
	إذا وُجد IntegrationRegistry في المنظومة، سنحاول استدعاءه؛ وإلا نعمل بوضع fallback.
	"""
	def __init__(self):
		self.engines_registry = {}      # name -> {capabilities, status, collaboration_score}
		self.knowledge_bus = []         # رسائل قصيرة بين المحركات
		self.collaboration_log = Path("artifacts/collaboration_log.jsonl")
		self.collective = CollectiveMemorySystem()

	# --- اكتشاف المحركات ---
	def detect_available_engines(self):
		# Fallback: من متغير بيئة أو قائمة افتراضية صغيرة
		env_list = os.getenv("AGL_ENGINES", "")
		if env_list.strip():
			return [x.strip() for x in env_list.split(",") if x.strip()]
		# قائمة رمزية؛ استبدلها لاحقًا بقراءة حقيقية من IntegrationRegistry إن متاح
		return ["planner", "deliberation", "emotion", "associative", "retriever", "self_learning"]

	def get_engine_capabilities(self, name):
		# تعريف بسيط؛ يمكن ربطه بقائمة قدرات حقيقية لاحقًا
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

	# --- اختيار محركات حسب مجال ---
	def find_engines_for_domain(self, domain):
		got = []
		for n, meta in self.engines_registry.items():
			caps = meta.get("capabilities", [])
			if domain in caps or domain in n or domain in " ".join(caps):
				got.append(n)
		# fallback: إن لم نجد، أعِد عدة محركات افتراضيًا
		return got or list(self.engines_registry.keys())[:2]

	# --- استدعاء محرك ---
	def query_engine(self, engine_name, problem, context=None):
		"""
		إن كان موجود IntegrationRegistry فحاول استدعاء محرك بالاسم؛
		وإلا نُنتج استجابة رمزية تتضمن بصمة + سياق.
		"""
		try:
			from Integration_Layer import Domain_Router as DR  # إن وجد
			if hasattr(DR, "IntegrationRegistry"):
				reg = getattr(DR, "IntegrationRegistry")
				if hasattr(reg, "get") and reg.get(engine_name):
					fn = reg.get(engine_name)
					return {
						"engine": engine_name,
						"ts": _utc(),
						"result": fn(problem, context=context)  # قد تتطلب توقيعًا مختلفًا
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

	# --- دمج حلول ---
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

	# --- واجهة الحل التعاوني ---
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
		return {"integration_id": integration_id, "solutions": sols}
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
	شبكة معرفة تربط المحركات وتستنتج المسارات المثلى بين القدرات (domains).
	- nodes: أسماء المحركات + قدراتها
	- edges: أوزان (حِمل/جودة/زمن) تُحدَّث وفق الأداء
	"""
	def __init__(self):
		self.nodes = {}   # name -> {capabilities: [...], score: float}
		self.edges = {}   # (a,b) -> weight (أقل أفضل)
		self.metrics = {"updates": 0}

	def add_engine(self, name, capabilities, perf_score=0.5):
		self.nodes[name] = {"capabilities": list(capabilities), "score": float(perf_score)}

	def connect(self, a, b, weight=1.0):
		self.edges[(a,b)] = float(max(weight, 1e-6))

	def suggest_path(self, domains_needed):
		"""
		مسار بسيط greedy: يختار لكل domain أفضل محرك (score/capability) مع تقليل الوزن.
		يمكن لاحقاً استبداله بـ Dijkstra/ILP. الآن سريع وخفيف.
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
	تصويت/إجماع على حلول متعددة:
	- يقيّم كل حل (جودة/تغطية شروط/تعليل)
	- يرتّب الحلول ويعيد المختار + ملخص مبررات
	- يكتب مقاييس جماعية إلى artifacts/collaborative_intelligence_metrics.json
	"""
	def __init__(self):
		self.history = []

	def score_proposal(self, proposal):
		# توقع شكل: {"text":..., "checks": {"constraints": bool, "feasible": bool}, "rationale": "...", "novelty":0..1}
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

# توسيع/ترقية CognitiveIntegrationEngine الحالي (دون كسر الواجهة)
try:
	class CognitiveIntegrationEngine(CognitiveIntegrationEngine):  # type: ignore
		def __init__(self):
			super().__init__()
			self.kn = KnowledgeNetwork()
			self.voter = ConsensusVotingEngine()

		def connect_engines(self):
			# استدعاء الأصلي
			super().connect_engines()
			# تغذية الشبكة بالمحركات المتاحة
			for name, meta in getattr(self, "engines_registry", {}).items():
				caps = meta.get("capabilities", [])
				score = float(meta.get("collaboration_score", 0.6))
				self.kn.add_engine(name, caps, perf_score=score)
			# وصل افتراضي خفيف (يمكن لاحقاً التعلم من السجل)
			names = list(self.engines_registry.keys())
			for i in range(len(names)-1):
				self.kn.connect(names[i], names[i+1], weight=1.0)

		def collaborative_solve(self, problem, domains_needed):
			# المسار الأصلي: توليد حلول من محركات متعددة
			solutions_raw = []
			for d in domains_needed:
				engines = self.find_engines_for_domain(d)
				for eng in engines:
					sol = self.query_engine(eng, problem, context=solutions_raw)
					# تحويل حل أولي إلى اقتراح مُقيَّم
					proposal = {
						"text": str(sol),
						"checks": {"constraints": True, "feasible": True},
						"rationale": f"{eng} rationale for {d}",
						"novelty": 0.6,
					}
					solutions_raw.append(proposal)

			# 1) مسار أمثل عبر الشبكة
			optimal = self.kn.export_optimal_paths(domains_needed)

			# 2) إجماع/تصويت
			ranked = self.voter.rank_and_select(solutions_raw)
			integration_id = uuid.uuid4().hex[:12]

			# 3) حفظ السجلات (متسق مع مرحلتك 2)
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

			# 4) تصدير المقاييس الجماعية
			metrics = self.voter.export_metrics(integration_id, ranked)

			# 5) نعيد موجزًا صغيرًا (متوافق مع ما طبعتَه سابقاً)
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

# سجل/مقاييس بسيطة مضافة لمرحلة 3
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


# ذاكرة مفعّلة افتراضيًا؛ عطّلها في CI بـ AGL_MEMORY_ENABLE=0
AGL_MEMORY_ENABLE = _env("AGL_MEMORY_ENABLE", "1")  # '1' أو '0'


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

# 1) واجهة محول موحّدة للمحرّكات
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

# 2) أمثلة محوّلات جاهزة للمحرّكات الشائعة
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

class AssociativeAdapter(EngineAdapter):
	name = "associative"; domains = ("creativity","synthesis","cross-domain")
	def infer(self, problem, context=None, timeout_s=3.0):
		t0=_now_ms()
		blends = ["analogy: biology→algorithms", "analogy: art→design"]
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
			"content": {"sketch":"assumptions→lemmas→result","hints":["use Banach/cvx/ODE if applicable"]},
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
			"content": {"proof_style":"sketch→rigor→edge-cases"},
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
			"content": {"ops":["meter→وزن","idioms→ثقافة","register→مقصد"]},
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

# 0) أدوات مساعدة بسيطة لتخزين/قراءة الذاكرة
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

# 1) حلقة الذاكرة (STM/LTM)
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

# 2) Perceptual Hub: يدمج vision/audio/sensor
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

# سجّل المحولين الجدد (سيتم دمجها مع القاموسbuiltins لاحقًا)
_EXTRA_ADAPTERS = {
	'perceptual_hub': PerceptualIntegrationAdapter,
	'goal_engine': GoalAdapter,
}

# 4) أسلاك CIE: أربط الذاكرة وHub داخل التكامل
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
	# اجعل الـ PerceptualHub يعرف الـ CIE (للوصول لاحقًا عند الحاجة)
	try:
		self.perceptual_hub = PerceptualHubAdapter(cie=self)
	except Exception:
		self.perceptual_hub = PerceptualHubAdapter()

CognitiveIntegrationEngine.__init__ = _cie_init_with_memory

# أدخل نقاط تذكّر وتثبيت خفيفة داخل collaborative_solve
_old_collab = CognitiveIntegrationEngine.collaborative_solve
def _collab_with_memory(self, problem: dict, domains_needed=()):
	res = _old_collab(self, problem, domains_needed)
	# 1) تذكّر الملخصات الفائزة (STM)
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

	# 2) ترقية إلى LTM لو لزم
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

	# 3) حقن Hub لاحقًا: إذا رصدنا مخرجات vision/audio/sensor ضمن top ولم يوجد hub في top—أعد إدخال hub لتعزيز الدمج
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


# سجلّه في البِلت-إن
# registration moved below after _BUILTIN_ADAPTERS is defined
# === [END PATCH D1] ===
# === [END :: Extra adapters] ===

# 3) سجل محولات—وأداة اكتشاف من AGL_ENGINES
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

def _register_extra_adapters():
	global _BUILTIN_ADAPTERS, _EXTRA_ADAPTERS
	try:
		if "_BUILTIN_ADAPTERS" in globals() and _EXTRA_ADAPTERS:
			_BUILTIN_ADAPTERS.update(_EXTRA_ADAPTERS)
	except Exception:
		pass

# دمج أي محولات إضافية مُجمعة سابقًا
_register_extra_adapters()

# register generative creativity adapter if present
try:
    _BUILTIN_ADAPTERS["gen_creativity"] = GenerativeCreativityAdapter
except Exception:
    pass

def discover_engines_from_env():
	raw = os.getenv("AGL_ENGINES","" ).strip()
	names = [n.strip() for n in raw.split(",") if n.strip()]

	# NEW: تحميل المحركات الحقيقية من البيئة
	overrides = _load_overrides_from_env()  # name -> instance

	# === [BEGIN PATCH :: Unknown-Engine Auto-Shim] ===
	# Shim عام لأسماء المحركات غير المعرّفة مسبقًا
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

	# مساعد بسيط لاستنتاج نطاقات من الاسم
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

	# عدّل الاكتشاف ليقبل الشِمز التلقائي عند تفعيل العلم AGL_ALLOW_UNKNOWN_SHIMS=1
	allow_unknown = os.getenv("AGL_ALLOW_UNKNOWN_SHIMS","0") == "1"

	adapters = []
	for n in names:
		# 1) Override ديناميكي (الأولوية)
		inst = overrides.get(n)
		if inst is not None:
			adapters.append(inst)
			continue
		# 2) Built-in إن وُجد
		cls = _BUILTIN_ADAPTERS.get(n)
		if cls is not None:
			try:
				adapters.append(cls())
				continue
			except Exception:
				pass
		# 3) Shim تلقائي للأسماء غير المعروفة (اختياري)
		if allow_unknown:
			try:
				adapters.append(_DefaultShimAdapter(n, _infer_domains_from_name(n)))
			except Exception:
				pass

	return adapters
	# === [END PATCH] ===

# === [PATCH :: Knowledge_Graph.py :: unify diversity + helper API] ===
# اجعل هذه helpers أعلى الملف إن لم تكن موجودة
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

# 4) توسيع CognitiveIntegrationEngine لدعم الكثير من المحرّكات بالتوازي
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
		env_adapters = discover_engines_from_env()

		# ترتيب ثابت اختياري
		ordered = os.getenv("AGL_ENGINE_ORDER", "").strip()
		if ordered:
			order = [x.strip() for x in ordered.split(",") if x.strip()]
			try:
				env_adapters.sort(key=lambda a: (order.index(a.name) if a.name in order else 10**6))
			except Exception:
				# إذا لم يعمل الترتيب بصورة صحيحة، تجاهل
				pass

		# سقف أقصى
		try:
			cap = int(os.getenv("AGL_ENGINE_MAX", "0"))
		except Exception:
			cap = 0
		if cap and cap > 0:
			env_adapters = env_adapters[:cap]

		self.adapters = env_adapters or self.adapters
		# سجّل نوع التنفيذ (override/builtin) عندما يكون ذلك ممكنًا
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
		# سجل موجز عن المحركات والأنواع (مفيد للتحقق من overrides)
		try:
			_append_jsonl("artifacts/engine_impls_log.jsonl", {
				"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
				"event": "connect_engines_summary",
				"engines": [getattr(a, "name", type(a).__name__) for a in self.adapters],
				"impl_types": [type(a).__name__ for a in self.adapters]
			})
		except Exception:
			pass
		return list(self.engines_registry.keys())

	def _attach_domains(self, proposal, adapter):
		if proposal is None:
			return {"engine": adapter.name, "content": {}, "checks": {}, "novelty": 0.5, "meta": {}}
		# ارفق domains إن كانت غير موجودة
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
				self.metrics["invocations"] += 1
				t0=_now_ms()
				r = adapter.infer(problem, context=results, timeout_s=timeout_s)
				r = self._attach_domains(r or {}, adapter)
				self.metrics["success"] += 1
				self.metrics["latency_ms"].append(_now_ms()-t0)
				q.put(r)
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
		يُرجع قائمة مرتبة بالمحركات المحمّلة مع نوع التنفيذ:
		[{"name": "...", "impl": "override|builtin", "domains": (...)}, ...]
		"""
		return [{"name": n,
			 "impl": (self.engines_registry.get(n, {}).get("impl") or "builtin"),
			 "domains": self.engines_registry.get(n, {}).get("domains", ())}
			for n in self.engines_registry.keys()]

	def _consensus_score(self, proposals):
		# معاملات قابلة للضبط من البيئة
		tie_eps = _env_float("AGL_TIE_EPS", 0.01)
		diversity_bonus = _env_float("AGL_TIE_DIVERSITY_BONUS", 0.02)

		# 1) السكور الأساسي
		ranked = []
		for p in proposals:
			novelty = _safe_float(p.get("novelty", 0.5), 0.5)
			checks = p.get("checks", {})
			fit = 1.0 if checks.get("constraints", True) else 0.0
			feas = 1.0 if checks.get("feasible", True) else 0.0
			base = 0.5 * novelty + 0.3 * fit + 0.2 * feas
			ranked.append({**p, "score": base})

		ranked.sort(key=lambda r: r.get("score", 0.0), reverse=True)
		if not ranked:
			return ranked

		# 2) تجميع التعادلات القريبة وإعادة ترتيبها بتفضيل التنوّع
		out = []
		seen_engines = set()
		i = 0
		while i < len(ranked):
			j = i
			ref = ranked[i]["score"]
			bucket = []
			while j < len(ranked) and abs(ranked[j]["score"] - ref) <= tie_eps:
				bucket.append(ranked[j]); j += 1

			# داخل الـ bucket: فضّل محركات أقل تكرارًا (لتجنب التكرار)، ثم غير المشاهد ثم الأعلى حداثة
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

	def collaborative_solve(self, problem: dict, domains_needed=()):
		proposals = self._fanout_query(problem, timeout_s=_safe_float(os.getenv("AGL_ENGINE_TIMEOUT","3.5"), 3.5))
		ranked = self._consensus_score(proposals)
		top = ranked[:5]
		winner = ranked[0] if ranked else None
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
        يُعيد dict فيه: confidence, diversity, need_alternative (bool)، ومؤشرات مساعدة.
        """
        if not ranked_top:
            return {"confidence": 0.0, "diversity": 0, "need_alternative": True, "reason": "no_proposals"}
        # ثقة مبسطة = score الأعلى – متوسط الفرق ضمن حزمة التساوي تقريبًا
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
        # استخراج تضاريس زمنية مختصرة (وهمية آمنة افتراضيًا)
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
        # مكافآت داخلية مبسطة: دقة/تنوع/سرعة/التزام
        reward = {"accuracy_hint": 0.6, "diversity_hint": 0.7, "speed_hint": 0.5, "constraint_hint": 0.8}
        return {
            "engine": self.name,
            "content": {"reward_signals": reward, "policy":"encourage_diverse_accurate_fast"},
            "checks": {"constraints": True, "feasible": True},
            "novelty": 0.55,
            "meta": {"latency_ms": _now_ms()-t0, "tokens": 0},
            "domains": self.domains,
        }

# تسجيل المحرّكات الجديدة
_BUILTIN_ADAPTERS.update({
    "timeline": TimelineAdapter,
    "contextualizer": ContextualizerAdapter,
    "motivation": MotivationAdapter,
})

# -------- ربط المتحكّم الفوقي مع CIE --------
try:
    _CIE_BASE = CognitiveIntegrationEngine
except NameError:
    class _CIE_BASE: 
        def __init__(self): pass

class CognitiveIntegrationEngine(_CIE_BASE):  # نعيد تعريفها بتوسيعات جديدة دون كسر ما سبق
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
	# البقية (self.adapters, self.metrics, إلخ) موجودة مسبقًا في نسختك

	def _inject_generative_strategy_if_needed(self, problem, ranked):
		if not self.generative_link:
			return ranked
		need_alt = self.meta.evaluate_cycle(ranked).get("need_alternative", False)
		if not need_alt:
			return ranked
		# إدراج استراتيجية تفكير بديلة (shim آمن) داخل السباق
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

		# تحديث priors عبر المتحكّم الفوقي
		if os.getenv("AGL_META_REFLECTION","1") == "1":
			try:
				latency = _safe_float((winner or {}).get("meta",{}).get("latency_ms",0.0), 0.0)
				self.meta.update_priors(self.engine_stats_path, winner, latency_ms=latency)
			except Exception:
				pass

		# السجلات والذاكرة كما كانت لديك مسبقًا (collaboration_log.jsonl, collective_memory.jsonl)
		# ... (نحتفظ بكتاباتك السابقة كما هي)

		return {"integration_id": self.integration_id,
				"solutions": (len(proposals) if isinstance(proposals, list) else int(proposals or 0)),
				"winner": winner,
				"top": top}
# Stage-5: perception tick (embodied perception step)

	def tick(self, goal=None):
		"""Minimal perception→act→learn step."""
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
	return res

CognitiveIntegrationEngine.collaborative_solve = _collab_with_memory_final

# === [BEGIN :: Self-Evolution / Stage-3 lightweight controller] ===
from dataclasses import dataclass
import shutil, tempfile, subprocess


@dataclass
class EvoResult:
	ok: bool
	fitness: float
	files_changed: int
	notes: str
	patch_path: str | None = None


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
	if _count_lines(patch_text) > MAX_PATCH_LINES:
		return False, "too_large"
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

		# premerge enforcement (opt-in via env)
		try:
			if os.getenv("AGL_PREMERGE_ENFORCE", "0") == "1" and not premerge_ok():
				_append_jsonl('artifacts/evolution_log.jsonl', {"ts": _ts(), "event": "evolve_blocked", "reason": "premerge_failed"})
				return EvoResult(False, 0.0, 0, "premerge_failed")
		except Exception:
			# if premerge check fails unexpectedly, block evolution
			_append_jsonl('artifacts/evolution_log.jsonl', {"ts": _ts(), "event": "premerge_error"})
			return EvoResult(False, 0.0, 0, "premerge_error")

		# validate patch text for quick rejections before sandboxing
		try:
			okv, reason_v = validate_patch_text_for_safety(patch_text)
			if not okv:
				_append_jsonl('artifacts/evolution_log.jsonl', {"ts": _ts(), "event": "evolve_reject", "reason": reason_v})
				return EvoResult(False, 0.0, 0, reason_v)
		except Exception:
			_append_jsonl('artifacts/evolution_log.jsonl', {"ts": _ts(), "event": "validate_error"})
			return EvoResult(False, 0.0, 0, "validate_error")

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
				res = EvoResult(False, 0.0, 0, f"exception:{e}")
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


