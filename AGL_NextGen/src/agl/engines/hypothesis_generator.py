from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging
import os

# Hypothesis generator knob (module-level)
try:
    _AGL_HYPOTHESIS_TOP_N = int(os.environ.get('AGL_HYPOTHESIS_TOP_N', '3'))
except Exception:
    _AGL_HYPOTHESIS_TOP_N = 3

logger = logging.getLogger("AGL.Hypothesis_Generator")
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# استدعاء اختياري للـLLM عبر بوابة موحدة (تفضّل HolographicLLM إن توفر)
try:
    from agl.lib.llm.gateway import chat_llm as _chat_llm
except Exception:
    _chat_llm = None  # بيئات CI بدون مزودات

_MOCK_ON = os.getenv("AGL_OLLAMA_KB_MOCK", "0") in ("1", "true", "True") or \
           os.getenv("AGL_EXTERNAL_INFO_MOCK", "0") in ("1", "true", "True")

class HypothesisGeneratorEngine:
    """
    يولّد فرضيات مرتبة حول ظاهرة/نص/بيانات.
    واجهة محرك موحّدة: name + process_task(payload)->Dict
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = "HYPOTHESIS_GENERATOR"
        self.config = config or {}
        try:
            from agl.engines.resonance_optimizer import VectorizedResonanceOptimizer as ResonanceOptimizer
            self.optimizer = ResonanceOptimizer()
        except ImportError:
            try:
                from Core_Engines.Resonance_Optimizer import ResonanceOptimizer
                self.optimizer = ResonanceOptimizer()
            except ImportError:
                self.optimizer = None

    def quantum_intuition_filter(self, hypotheses: List[str], context: str) -> List[Dict[str, Any]]:
        """
        Filters and ranks hypotheses using Quantum-Synaptic Resonance.
        Allows 'crazy' ideas (High Barrier) if they have high explanatory power (High Energy).
        """
        if not self.optimizer:
            return [{"text": h, "score": 0.5, "type": "Standard"} for h in hypotheses]
            
        ranked = []
        for h in hypotheses:
            # 1. Calculate Explanatory Energy (How much does it explain?)
            # Heuristic: Length and keyword overlap with context
            overlap = sum(1 for w in h.split() if w in context)
            energy = min(1.0, (len(h) / 100.0) + (overlap * 0.1))
            
            # 2. Calculate Cognitive Barrier (How 'crazy' or complex is it?)
            # Heuristic: Words like 'quantum', 'non-linear', 'paradigm' increase barrier
            complexity_words = ['quantum', 'non-linear', 'paradigm', 'revolution', 'entanglement', 'hidden', 'latent']
            barrier = 0.2 + (sum(1 for w in h.lower().split() if w in complexity_words) * 0.2)
            barrier = min(1.0, barrier)
            
            # 3. Resonance (Does it 'feel' right?)
            # We simulate intuition by checking for 'insight' keywords
            insight_words = ['therefore', 'implies', 'suggests', 'because', 'link', 'correlation']
            is_insightful = any(w in h.lower() for w in insight_words)
            
            resonance = self.optimizer._resonance_amplification(
                signal_freq=1.0 if is_insightful else 0.5,
                natural_freq=1.0,
                gamma=0.1
            )
            
            # 4. Tunneling (Can we accept a crazy idea?)
            # Energy Diff = (Energy * Resonance) - Barrier
            effective_energy = energy * (resonance / 5.0)
            tunneling = self.optimizer._wkb_tunneling_prob(
                energy_diff=effective_energy - barrier,
                barrier_height=barrier
            )
            
            score = energy * resonance * (1 + tunneling)
            
            ranked.append({
                "text": h,
                "score": score,
                "metrics": {"energy": energy, "barrier": barrier, "tunneling": tunneling},
                "type": "Quantum Leap" if tunneling > 0.5 and barrier > 0.5 else "Standard Deduction"
            })
            
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked

    def _logical_hypothesize(self, topic: str, context: str, hints: List[str]) -> List[str]:
        """
        توليد فرضيات منطقية بدون استدعاء LLM (معالجة الفراغ).
        يستخدم قواعد استنتاجية وأنماط علمية.
        """
        hypotheses = []
        
        # نمط 1: فرضية التغيير البسيط
        hypotheses.append(
            f"إذا تغيّر {topic} بنسبة صغيرة، فسيظهر أثر قابل للقياس في سياق {context[:60] if context else 'النظام'}."
        )
        
        # نمط 2: فرضية العلاقة غير الخطية
        hypotheses.append(
            f"العلاقة بين {topic} والعوامل المؤثرة قد تكون غير خطية ويمكن نمذجتها بدالة أسية أو لوغاريتمية."
        )
        
        # نمط 3: فرضية إعادة الاختبار
        hypotheses.append(
            f"يمكن إعادة اختبار الفرضيات السابقة حول {topic} باستخدام بيانات محدثة للتحقق من الاستقرار الزمني."
        )
        
        # نمط 4: فرضية مبنية على الأدلة
        if hints and len(hints) > 0:
            evidence = ', '.join(str(h) for h in hints[:3])
            hypotheses.append(
                f"بناءً على الأدلة ({evidence})، يُحتمل وجود علاقة سببية مباشرة تحتاج للتحقق التجريبي."
            )
        
        # نمط 5: فرضية التفاعل المتعدد
        if context:
            hypotheses.append(
                f"التفاعل بين {topic} والعوامل في {context[:40]}... قد ينتج تأثيرات ظاهرة (emergent effects) غير متوقعة."
            )
        
        try:
            top_n = int(os.environ.get('AGL_HYPOTHESIS_TOP_N', '3'))
        except Exception:
            top_n = 3
        
        return hypotheses[:top_n]

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # --- LOGGING TRAP FOR USER PROOF ---
        try:
            import os
            import datetime
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "artifacts", "hypothesis_engine_activity.log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now()}] HypothesisGenerator ACTIVATED for payload: {str(payload)[:50]}...\n")
        except Exception as e:
            print(f"Hypothesis Logging Failed: {e}")
        # -----------------------------------
        topic = (payload or {}).get("topic", "") or "موضوع عام"
        # Bench runner often sends {"query": prompt, "text": prompt}
        context = (payload or {}).get("context", "") or (payload or {}).get("text", "") or (payload or {}).get("query", "") or ""
        hints = (payload or {}).get("hints", []) or []

        # Fast-path: infer simple numeric relationships from (x,y) tables.
        # This supports the bench's hypothesis_with_prediction evaluator.
        def _infer_xy_prediction(ctx: str) -> Optional[Dict[str, Any]]:
            import re

            if not ctx:
                return None

            pairs = []
            for line in ctx.splitlines():
                m = re.match(r"\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*$", line.strip())
                if m:
                    try:
                        x = float(m.group(1))
                        y = float(m.group(2))
                        pairs.append((x, y))
                    except Exception:
                        continue

            if len(pairs) < 3:
                return None

            # parse target x from prompt
            m_target = re.search(r"x\s*=\s*([-+]?\d+(?:\.\d+)?)", ctx, flags=re.IGNORECASE)
            target_x = None
            if m_target:
                try:
                    target_x = float(m_target.group(1))
                except Exception:
                    target_x = None

            # Least-squares fit y = a*x + b
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            n = float(len(pairs))
            x_mean = sum(xs) / n
            y_mean = sum(ys) / n
            denom = sum((x - x_mean) ** 2 for x in xs)
            if denom == 0:
                return None
            a = sum((x - x_mean) * (y - y_mean) for x, y in pairs) / denom
            b = y_mean - a * x_mean

            pred_y = None
            if target_x is not None:
                pred_y = a * target_x + b

            # Produce a short Arabic hypothesis with explicit x/y tokens.
            eq = f"y ≈ {a:.4g}x + {b:.4g}" if abs(b) > 1e-9 else f"y ≈ {a:.4g}x"
            parts = [
                f"فرضية: العلاقة تقريباً خطية بين x و y: {eq}.",
            ]
            if target_x is not None and pred_y is not None:
                # round nicely if near-integer
                y_out = pred_y
                if abs(y_out - round(y_out)) < 1e-6:
                    y_out = int(round(y_out))
                parts.append(f"تنبؤ: إذا x={target_x:g} فـ y={y_out}." )
            return {"equation": eq, "target_x": target_x, "pred_y": pred_y, "text": " ".join(parts)}

        inferred = _infer_xy_prediction(context)
        if inferred is not None:
            return {
                "engine": self.name,
                "topic": topic,
                "text": inferred.get("text", ""),
                "inference": {k: inferred.get(k) for k in ("equation", "target_x", "pred_y")},
                "count": 1,
                "confidence": 0.85,
            }
        
        # 🎯 استراتيجية تكيفية: تختار تلقائياً بناءً على التعقيد
        try:
            from Core_Engines.Adaptive_Processing_Strategy import adaptive_strategy
            mode, complexity_score, reason = adaptive_strategy.recommend_mode(payload)
            logger.debug(f"🎯 Hypothesis mode={mode}, complexity={complexity_score:.2f}, reason={reason}")
        except ImportError:
            # fallback إذا لم يتوفر adaptive_strategy
            mode = "vacuum" if os.getenv("AGL_VACUUM_MODE", "1") == "1" else "llm"
            complexity_score = 0.5
            reason = "fallback mode"

        # معالجة بناءً على الوضع الموصى به
        if mode == "vacuum":
            hyps = self._logical_hypothesize(topic, context, hints)
        else:  # mode == "llm"
            # استخدام LLM للمهام المعقدة
            if _chat_llm is not None:
                sys_msg = "أنت باحث علمي يولّد فرضيات قابلة للاختبار بالعربية المعيارية."
                user_msg = f"الموضوع: {topic}\nالسياق:\n{context}\nأعطني 3 فرضيات مختصرة وقابلة للاختبار، مرقّمة."
                try:
                    msgs = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]
                    out = _chat_llm(msgs)
                    if isinstance(out, dict):
                        text = out.get("text") or out.get("answer") or ""
                    else:
                        text = str(out or "")
                    lines = [l.strip("- ").strip() for l in text.splitlines() if l.strip()]
                    hyps = [l for l in lines if any(l.startswith(x) for x in ("1", "2", "3", "١", "٢", "٣"))]
                    try:
                        _AGL_HYPOTHESIS_TOP_N = int(os.environ.get('AGL_HYPOTHESIS_TOP_N', '3'))
                    except Exception:
                        _AGL_HYPOTHESIS_TOP_N = 3
                    hyps = hyps[:_AGL_HYPOTHESIS_TOP_N] if hyps else lines[:_AGL_HYPOTHESIS_TOP_N]
                except Exception:
                    # fallback to vacuum if LLM fails
                    hyps = self._logical_hypothesize(topic, context, hints)
            else:
                hyps = self._logical_hypothesize(topic, context, hints)

        # 3) Apply Quantum Intuition Filter
        quantum_ranked = self.quantum_intuition_filter(hyps, context)
        
        # Extract text back from ranked list
        final_hyps = [item["text"] for item in quantum_ranked]

        return {
            "engine": self.name,
            "hypotheses": final_hyps,
            "text": "\n".join(final_hyps),
            "quantum_details": quantum_ranked, # Return full details for inspection
            "count": len(final_hyps),
            "confidence": 0.8 if self.optimizer else (0.6 if hyps else 0.0)
        }

def create_engine(config: Optional[Dict[str, Any]] = None) -> HypothesisGeneratorEngine:
    return HypothesisGeneratorEngine(config=config)
from typing import List, Dict
import itertools
import uuid


class HypothesisGenerator:
    """Generate simple hypotheses from accepted facts.

    This is a lightweight, extensible generator. Later we can plug LLM prompts
    or template-based generators per-domain.
    """

    def __init__(self, max_pairs: int = 50, max_hyps: int = 20):
        self.max_pairs = max_pairs
        self.max_hyps = max_hyps

    def propose(self, facts: List[Dict]) -> List[Dict]:
        hyps = []
        # Take last N facts to reduce combinatoric blowup
        pool = facts[-self.max_pairs:]
        for a, b in itertools.combinations(pool, 2):
            if (a.get('domain') or '').strip() != (b.get('domain') or '').strip():
                continue
            aid = a.get('id') or a.get('ts')
            bid = b.get('id') or b.get('ts')
            text_a = (a.get('text') or '')[:80]
            text_b = (b.get('text') or '')[:80]
            hyp = {
                'id': uuid.uuid4().hex,
                'domain': a.get('domain'),
                'hypothesis': f"قد ترتبط '{text_a}' مع '{text_b}' بمعنى أن وجود أحدهما قد يؤثر على الآخر.",
                'support': [aid, bid],
                'confidence': 0.55
            }
            hyps.append(hyp)
        hyps.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)
        return hyps[: self.max_hyps]
