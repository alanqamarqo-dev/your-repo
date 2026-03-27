from typing import Any, Dict, List, Optional, Tuple, Callable

class MetaLearningEngine:
    """
    محرك تعلم-ميتا خفيف وآمن للاستيراد:
    - يجمع فرضيات + روابط سببية + أدلة اختيارية
    - ينتج ترتيبًا للفرضيات مع درجات وثقة تقريبية
    - واجهة ثابتة: name, process_task(payload), create_engine(config)
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = "Meta_Learning"
        self.config = config or {}
        # store learned simple principles per id
        # mapping: principle_id -> {"rule": callable, "desc": str, "confidence": float}
        self._principles: Dict[str, Dict[str, Any]] = {}
        self.reflection_loop_active = False

    def activate_reflection_loop(self):
        """
        Activates the continuous reflection loop.
        """
        self.reflection_loop_active = True
        print(f"[{self.name}] REFLECTION LOOP ACTIVATED.")

    def _score_hypothesis(
        self,
        h: str,
        n_edges: int,
        n_evidence: int,
        boost_words: Tuple[str, ...]
    ) -> float:
        base = 0.4 + 0.05 * n_edges + 0.03 * n_evidence
        if any(w in h for w in boost_words):
            base += 0.2
        return max(0.0, min(1.0, base))

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload:
          - text: str (اختياري)
          - causal_edges: List[tuple(str,str)] 例: [("X","Y"), ...]
          - hypotheses: List[str]
          - evidence: Optional[List[str]]  (docs/snippets)
        return:
          {
            "engine": "Meta_Learning",
            "ok": True,
            "ranked_hypotheses": [{"hypothesis": str, "score": float}],
            "meta_summary": {...}
          }
        """
        import os
        _META_EXAMPLES = int(os.environ.get('AGL_META_LEARNING_EXAMPLES', '12'))
        hyps: List[str] = (payload.get("hypotheses") or [])[:_META_EXAMPLES]
        edges = payload.get("causal_edges") or []
        evid = payload.get("evidence") or []

        boost_words = (
            "سبب", "يسبب", "ينتج", "يؤدي", "because", "causal", "leads to", "if"
        )

        scored = [
            {
                "hypothesis": h,
                "score": round(self._score_hypothesis(h, len(edges), len(evid), boost_words), 3)
            }
            for h in hyps
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)

        return {
            "engine": self.name,
            "ok": True,
            "ranked_hypotheses": scored,
            "meta_summary": {
                "n_inputs": {"edges": len(edges), "hypotheses": len(hyps), "evidence": len(evid)},
                "rule": "boost السببية + عدد الروابط + حجم الدليل",
            }
        }

    def auto_learn_skill(self, skill_id: str, examples: List[Tuple[Any, Any]], persist: bool = True) -> Dict[str, Any]:
        """
        Minimal auto-learn placeholder to satisfy tests.
        It 'learns' simple patterns by storing example count under a fake principle id.
        Returns metadata similar to the fuller implementation.
        """
        # Try to detect a simple rule: append suffix or prepend prefix
        stored = []
        if not examples:
            return {"skill": skill_id, "stored_principles": stored, "count": 0}

        # check append-suffix pattern: y == x + sfx
        sfx = None
        ok_suffix = True
        for x, y in examples:
            xs = str(x)
            ys = str(y)
            if not ys.startswith(xs):
                ok_suffix = False
                break
            cur = ys[len(xs):]
            if sfx is None:
                sfx = cur
            elif sfx != cur:
                ok_suffix = False
                break

        if ok_suffix and sfx is not None and sfx != "":
            pid = f"{skill_id}:append_suffix"
            def rule(v, _sfx=sfx):
                return str(v) + _sfx
            self._principles[pid] = {"rule": rule, "desc": f"append suffix '{sfx}'", "confidence": 0.8}
            stored.append(pid)

        # fallback: synthetic placeholder if no clear rule
        if not stored:
            pid = f"{skill_id}:synthetic"
            self._principles[pid] = {"rule": lambda v: v, "desc": "synthetic no-op", "confidence": 0.3}
            stored.append(pid)

        return {"skill": skill_id, "stored_principles": stored, "count": len(stored)}

    def continual_self_learning(self, skill_id: str, example_batches: List[List[Tuple[Any, Any]]], rounds: int = 3, eval_holdout: Optional[List[Tuple[Any, Any]]] = None, lr: float = 0.1) -> Dict[str, Any]:
        """
        Minimal continual learning loop: learn from batches, optionally evaluate on holdout and adjust confidences.
        Returns history with per-round eval and confidences for principles under the skill namespace.
        """
        history: Dict[str, Any] = {"rounds": []}
        for r in range(rounds):
            batch = example_batches[r] if r < len(example_batches) else []
            self.auto_learn_skill(skill_id, batch, persist=True)

            eval_res = None
            feedback = []
            if eval_holdout:
                correct = 0
                total = 0
                # pick first principle for this skill if available
                pids = [pid for pid in self._principles.keys() if isinstance(pid, str) and pid.startswith(f"{skill_id}:")]
                rule = None
                pid_used = pids[0] if pids else None
                if pid_used:
                    rule = self._principles[pid_used]["rule"]
                for x, y_true in eval_holdout:
                    total += 1
                    try:
                        pred = rule(x) if rule else None
                    except Exception:
                        pred = None
                    if pred == y_true:
                        correct += 1
                        if pid_used:
                            feedback.append({"id": pid_used, "correct": True})
                    else:
                        if pid_used:
                            feedback.append({"id": pid_used, "correct": False})
                acc = (correct / total) if total else None
                eval_res = {"accuracy": acc, "correct": correct, "total": total}
                # apply simple self_improve: adjust confidence slightly
                for f in feedback:
                    pid = f.get("id")
                    if pid in self._principles:
                        conf = float(self._principles[pid].get("confidence", 0.5))
                        if f.get("correct"):
                            conf = min(1.0, conf + lr * (1.0 - conf))
                        else:
                            conf = max(0.0, conf - lr * conf)
                        self._principles[pid]["confidence"] = conf

            confidences = {pid: meta.get("confidence") for pid, meta in self._principles.items() if pid.startswith(f"{skill_id}:")}
            history["rounds"].append({"round": r + 1, "eval": eval_res, "confidences": confidences})

        return history

    def transfer_principles_between_domains(self, mapping: Dict[str, str]) -> Dict[str, Any]:
        transferred = []
        for old_id, new_id in mapping.items():
            if old_id in self._principles and new_id:
                self._principles[new_id] = dict(self._principles[old_id])
                transferred.append(new_id)
        return {"count": len(transferred), "new_ids": transferred}

    def transfer_using_embeddings(self, principles: List[Dict[str, Any]], embed_fn: Optional[Callable[[str], List[float]]] = None, threshold: float = 0.6) -> Dict[str, Any]:
        """Optional embedding-based transfer helper.

        - `principles`: list of {'id': str, 'desc': str, 'confidence': float} or mapping-like
        - `embed_fn`: callable(text) -> vector (list[float]). If None, falls back to name-based copy.
        - `threshold`: similarity threshold for transfer.

        This method is non-destructive: it only writes new entries when similarity
        between a source principle and a target description exceeds `threshold`.
        """
        if not embed_fn:
            # fallback to name-based transfer: copy any principle whose id appears
            mapping = {p.get('id'): p.get('id') for p in principles if isinstance(p, dict) and p.get('id')}
            return self.transfer_principles_between_domains(mapping)

        # compute vectors for existing principles
        def _cos(a, b):
            try:
                sa = sum(x * x for x in a) ** 0.5
                sb = sum(x * x for x in b) ** 0.5
                if sa == 0 or sb == 0:
                    return 0.0
                return sum(x * y for x, y in zip(a, b)) / (sa * sb)
            except Exception:
                return 0.0

        # build index of existing principles' embeddings
        existing = []
        for pid, meta in self._principles.items():
            desc = meta.get('desc', '') or ''
            try:
                vec = embed_fn(desc)
            except Exception:
                vec = None
            existing.append((pid, desc, vec))

        transferred = []
        for item in principles:
            pid = item.get('id') if isinstance(item, dict) else None
            desc = item.get('desc') if isinstance(item, dict) else str(item)
            try:
                tvec = embed_fn(desc)
            except Exception:
                tvec = None
            if tvec is None:
                continue
            # find best matching existing principle
            best_pid = None
            best_sim = 0.0
            for eid, edesc, evec in existing:
                if evec is None:
                    continue
                sim = _cos(tvec, evec)
                if sim > best_sim:
                    best_sim = sim
                    best_pid = eid
            if best_sim >= threshold and best_pid:
                # create a transferred copy under a new id if provided or reuse pid
                new_id = pid or f"transferred:{best_pid}"
                self._principles[new_id] = dict(self._principles[best_pid])
                transferred.append({"from": best_pid, "to": new_id, "sim": best_sim})

        return {"count": len(transferred), "transfers": transferred}

    # Backwards-compatible alias required by some tests: cross_domain_transfer
    def cross_domain_transfer(self, insight: Dict[str, str]) -> Dict[str, Any]:
        """Simple shim that accepts a mapping or single-insight payload and
        performs a lightweight transfer. Returns a minimal status dict.
        """
        # allow both {'mapping': {...}} and direct mapping
        mapping = insight.get('mapping') if isinstance(insight, dict) and 'mapping' in insight else insight
        if not isinstance(mapping, dict):
            # fallback: nothing to transfer
            return {"ok": False, "transferred": False, "confidence": 0.0, "note": "invalid_input"}
        res = self.transfer_principles_between_domains(mapping)
        ok = bool(res.get('count', 0) > 0)
        return {"ok": True, "transferred": ok, "confidence": 0.65 if ok else 0.0, "note": "cross_domain_transfer"}

    def list_principles(self) -> List[Dict[str, Any]]:
        return [{"id": k, "desc": v.get("desc"), "confidence": v.get("confidence")} for k, v in sorted(self._principles.items())]

    # Backwards-compatible wrapper expected by some tests
    def extract_principles(self, examples: List[Tuple[Any, Any]] = None) -> List[Dict[str, Any]]:
        """Extract simple principles from examples.

        If examples provided and look numeric, attempt a simple affine fit y = a*x + b.
        Otherwise fall back to returning stored/listed principles.
        """
        if examples:
            # try simple linear fit for numeric examples
            try:
                xs = [float(x) for x, _ in examples]
                ys = [float(y) for _, y in examples]
                n = len(xs)
                if n >= 2:
                    mean_x = sum(xs) / n
                    mean_y = sum(ys) / n
                    num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
                    den = sum((xs[i] - mean_x) ** 2 for i in range(n))
                    if den != 0:
                        a = num / den
                        b = mean_y - a * mean_x
                        self._last_principles = [{"rule": f"y = {a:.3f}*x + {b:.3f}", "a": a, "b": b, "confidence": 0.9}]
                        return self._last_principles
            except Exception:
                pass
        # fallback: return currently stored summary
        self._last_principles = self.list_principles()
        return self._last_principles

    def few_shot_predict(self, x: Any):
        """Use the last extracted principle to make a prediction for x if available."""
        try:
            if hasattr(self, "_last_principles") and self._last_principles:
                p = self._last_principles[0]
                a = p.get("a")
                b = p.get("b")
                if a is not None and b is not None:
                    return a * float(x) + b
        except Exception:
            pass
        return None

def create_engine(config: Optional[Dict[str, Any]] = None) -> MetaLearningEngine:
    return MetaLearningEngine(config=config)

