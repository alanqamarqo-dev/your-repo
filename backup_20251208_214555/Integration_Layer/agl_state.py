# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
import json
import os
import subprocess
from pathlib import Path

try:
    from Self_Improvement.meta_logger import MetaLogger
except Exception:
    MetaLogger = None


@dataclass
class AGLState:
    question: str
    project: str = "default"
    lang: str = "ar"
    ts: float = field(default_factory=time.time)
    session_id: Optional[str] = None
    intent: Optional[str] = None
    sub_tasks: List[Dict[str, Any]] = field(default_factory=list)
    engine_calls: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    # contextual relations between facts: list of {fact_a_id, fact_b_id, relation, confidence, ts}
    context_relations: List[Dict[str, Any]] = field(default_factory=list)
    # media context representations (simple fallback or metadata)
    media_ctx: List[Dict[str, Any]] = field(default_factory=list)
    # snapshots of intermediate states for replay/analysis
    snapshots: List[Dict[str, Any]] = field(default_factory=list)
    # knowledge-graph versioning (increment when KG updates)
    kg_version: int = 0
    # lightweight entity store for world-modeling (entity_id -> attrs)
    entities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    rag_used: bool = False

    def record_engine_call(self, engine: str, answer: str, meta: Optional[Dict[str, Any]] = None):
        entry = {"engine": engine, "answer": answer, "meta": meta or {}, "ts": time.time()}
        self.engine_calls.append(entry)
        return entry

    def add_evidence(self, doc_id: str, snippet: str, score: float = 0.0):
        self.evidence.append({"doc_id": doc_id, "snippet": snippet, "score": float(score)})

    def add_context_relation(self, fact_id_a: str, fact_id_b: str, relation: str, confidence: float = 0.5):
        ent = {"a": fact_id_a, "b": fact_id_b, "relation": relation, "confidence": float(confidence), "ts": time.time()}
        self.context_relations.append(ent)
        return ent

    def add_entity(self, entity_id: str, attrs: Optional[Dict[str, Any]] = None):
        """Add or update an entity in the lightweight entity store."""
        try:
            if entity_id not in self.entities:
                self.entities[entity_id] = {}
            if attrs:
                self.entities[entity_id].update(attrs)
            return self.entities[entity_id]
        except Exception:
            return {}

    def add_relation(self, subject_id: str, object_id: str, predicate: str, confidence: float = 0.5):
        """Higher-level wrapper to add an entity relation and record as context_relation."""
        try:
            self.add_entity(subject_id)
            self.add_entity(object_id)
            rel = {'a': subject_id, 'b': object_id, 'relation': predicate, 'confidence': float(confidence), 'ts': time.time()}
            self.context_relations.append(rel)
            # bump KG version to reflect structural change
            try:
                self.kg_version = int(self.kg_version) + 1
            except Exception:
                self.kg_version = 1
            return rel
        except Exception:
            return {}

    def get_world_model_summary(self) -> Dict[str, Any]:
        """Return a compact summary of the lightweight world model (entities + relations counts)."""
        return {
            'entities_count': len(self.entities),
            'relations_count': len(self.context_relations),
            'kg_version': getattr(self, 'kg_version', 0),
        }

    def get_context_confidence(self) -> float:
        """Estimate an overall context confidence score from relations' confidences."""
        try:
            if not self.context_relations:
                return 0.0
            vals = [float(r.get('confidence', 0.0)) for r in self.context_relations]
            return sum(vals) / max(1, len(vals))
        except Exception:
            return 0.0

    def add_media_ctx(self, media_meta: Dict[str, Any]):
        self.media_ctx.append(media_meta)
        return media_meta

    def summary(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "project": self.project,
            "lang": self.lang,
            "ts": self.ts,
            "session_id": self.session_id,
            "intent": self.intent,
            "sub_tasks": self.sub_tasks,
            "engines": [c.get("engine") for c in self.engine_calls],
            "evidence_count": len(self.evidence),
            "metrics": self.metrics,
            "context_relations_count": len(self.context_relations),
            "media_ctx_count": len(self.media_ctx),
            "snapshot_count": len(self.snapshots),
        }

    def tick(self, label: Optional[str] = None):
        """Record a snapshot of current state and write via MetaLogger."""
        snap = {
            'label': label or 'tick',
            'question': self.question,
            'intent': self.intent,
            'top_engines': [c.get('engine') for c in self.engine_calls[-3:]],
            'top_k_rag': [e.get('doc_id') for e in self.evidence[:5]],
            'context_relations': list(self.context_relations),
            'media_ctx': list(self.media_ctx),
            'ts': time.time(),
        }
        self.snapshots.append(snap)
        try:
            if MetaLogger is not None:
                # use session_id if present otherwise generate a transient id
                sid = getattr(self, 'session_id', None) or str(int(time.time()))
                MetaLogger.log_snapshot(sid, snap)
        except Exception:
            pass
        return snap

    def evaluate_and_score(self, final_answer: str, provenance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Compute a simple composite score for an answer using provenance and evidence.

        Returns a dict: {score: float (0..1), components: {...}}
        """
        try:
            prov = provenance or {}
            # grounding score: proportion of evidence with positive score
            if self.evidence:
                e_scores = [float(e.get('score', 0.0)) for e in self.evidence]
                grounding = sum([1 for s in e_scores if s > 0.2]) / max(1, len(e_scores))
                avg_e_score = sum(e_scores) / max(1, len(e_scores))
            else:
                grounding = 0.0
                avg_e_score = 0.0

            # provenance hint: prefer rag_shortcircuit or 'rag' source
            raw_src = None
            try:
                raw_src = prov.get('raw_provenance', {}).get('source') if isinstance(prov, dict) else None
            except Exception:
                raw_src = None
            src_boost = 0.1 if raw_src and 'rag' in str(raw_src) else 0.0

            # verification: if model flagged verified.ok False, penalize
            verified_ok = True
            try:
                verified_ok = bool(prov.get('verified', {}).get('ok', True)) if isinstance(prov, dict) else True
            except Exception:
                verified_ok = True
            # soften penalty if the answer appears substantial (long/structured/keyword-rich)
            verify_penalty = 0.2 if not verified_ok else 0.0

            # length/structure/keyword heuristics
            try:
                words = final_answer.split() if final_answer else []
                length_words = len(words)
                # length score: saturates around 200 words
                length_score = min(1.0, float(length_words) / 200.0)
            except Exception:
                length_score = 0.0

            try:
                import re
                # detect numbered or ordered lists (1., 1), Arabic numerals, or bullets
                struct_re = re.compile(r"(^|\n)\s*(\d+[\)\.]|[\u0660-\u0669]+[\)\.]|[-•▪])")
                has_structure = bool(struct_re.search(final_answer or ""))
                structure_score = 0.8 if has_structure else 0.0
            except Exception:
                structure_score = 0.0

            try:
                # domain-strong keywords that raise signal
                strong_keywords = ("استدامة", "ضغط", "تصميم", "تدفق", "الطاقة", "مخاطر", "أمن", "بنية", "هندسة")
                lower = (final_answer or "").lower()
                kw_hits = sum(1 for k in strong_keywords if k.lower() in lower)
                # normalized to 0..1 (saturate at 3 hits)
                keyword_score = min(1.0, float(kw_hits) / 3.0)
            except Exception:
                keyword_score = 0.0

            # simple fluency fallback (short answers are less fluent)
            fluency = 1.0 if length_words > 5 else 0.5

            # soften verification penalty when the answer is long/structured/keyword-rich
            if not verified_ok:
                if length_score >= 0.3 or structure_score >= 0.5 or keyword_score >= 0.3:
                    verify_penalty = 0.05
                else:
                    verify_penalty = 0.2

            # composite score (weighted sum emphasising grounding and content richness)
            score = (
                0.30 * grounding
                + 0.15 * avg_e_score
                + 0.20 * length_score
                + 0.10 * structure_score
                + 0.10 * keyword_score
                + src_boost
                - verify_penalty
            )

            # Additional explicit bonuses per request: structure/visual/depth
            try:
                lower = (final_answer or "").lower()
                # structure bonus: presence of sequential numbering markers
                structure_bonus = 0.15 if ("1." in final_answer and "2." in final_answer) or any(m in lower for m in ("أولًا", "ثانيًا", "ثالثًا", "١.", "٢.", "٣.")) else 0.0
                # visual/table bonus: ascii-art/table characters or fenced code blocks
                visual_markers = ("+---", "|", "```", "┌", "┐", "└", "┘", "+---")
                visual_bonus = 0.25 if any(vm in final_answer for vm in visual_markers) else 0.0
                # depth bonus: long and contains summary marker
                depth_bonus = 0.10 if len((final_answer or "").split()) > 100 and ("الخلاصة" in lower or "خلاصة" in lower) else 0.0
            except Exception:
                structure_bonus = visual_bonus = depth_bonus = 0.0

            # apply bonuses
            bonus_sum = float(structure_bonus) + float(visual_bonus) + float(depth_bonus)
            score = float(score) + bonus_sum
            # If any strong bonus present, give an extra calibration uplift so richly-structured
            # answers become competitive versus short safe answers.
            try:
                if bonus_sum > 0.0:
                    # calibration uplift: favor richly-structured answers
                    # If structure bonus present along with some length/keyword signal, give a larger boost.
                    if structure_bonus > 0.0 and (length_score > 0.1 or keyword_score > 0.5):
                        score += 0.35
                    else:
                        # smaller uplift otherwise
                        score += 0.15 + 0.5 * bonus_sum
            except Exception:
                pass

            # Aggressive calibration mode (opt-in via env) to push highly-structured answers
            try:
                if os.getenv('AGL_CALIBRATE_AGGRESSIVE', '0') == '1' and structure_bonus > 0.0:
                    score = min(1.0, score + 0.20)
            except Exception:
                pass

            score = max(0.0, min(1.0, float(score)))

            components = {
                'grounding': grounding,
                'avg_e_score': avg_e_score,
                'length_score': length_score,
                'structure_score': structure_score,
                'keyword_score': keyword_score,
                'fluency': fluency,
                'src_boost': src_boost,
                'verify_penalty': verify_penalty,
                'structure_bonus': structure_bonus,
                'visual_bonus': visual_bonus,
                'depth_bonus': depth_bonus,
            }
            return {'score': score, 'components': components}
        except Exception as e:
            return {'score': 0.0, 'components': {'error': repr(e)}}

    def trigger_learning_if_needed(self, final_answer: str, provenance: Optional[Dict[str, Any]] = None):
        """Persist learned fact and optionally trigger LoRA training based on thresholds.

        Controlled by env vars:
          AGL_REWARD_PERSIST_THRESHOLD (default 0.7) -> persist to artifacts/learned_facts.jsonl
          AGL_REWARD_TRAIN_THRESHOLD (default 0.9) -> call make_train_from_learned.py --train
        """
        try:
            ev = self.evaluate_and_score(final_answer, provenance or {})
            score = float(ev.get('score', 0.0))
            persist_th = float(os.getenv('AGL_REWARD_PERSIST_THRESHOLD', '0.7'))
            train_th = float(os.getenv('AGL_REWARD_TRAIN_THRESHOLD', '0.9'))

            persisted = False
            trained = False

            if score >= persist_th:
                # append to artifacts/learned_facts.jsonl
                learnt_fn = Path(os.getcwd()) / 'artifacts' / 'learned_facts.jsonl'
                learnt_fn.parent.mkdir(parents=True, exist_ok=True)
                # compute simple relations to existing learned facts
                relations = []
                try:
                    if learnt_fn.exists():
                        with learnt_fn.open('r', encoding='utf-8') as fh:
                            for ln in fh:
                                try:
                                    item = json.loads(ln)
                                except Exception:
                                    continue
                                # simple keyword overlap heuristic
                                a_text = (item.get('answer') or '')
                                b_text = final_answer or ''
                                a_tokens = set([w.strip().lower() for w in a_text.split() if w.strip()])
                                b_tokens = set([w.strip().lower() for w in b_text.split() if w.strip()])
                                if not a_tokens or not b_tokens:
                                    continue
                                overlap = len(a_tokens.intersection(b_tokens))
                                denom = max(1, min(len(a_tokens), len(b_tokens)))
                                conf = float(overlap) / float(denom)
                                if conf > 0:
                                    rel = {'existing_ts': item.get('ts'), 'overlap': overlap, 'confidence': conf, 'existing_score': item.get('score')}
                                    relations.append(rel)
                                    # record relation in state context_relations (use timestamps as ids)
                                    try:
                                        a_id = str(item.get('ts') or item.get('id') or '')
                                        b_id = str(time.time())
                                        self.add_context_relation(a_id, b_id, 'keyword_overlap', confidence=conf)
                                    except Exception:
                                        pass
                except Exception:
                    relations = []

                entry = {
                    'question': self.question,
                    'answer': final_answer,
                    'score': score,
                    'provenance': provenance or {},
                    'ts': time.time(),
                    'source': 'auto_reward',
                    'context_relations': relations,
                    'hypothesis_variants': provenance.get('hypothesis_variants') if isinstance(provenance, dict) else None,
                    'media_ctx': list(self.media_ctx) if self.media_ctx else None,
                }
                with learnt_fn.open('a', encoding='utf-8') as fh:
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                persisted = True

            if score >= train_th:
                # attempt to call make_train_from_learned.py --train
                try:
                    script = Path(os.getcwd()) / 'scripts' / 'make_train_from_learned.py'
                    cmd = [os.getenv('PYTHON', 'py'), str(script), '--train']
                    # pass min-score to ensure we're training on reasonable set
                    cmd += ['--min-score', str(os.getenv('AGL_TRAIN_MIN_SCORE', '0.75'))]
                    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                    trained = proc.returncode == 0
                    train_log = {'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}
                except Exception as e:
                    trained = False
                    train_log = {'error': repr(e)}
            else:
                train_log = {'note': 'below-train-threshold'}

            # log via MetaLogger if available
            try:
                if MetaLogger is not None:
                    class _S: pass
                    s = _S()
                    s.question = self.question
                    s.engine_calls = self.engine_calls
                    meta = MetaLogger.start_session(s)
                    meta.update({'reward_score': score, 'persisted': persisted, 'trained': trained, 'train_log': train_log})
                    MetaLogger.finish_session(meta, s)
            except Exception:
                pass

            return {'persisted': persisted, 'trained': trained, 'train_log': train_log, 'score': score}
        except Exception as e:
            return {'persisted': False, 'trained': False, 'train_log': {'error': repr(e)}, 'score': 0.0}
