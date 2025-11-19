# Integration_Layer/Task_Orchestrator.py
import unicodedata, re, hashlib, json, os
from difflib import SequenceMatcher
from Knowledge_Base.seed_formulas import load_seed_formulas
from Core_Engines.Law_Parser import LawParser
from Core_Engines.Law_Matcher import LawMatcher
from Learning_System.Law_Learner import LawLearner
from Learning_System.Self_Learning import SelfLearning
from Learning_System.Inference_Engine import InferenceEngine
from Core_Engines.Units_Validator import check_dimensional_consistency
import csv
import math
from typing import Optional
from Safety_Systems.EmergencyIntegration import EmergencyIntegration
from Core_Engines.Perception_Context import PerceptionContext
from Core_Engines.Reasoning_Planner import ReasoningPlanner


def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFC", str(s))
    s = re.sub(r"[\u0640]", "", s)          # إزالة التطويل
    s = re.sub(r"\s+", " ", s).strip()
    return s


def stable_inputs_hash(task: str, seed: int) -> str:
    payload = {"task": normalize_text(task), "seed": int(seed)}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


class TaskOrchestrator:
    def __init__(self, *args, **kwargs):
        # initialize law-related components once
        try:
            self.law_store = load_seed_formulas()
            self.law_parser = LawParser()
            self.law_matcher = LawMatcher(self.law_store, self.law_parser)
            self.law_learner = LawLearner(self.law_parser)
        except Exception:
            # keep orchestrator usable even if law components fail to initialize
            self.law_store = None
            self.law_parser = None
            self.law_matcher = None
            self.law_learner = None
        # emergency integration (safe-run bridge)
        try:
            self.emergency_system = EmergencyIntegration(self)
            self.emergency_system.initialize_emergency_system()
        except Exception:
            self.emergency_system = None
        # inference engine (Phase H)
        try:
            self.inference = InferenceEngine()
        except Exception:
            self.inference = None
        # Perception & Context extractor (PCX)
        try:
            self.pcx = PerceptionContext()
        except Exception:
            self.pcx = None
        # Reasoning & Planning (RPL)
        try:
            self.rpl = ReasoningPlanner()
        except Exception:
            self.rpl = None

    def handle_task_with_emergency_protection(self, task: str, context: dict) -> dict:
        if self._requires_emergency_isolation(task, context):
            try:
                # delegate to emergency bridge
                if self.emergency_system:
                    self.logger = getattr(self, 'logger', None) or None
                    if self.logger:
                        self.logger.info("🛡️ تفعيل الحماية الطارئة للمهمة")
                    container_id = context.get('container_id', 'tmp_emergency') if isinstance(context, dict) else 'tmp_emergency'
                    code = context.get('code', '') if isinstance(context, dict) else ''
                    return self.emergency_system.handle_emergency_task(container_id, code, context.get('task_data') if isinstance(context, dict) else {}) # type: ignore
            except Exception as e:
                return {'task': task, 'error': str(e)}
        return self.process(task, **(context or {})) # type: ignore

    def _requires_emergency_isolation(self, task: str, context: dict) -> bool:
        flags = set((context or {}).get('flags', [])) if isinstance(context, dict) else set()
        risky = any([
            'copilot' in (task or '').lower(),
            'experimental' in (task or '').lower(),
            'unsafe' in flags,
            (context or {}).get('requires_isolation', False),
            (context or {}).get('risk_level', 'low') in ('high','critical'),
        ])
        return risky

    def decompose_complex_tasks(self, complex_task):
        """تفكيك المهام المعقدة"""
        return {
            'main_task': complex_task,
            'subtasks': ['تحليل', 'حل', 'تحقق'],
            'allocated_engines': ['mathematical_brain']
        }

    # Backwards-compatible wrapper expected by some tests
    def process_task(self, complex_task, context=None):
        if complex_task is None or (isinstance(complex_task, str) and not complex_task.strip()):
            return {"error": "empty_task"}
        # rudimentary routing for math tasks
        if isinstance(complex_task, str) and ("تفاضلية" in complex_task or "differential" in complex_task):
            # delegate to mathematical brain
            try:
                mb = __import__("Core_Engines.Mathematical_Brain", fromlist=["MathematicalBrain"]).MathematicalBrain()
                return {"solution": mb.process_task(complex_task), "confidence": 0.9}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "unknown_task"}

    # keep compatibility wrapper methods
    def normalize_text(self, s: str) -> str:
        return normalize_text(s)

    def stable_inputs_hash(self, task: str, seed: int) -> str:
        return stable_inputs_hash(task, seed)

    def process(self, task: str, **kwargs):
        t = task.strip()
        # allow PCX to annotate incoming kwargs/context for routing decisions
        try:
            if self.pcx:
                pcx_res = self.pcx.extract(kwargs or {})
                # merge lightweight context hints
                kwargs['_pcx'] = pcx_res
        except Exception:
            pass
        # emergency execution: run user-provided code in isolated container
        if t == 'emergency:exec':
            try:
                code = kwargs.get('code', '')
                container_id = kwargs.get('container_id', 'tmp_emergency')
                # register a temporary container workspace under reports/tmp_emergency
                try:
                    from Safety_Systems.EmergencyIntegration import register_temp_container, run_emergency_code
                    tmp_dir = os.path.join('reports', container_id)
                    register_temp_container(container_id, tmp_dir)
                    res = run_emergency_code(container_id, code, kwargs.get('task_data', {}))
                    return {'task': t, 'result': res}
                except Exception as e:
                    return {'task': t, 'error': str(e)}
            except Exception as e:
                return {'task': t, 'error': str(e)}
        # law validation
        if t == "law_validate":
            formula = kwargs.get("formula", "")
            if not self.law_matcher:
                return {"task": t, "status": "error", "reason": "law subsystem not available"}
            m = self.law_matcher.match(formula)
            # units check: optional var_units passed in kwargs
            var_units = kwargs.get("var_units") or {}
            units_ok = None
            units_report = None
            try:
                uv = check_dimensional_consistency(formula, var_units) # type: ignore
                units_ok = bool(uv.get("ok"))
                units_report = uv
            except Exception:
                units_ok = None

            # composite confidence: symbolic match (1/0) and units (1/0)
            sym_score = 1.0 if m.get("match") else 0.0
            units_score = 1.0 if units_ok else 0.0 if units_ok is not None else 0.5
            composite = 0.6 * sym_score + 0.4 * units_score

            return {"task": t, "status": "validated" if m["match"] else "unknown",
                    "match": (m["match"].id if m["match"] else None),
                    "normalized": str(self.law_parser.normalize(formula)), # type: ignore
                    "units": units_report,
                    "composite_confidence": composite}

        # law development / propose tweak
        if t == "law_development":
            # delegate to run_law_development for programmatic and CLI use
            formula = kwargs.get("formula", "")
            samples = kwargs.get("samples")
            data_path = kwargs.get("data") or kwargs.get("data_path")
            model = kwargs.get("model")
            return self.run_law_development(formula, samples=samples, data_path=data_path, model_hint=model)

        # lightweight training entrypoint for demo datasets
        if "train-laws" in t:
            try:
                from Learning_System.Self_Learning_Module import SelfLearningModule
                import csv, json
                csv_path = kwargs.get("data", "data/hooke_sample.csv")
                if not os.path.exists(csv_path):
                    return {"ok": False, "error": f"dataset not found: {csv_path}"}

                X = []
                y = []
                with open(csv_path, 'r', encoding='utf-8') as f:
                    r = csv.DictReader(f)
                    for row in r:
                        X.append({"x": float(row["x"])})
                        y.append(float(row["F"]))

                sl = SelfLearningModule()
                hooke = [h for h in sl.generate_hypotheses("hooke") if h.name == "hooke"][0]
                fitted = sl.fit_params(hooke, X, y)
                mse = sl.evaluate_mse(fitted, X, y)

                out_path = os.path.join("Knowledge_Base", "Learned_Patterns.json")
                rec = {"law": "hooke", "params": fitted.params, "mse": mse}
                with open(out_path, 'w', encoding='utf-8') as f:
                    json.dump(rec, f, ensure_ascii=False, indent=2)

                return {"ok": True, "law": "hooke", "params": fitted.params, "mse": mse, "artifact": out_path}
            except Exception as e:
                return {"ok": False, "error": str(e)}

    def run_law_development(self, formula: str, samples=None, data_path: Optional[str] = None, model_hint: Optional[str] = None):
        """Programmatic API: fit law from samples or CSV and save facts.

        Returns a report dict with fit results and gate evaluation.
        """
        t = "law_development"
        if not self.law_learner:
            return {"task": t, "status": "error", "reason": "law subsystem not available"}

        # ensure sample_list populated
        sample_list = None
        if data_path and os.path.exists(data_path):
            try:
                with open(data_path, 'r', encoding='utf-8-sig') as f:
                    dr = csv.DictReader(f)
                    sample_list = [ {k: float(v) for k,v in row.items()} for row in dr ]
            except Exception:
                sample_list = None
        elif isinstance(samples, list):
            sample_list = samples

        m = self.law_matcher.match(formula) if self.law_matcher else {"match": None}
        norm = self.law_parser.normalize(formula) if self.law_parser else formula

        match_obj = m.get("match")
        if not match_obj:
            return {"task": t, "status": "new_candidate", "normalized": str(norm)}

        base_eq = str(getattr(match_obj, 'equation_str', '') or '')
        prop = self.law_learner.propose_scale_bias(base_eq)
        fit_result = None
        if sample_list:
            try:
                fit_result = self.law_learner.fit_params(base_eq, sample_list)
            except Exception:
                fit_result = None

        # evaluate law-specific gate
        try:
            from ConfidenceGate import law_confidence_gate
            gate_res = law_confidence_gate({"result": fit_result} if fit_result else {})
        except Exception:
            gate_res = {"passed": False, "reason": "gate_error"}

        match_id = getattr(match_obj, 'id', None)
        report = {
            "task": t,
            "status": "matched",
            "base": match_id,
            "proposal": str(prop.get("proposal_expr") if isinstance(prop, dict) else prop),
            "params": prop.get("params") if isinstance(prop, dict) else None,
            "fit": fit_result,
            "gate": gate_res,
            "normalized": str(norm)
        }

        # save to knowledge base only if gate passed
        try:
            from Knowledge_Base.Law_Facts import save_law_fact
            import time
            match_id = getattr(match_obj, 'id', None)
            if isinstance(gate_res, dict) and gate_res.get('passed'):
                key = f"fact_{match_id}_{int(time.time())}"
                payload = {"law_id": match_id, "fit": fit_result, "gate": gate_res, "ts": int(time.time()), "confidence": float(gate_res.get('confidence', 0.0))}
                save_law_fact(key, payload)
        except Exception:
            pass

        return report

    def run_self_learning(self, base_formula: str, samples=None, data_path: Optional[str] = None, max_candidates: int = 4, persist_if_pass: bool = False):
        """Run self-learning: generate candidates from base_formula, evaluate on samples or CSV.

        If persist_if_pass is True, persist candidate to Knowledge_Base if gate passes.
        """
        sl = SelfLearning()
        sample_list = None
        if data_path and os.path.exists(data_path):
            try:
                with open(data_path, 'r', encoding='utf-8-sig') as f:
                    dr = csv.DictReader(f)
                    sample_list = [ {k: float(v) for k,v in row.items()} for row in dr ]
            except Exception:
                sample_list = None
        elif isinstance(samples, list):
            sample_list = samples

        results = sl.run(base_formula, sample_list or [], max_candidates=max_candidates)

        # optional persistence when gate passes
        persisted = []
        try:
            from ConfidenceGate import law_confidence_gate
        except Exception:
            law_confidence_gate = None

        for r in results:
            gate_ok = False
            gate_info = None
            if law_confidence_gate and persist_if_pass:
                try:
                    gate_info = law_confidence_gate({'result': r.get('fit')})
                    gate_ok = bool(gate_info.get('passed'))
                except Exception:
                    gate_ok = False

            if persist_if_pass and gate_ok:
                try:
                    from Knowledge_Base.Law_Facts import save_law_fact
                    import time
                    key = f"selflearn_{int(time.time())}_{hash(r.get('candidate'))}"
                    payload = {'candidate': r.get('candidate'), 'fit': r.get('fit'), 'ts': r.get('ts'), 'gate': gate_info}
                    save_law_fact(key, payload)
                    persisted.append(key)
                except Exception:
                    pass

        return {'results': results, 'persisted': persisted}

    # ----------------------------
    # Inference task helpers (Phase H)
    # ----------------------------
    def task_predict(self, payload: dict) -> dict:
        """
        payload:
          { "base": "ohm|hooke|poly2|rc_step|power|exp1", "x": 0.5 or [0.1,0.2,...] }
        """
        base = payload.get("base")
        x = payload.get("x")
        if base is None or x is None:
            return {"ok": False, "error": "missing base or x"}
        if not self.inference:
            return {"ok": False, "error": "inference engine not available"}
        try:
            out = self.inference.predict(base, x)
            return {"ok": True, "result": out}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def task_derive(self, payload: dict) -> dict:
        """
        Return only derived quantities from the winner pattern for `base`.
        """
        base = payload.get("base")
        if base is None:
            return {"ok": False, "error": "missing base"}
        if not self.inference:
            return {"ok": False, "error": "inference engine not available"}
        try:
            p = self.inference.predict(base, 0.0)
            return {"ok": True, "derived": p.get("derived", {})}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # New hook: ask RPL for a plan given a goal + PCX-annotated context
    def plan_for_goal(self, goal: str, context: dict = None) -> dict: # type: ignore
        try:
            ctx = context or {}
            # prefer PCX annotations if available
            if self.pcx:
                pcx = self.pcx.extract(ctx)
                ctx['_pcx'] = pcx
            if self.rpl:
                return self.rpl.plan(goal, ctx)
            return {'steps': [], 'justification': 'rpl-not-available', 'confidence': 0.0}
        except Exception as e:
            return {'steps': [], 'error': str(e), 'confidence': 0.0}

    def route(self, task_type: str, payload: dict) -> dict:
        t = task_type or ""
        if t == "predict":
            return self.task_predict(payload or {})
        if t == "derive":
            return self.task_derive(payload or {})
        # fallback to process for known process tasks
        try:
            return self.process(t, **(payload or {})) # type: ignore
        except Exception as e:
            return {"error": str(e)}


# Compatibility proxy so tests can import execute_pipeline from Task_Orchestrator
def execute_pipeline(pipeline, context):
    try:
        from Integration_Layer.Pipeline_Orchestrator import execute_pipeline as _exec
        return _exec(pipeline, context)
    except Exception:
        raise