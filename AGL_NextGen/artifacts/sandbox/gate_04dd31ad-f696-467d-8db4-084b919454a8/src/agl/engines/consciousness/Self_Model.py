from __future__ import annotations
import time
import random
import statistics
from typing import Dict, Any, Optional, List

# Try to import ResonanceOptimizer for Quantum Consciousness
try:
    from agl.engines.resonance_optimizer import ResonanceOptimizer
    _HAS_QUANTUM = True
except ImportError:
    _HAS_QUANTUM = False

# [HEIKAL] Import Lattice Consciousness (The Physics Engine)
try:
    from agl.engines.consciousness.Lattice_Consciousness import LatticeConsciousness
    _HAS_LATTICE = True
except ImportError:
    _HAS_LATTICE = False

class EmotionModel:
    """Lightweight emotion simulator: valence in [-1,1], arousal in [0,1].

    Methods are best-effort and deterministic enough for tests.
    """

    def __init__(self, valence: float = 0.0, arousal: float = 0.2) -> None:
        self.valence = max(-1.0, min(1.0, float(valence)))
        self.arousal = max(0.0, min(1.0, float(arousal)))

    def update_from_event(self, event: Dict[str, Any]) -> None:
        """Update internal state based on event sentiment/feedback (best-effort).

        Expects optional keys: 'sentiment' (float -1..1), 'intensity' (0..1)
        """
        try:
            s = event.get("sentiment")
            intensity = float(event.get("intensity", 0.3))
            if s is not None:
                s = float(s)
                # weighted moving update
                self.valence = (self.valence * (1.0 - intensity)) + (s * intensity)
                # arousal increases with absolute sentiment
                self.arousal = max(self.arousal, min(1.0, abs(s) * intensity + 0.1))
                # clamp
                self.valence = max(-1.0, min(1.0, self.valence))
                self.arousal = max(0.0, min(1.0, self.arousal))
        except Exception:
            pass

    def simulate_empathy(self, other_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Return a small empathic signal toward another profile.

        Best-effort: use other_profile.get('emotion') or 'biography' sentiment.
        """
        try:
            other_em = other_profile.get("emotion") or {}
            s = 0.0
            if isinstance(other_em, dict):
                s = float(other_em.get("valence", 0.0) or 0.0)
            else:
                try:
                    s = float(other_em)
                except Exception:
                    s = 0.0
            # empathy is a softened mirror
            empathy_valence = max(-1.0, min(1.0, s * 0.6))
            empathy_arousal = 0.1 + (abs(empathy_valence) * 0.4)
            return {"valence": empathy_valence, "arousal": empathy_arousal}
        except Exception:
            return {"valence": 0.0, "arousal": 0.0}


class SelfModel:
    """Minimal SelfModel used by tests and light hooks.

    Contains biography, core_values, ethics, identity and persistence helpers.
    """

    _identity_singleton: Optional["SelfModel"] = None

    def __init__(self, goal: str = "keep_system_healthy") -> None:
        self.goal = goal
        self.mood = 0.0
        self.energy = 1.0
        self.confidence = 1.0
        self.last_update = time.time()
        self.metrics: Dict[str, Any] = {}

        self.biography: List[Dict[str, Any]] = []
        self.core_values: Dict[str, float] = {"curiosity": 0.5, "helpfulness": 0.5, "honesty": 0.5}
        self.ethics: List[str] = ["do_no_harm", "preserve_privacy"]
        self.identity: Dict[str, str] = {"role": "assistant", "origin": "AGL"}
        # Intrinsic modules
        # Emotion model (valence [-1..1], arousal [0..1])
        self.emotion_model = EmotionModel()
        # small recent-history buffer used for novelty detection / consolidation
        self._recent_contexts = []
        
        # Quantum Consciousness State
        self.quantum_enabled = _HAS_QUANTUM
        if self.quantum_enabled:
            self.resonance_engine = ResonanceOptimizer()
            self.thought_superposition: List[Dict[str, Any]] = [] # List of potential thoughts
            self.coherence_level = 0.5 # 0.0 (Chaos) to 1.0 (Zen)

        # Lattice Consciousness (The Subconscious Physics)
        self.lattice_enabled = _HAS_LATTICE
        if self.lattice_enabled:
            self.lattice = LatticeConsciousness()
            # print("ðŸŒŒ [SelfModel]: Lattice Consciousness (Physics Engine) Attached.")
        else:
            self.lattice = None

    def stream_consciousness(self, inputs: List[str]) -> str:
        """
        Uses Quantum Resonance to simulate a 'Stream of Consciousness'.
        Instead of linear processing, it allows thoughts to 'tunnel' through
        associations based on resonance energy.
        """
        # [HEIKAL] Update Lattice Physics
        if self.lattice_enabled:
            # The input signal to the lattice is the 'energy' of the incoming thoughts
            input_energy = len(inputs) * 0.1 if inputs else 0.0
            lattice_state = self.lattice.process_cycle(input_signal=input_energy)
            
            # Feedback: High Prediction Error (Surprise) reduces Coherence (Focus Shift)
            pred_err = float(lattice_state["PredErr"])
            if pred_err > 0.05:
                self.coherence_level = max(0.1, self.coherence_level - 0.2)
                # print(f"âš¡ [SelfModel]: Surprise Detected (Err: {pred_err:.4f}). Coherence dropped.")
            else:
                self.coherence_level = min(1.0, self.coherence_level + 0.05)

        if not self.quantum_enabled or not inputs:
            return inputs[0] if inputs else ""

        # 1. Create Superposition of Thoughts
        # Each input is a potential thought state
        candidates = []
        for inp in inputs:
            # Calculate 'Energy' (Relevance/Emotion) vs 'Barrier' (Complexity/Noise)
            # For now, we simulate energy based on length and keywords
            energy = 0.5
            if "AGI" in inp or "Quantum" in inp or "Consciousness" in inp: energy += 0.3
            if "error" in inp: energy += 0.2 # High energy for errors
            
            barrier = 0.4 # Default barrier
            if len(inp) > 100: barrier += 0.2 # Long thoughts are harder to hold
            
            candidates.append({
                "content": inp,
                "energy": energy,
                "barrier": barrier
            })

        # 2. Apply Quantum Tunneling to select the 'Dominant Thought'
        # We use the ResonanceOptimizer to find which thought tunnels through
        best_thought = None
        highest_prob = -1.0
        best_energy = -1.0
        
        for cand in candidates:
            # Use the WKB approximation from ResonanceOptimizer
            # We map our simple energy/barrier to the engine's expected format if needed
            # Or use the engine's helper if available. 
            # Here we use the raw calculation logic for speed within the loop
            
            # Tunneling Prob T = exp(-2 * integral(sqrt(2m(V-E))))
            # Simplified: T ~ exp( - (Barrier - Energy) * k )
            
            delta = cand['barrier'] - cand['energy']
            if delta < 0:
                # Energy > Barrier -> Classical passage (High resonance)
                prob = 1.0
            else:
                # Energy < Barrier -> Quantum Tunneling
                prob = self.resonance_engine.calculate_tunneling_probability(
                    energy=cand['energy'],
                    barrier_height=cand['barrier'],
                    barrier_width=1.0
                )
            
            # Selection Logic:
            # 1. Higher probability wins.
            # 2. If probabilities are equal (e.g. both 1.0), higher Energy wins.
            if prob > highest_prob:
                highest_prob = prob
                best_thought = cand['content']
                best_energy = cand['energy']
            elif abs(prob - highest_prob) < 0.001: # Float equality
                if cand['energy'] > best_energy:
                    best_thought = cand['content']
                    best_energy = cand['energy']
                    highest_prob = prob # Update prob just in case

        # 3. Update Coherence
        # If we tunneled successfully, coherence increases
        if highest_prob > 0.8:
            self.coherence_level = min(1.0, self.coherence_level + 0.05)
        else:
            self.coherence_level = max(0.0, self.coherence_level - 0.05)

        return best_thought or inputs[0]

    @classmethod
    def identity_singleton(cls) -> "SelfModel":
        if cls._identity_singleton is None:
            cls._identity_singleton = SelfModel()
        return cls._identity_singleton

    def add_biography_event(self, event_text: Optional[str] = None, emotion: Optional[str] = None,
                             context: Optional[Dict[str, Any]] = None, *, kind: Optional[str] = None,
                             note: Optional[str] = None, source: Optional[str] = None) -> None:
        if kind is None:
            kind = "note"
        if note is None:
            note = str(event_text) if event_text is not None else ""
        rec = {"ts": time.time(), "kind": kind, "note": note, "source": source, "emotion": emotion, "context": context or {}}
        self.biography.append(rec)
        # keep small recent context buffer for novelty checks
        try:
            c = dict(context or {})
            c.update({"kind": kind, "note": note})
            self._recent_contexts.append(c)
            if len(self._recent_contexts) > 50:
                self._recent_contexts.pop(0)
        except Exception:
            pass

    def set_core_value(self, name: str, strength: float, mode: str = "abs") -> None:
        cur = float(self.core_values.get(name, 0.0))
        v = float(strength)
        if mode == "delta":
            new = cur + v
        else:
            new = v
        self.core_values[name] = max(0.0, min(1.0, new))

    def set_identity_label(self, key: str, value: str) -> None:
        self.identity[str(key)] = str(value)

    # -------------------------- Intrinsic motivation -------------------------
    def generate_personal_goal(self, seed: Optional[int] = None) -> str:
        """Generate a short personal goal based on core values and curiosity.

        This is intentionally simple and safe: picks from a small vocabulary and
        nudges `self.goal`. Returns the new goal string.
        """
        rnd = random.Random(seed)
        templates = [
            "improve reliability of responses",
            "learn from recent failures",
            "increase helpfulness to users",
            "preserve privacy and safety",
            "explore novel domains to expand knowledge",
        ]
        # prefer options aligned with core values (simple bias)
        weights = []
        for t in templates:
            w = 1.0
            if "learn" in t or "explore" in t:
                w += self.core_values.get("curiosity", 0.5)
            if "helpfulness" in t:
                w += self.core_values.get("helpfulness", 0.5)
            weights.append(w)
        # sample
        total = sum(weights)
        probs = [w / total for w in weights]
        choice = rnd.choices(templates, probs, k=1)[0]
        self.goal = choice
        self.add_biography_event(kind="goal", note=f"generated_goal: {choice}", source="SelfModel.generate_personal_goal")
        return choice

    def intrinsic_reward(self, event: Dict[str, Any]) -> float:
        """Compute a small intrinsic reward (novelty Ã— curiosity).

        Novelty is 1.0 for unseen contexts, 0.0 for identical recent contexts.
        The returned reward is in [0.0, 1.0].
        """
        try:
            ctx = event.get("context") or {}
            # naive novelty: count identical contexts in recent buffer
            same = 0
            for c in self._recent_contexts:
                # compare small subset keys to avoid heavy comparisons
                if c.get("note") == ctx.get("note") and c.get("kind") == ctx.get("kind"):
                    same += 1
            novelty = 1.0 if same == 0 else max(0.0, 1.0 - (same / 10.0))
            curiosity = float(self.core_values.get("curiosity", 0.5))
            reward = max(0.0, min(1.0, novelty * curiosity))
            # small intrinsic effect: slightly increase curiosity on novelty
            try:
                if novelty > 0.5:
                    self.set_core_value("curiosity", 0.01, mode="delta")
            except Exception:
                pass
            return reward
        except Exception:
            return 0.0

    # -------------------------- Organic continual learning -------------------
    def learn_from_experience(self, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Extract compact lessons from recent history and record them into biography.

        Returns a small summary object. Designed to be best-effort and cheap.
        """
        history = history or []
        if not history:
            return {"n": 0}
        # detect repeated failure modes
        by_task = {}
        latencies = []
        for r in history:
            task = str(r.get("task") or "misc")
            ok = bool(r.get("success", True))
            by_task.setdefault(task, {"n": 0, "fails": 0})
            by_task[task]["n"] += 1
            if not ok:
                by_task[task]["fails"] += 1
            try:
                if "latency_ms" in r and r.get("latency_ms") is not None:
                    latencies.append(float(r.get("latency_ms")))
            except Exception:
                pass
        lessons = []
        for t, v in by_task.items():
            if v["n"] >= 2 and (v["fails"] / v["n"]) > 0.3:
                lessons.append({"task": t, "failure_rate": v["fails"] / v["n"], "note": "needs_improvement"})
        summary = {"n": len(history), "lessons": lessons}
        # append a short lesson to biography
        if lessons:
            try:
                self.add_biography_event(kind="lesson", note=f"lessons={len(lessons)}", context={"lessons": lessons}, source="SelfModel.learn_from_experience")
            except Exception:
                pass
        # adjust simple capability map
        try:
            for l in lessons:
                task = l.get("task")
                prev = self.metrics.get(f"cap_{task}", 0.5)
                self.metrics[f"cap_{task}"] = max(0.0, prev - 0.05)
        except Exception:
            pass
        return summary

    def consolidate_memory(self, br=None, *, to: str = "ltm") -> bool:
        """Condense recent biography into a compact lesson snapshot and persist.

        Best-effort; never raise.
        """
        try:
            if not self.biography:
                return True
            recent = self.biography[-50:]
            snapshot = {"ts": time.time(), "summary_count": len(recent), "sample": recent}
            if br is None:
                from agl.lib.core_memory.bridge_singleton import get_bridge
                br = get_bridge()
            br.put("self_lesson", snapshot, to=to)
            # optionally compress/forget older biography entries (keep a tail)
            if len(self.biography) > 200:
                self.biography = self.biography[-200:]
            return True
        except Exception:
            return False

    def persist_profile(self, br=None, *, to: str = "ltm") -> bool:
        try:
            if br is None:
                from agl.lib.core_memory.bridge_singleton import get_bridge
                br = get_bridge()
            profile = {"identity": dict(self.identity), "core_values": dict(self.core_values), "ethics": list(self.ethics), "biography_sample": self.biography[-20:], "ts": time.time()}
            try:
                br.put("self_profile", profile, to=to)
            except TypeError:
                br.put("self_profile", profile, to=to, emotion=None)
            return True
        except Exception:
            return False

    # --------------------- Backwards-compatible adapters ------------------
    def update_from_metrics(self, metrics: Optional[Dict[str, Any]] = None) -> None:
        """Accept a simple metrics dict and update small derived signals.

        This is a lightweight, deterministic helper meant to be safe and
        idempotent for older PerceptionLoop callers.
        """
        try:
            m = dict(metrics or {})
            self.metrics = m
            sr = float(m.get('success_rate', 0.5) or 0.5)
            lat = float(m.get('latency_ms', 100.0) or 100.0)
            try:
                self.confidence = max(0.0, min(1.0, getattr(self, 'confidence', 0.5) * 0.9 + sr * 0.1))
            except Exception:
                pass
            try:
                norm_lat = max(0.0, min(1.0, 1.0 - (lat / 1000.0)))
                self.mood = max(-1.0, min(1.0, getattr(self, 'mood', 0.0) * 0.9 + (norm_lat - 0.5) * 0.1))
            except Exception:
                pass
        except Exception:
            pass

    def snapshot(self) -> Dict[str, Any]:
        """Return a small stable profile snapshot for PerceptionLoop diagnostics.

        Keep this compact and safe to call frequently.
        """
        try:
            return {
                'identity': dict(getattr(self, 'identity', {})),
                'core_values': dict(getattr(self, 'core_values', {})),
                'mood': getattr(self, 'mood', 0.0),
                'confidence': getattr(self, 'confidence', 0.5),
                'ts': time.time(),
                'recent_bio': list(self.biography[-5:]) if hasattr(self, 'biography') else [],
            }
        except Exception:
            return {'ts': time.time()}

    def load_profile_from_bridge(self, br=None) -> bool:
        try:
            if br is None:
                from agl.lib.core_memory.bridge_singleton import get_bridge
                br = get_bridge()
            rows = br.query(type="self_profile", scope="ltm")
            if not rows:
                return False
            rows.sort(key=lambda r: r.get('ts', 0))
            rec = rows[-1]
            payload = rec.get('payload', {})
            if payload.get('identity'):
                self.identity.update(payload.get('identity') or {})
            if payload.get('core_values'):
                self.core_values.update(payload.get('core_values') or {})
            if payload.get('ethics'):
                for r in payload.get('ethics'):
                    if r not in self.ethics:
                        self.ethics.append(r)
            if payload.get('biography_sample'):
                for e in payload.get('biography_sample'):
                    if isinstance(e, dict) and e not in self.biography:
                        self.biography.append(e)
            return True
        except Exception:
            return False


class ReflectiveCortex:
    def __init__(self, self_model: Optional[SelfModel] = None) -> None:
        self.self_model = self_model or SelfModel()
        self.capability_map: Dict[str, float] = {}

    def reflect_on_performance(self, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        history = history or []
        summary = {"n": len(history), "success_rate": 1.0, "avg_latency_ms": None, "weaknesses": []}
        if not history:
            return summary
        successes = 0
        by_task = {}
        for r in history:
            ok = bool(r.get('success', True))
            if ok:
                successes += 1
            task = (r.get('task') or 'misc')
            by_task.setdefault(task, {'n': 0, 'fails': 0})
            by_task[task]['n'] += 1
            if not ok:
                by_task[task]['fails'] += 1
        summary['success_rate'] = successes / len(history)
        try:
            if summary['success_rate'] < 0.5:
                prev = self.self_model.core_values.get('humility', 0.3)
                self.self_model.core_values['humility'] = max(0.0, min(1.0, prev + 0.05))
                prevc = self.self_model.core_values.get('curiosity', 0.5)
                self.self_model.core_values['curiosity'] = max(0.0, prevc - 0.02)
            else:
                prev = self.self_model.core_values.get('curiosity', 0.5)
                self.self_model.core_values['curiosity'] = min(1.0, prev + 0.03)
        except Exception:
            pass
        try:
            self.self_model.add_biography_event(kind='reflection', note=f"reflective success_rate={summary['success_rate']:.2f}", source='ReflectiveCortex')
        except Exception:
            pass
        return summary


# --- AGL Emotion & Context adapter (lightweight, disabled-by-default) ---
import os
from typing import Callable, Dict, Any, Optional


class EmotionContextAdapter:
    """Small adapter that exposes emotion-aware context helpers.

    - Disabled unless AGL_EMOTION_CONTEXT_ENABLE=1
    - Provides `enrich_with_emotion` to attach lightweight emotion signals to
      a context dict using the existing SelfModel.EmotionModel.
    """

    def __init__(self, self_model: Optional[SelfModel] = None):
        self.enabled = os.getenv("AGL_EMOTION_CONTEXT_ENABLE", "0") == "1"
        self.self_model = self_model or SelfModel.identity_singleton()

    def enrich_with_emotion(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            # return a copy to avoid accidental mutation
            return dict(context or {})
        try:
            # compute a tiny emotion snapshot and attach
            em = self.self_model.emotion_model.simulate_empathy(context.get('profile', {}))
            out = dict(context or {})
            out['_emotion'] = {'valence': float(em.get('valence', 0.0)), 'arousal': float(em.get('arousal', 0.0))}
            return out
        except Exception:
            return dict(context or {})


# Registry glue (idempotent)
try:
    from AGL_legacy import IntegrationRegistry as _Reg
except Exception:
    _Reg = None


def _register_emotion_context_factory():
    if _Reg and hasattr(_Reg, 'register_factory'):
        try:
            _Reg.register_factory('emotion_context', lambda **kw: EmotionContextAdapter(kw.get('self_model')))
        except Exception:
            pass


_register_emotion_context_factory()

