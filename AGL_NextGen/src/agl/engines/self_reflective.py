"""Self-Reflective engine: inspects reasoning traces and produces a short analysis
about logical gaps, contradictions, confidence propagation, and suggested fixes.
"""
from typing import Any, Dict, List, Optional
# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_PREVIEW_120 = _to_int('AGL_PREVIEW_120', 120)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import time
class SelfReflectiveEngine:
    def __init__(self, config: Optional[Dict[str, Any]]=None):
        self.name = 'Self_Reflective'
        self.config = config or {}
    def _find_contradictions(self, trace: List[Dict[str, Any]]) -> List[str]:
        seen = {}
        issues = []
        for step in trace:
            for claim in step.get('assertions', []):
                key = claim.get('prop') if isinstance(claim, dict) else str(claim)
                val = claim.get('value') if isinstance(claim, dict) else True
                if key in seen and seen[key] != val:
                    issues.append(f"Contradiction on '{key}': {seen[key]} vs {val}")
                seen[key] = val
        return issues
    def _compute_confidence(self, trace: List[Dict[str, Any]]) -> float:
        vals = []
        for s in trace:
            try:
                c = float(s.get('confidence', 0.5))
            except Exception:
                c = 0.5
            vals.append(max(0.0, min(1.0, c)))
        if not vals:
            return 0.5
        return sum(vals) / len(vals)
    def _suggest_improvements(self, trace: List[Dict[str, Any]]) -> List[str]:
        suggestions = []
        if len(trace) < 3:
            suggestions.append('Expand intermediate reasoning steps to justify derivations.')
        for i, s in enumerate(trace):
            try:
                c = float(s.get('confidence', 0.0))
            except Exception:
                c = 0.0
            if c < 0.4:
                suggestions.append(f'Step {i + 1} has low confidence ({c:.2f}); add evidence or checks.')
        return suggestions
    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Expect payload with 'reasoning_trace': List[{'step':str, 'assertions':[...], 'confidence':float}]"""
        trace = payload.get('reasoning_trace') or []
        issues = self._find_contradictions(trace)
        conf = self._compute_confidence(trace)
        suggestions = self._suggest_improvements(trace)
        analysis = {'engine': self.name, 'ok': True, 'summary': {'n_steps': len(trace), 'avg_confidence': round(conf, 3), 'n_issues': len(issues)}, 'issues': issues, 'suggestions': suggestions}
        return analysis
def create_engine(config: Optional[Dict[str, Any]]=None) -> SelfReflectiveEngine:
    return SelfReflectiveEngine(config=config)
class CuriosityEngine:
    """Lightweight Curiosity engine that detects curiosity triggers from
    event streams and registers simple learning goals / knowledge gaps.
    - learning_goals: list of generated learning objectives
    - knowledge_gaps: set of short identifiers/topics that appear under-explored
    """
    def __init__(self, logger: Optional[Any]=None):
        self.learning_goals: List[str] = []
        self.knowledge_gaps = set()
        self.logger = logger
        if self.logger is None:
            try:
                from Core_Consciousness.State_Logger import StateLogger as _SL
                try:
                    self.logger = _SL()
                except Exception:
                    self.logger = None
            except Exception:
                self.logger = None
    def detect_curiosity_triggers(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return a list of detected 'questions' or gaps based on simple heuristics.
        Heuristics (conservative):
        - events with type 'question' or 'unknown' produce direct triggers
        - repeated 'error' or 'failure' events on same topic => knowledge gap
        - low-confidence traces (confidence key < 0.5) generate targets
        """
        triggers = []
        freq = {}
        for ev in events or []:
            t = ev.get('type') or ev.get('event_type') or ''
            payload = ev.get('payload') or {}
            text = None
            if isinstance(payload, dict):
                text = payload.get('text') or payload.get('query') or payload.get('question')
            if not text and isinstance(ev.get('payload'), str):
                text = ev.get('payload')
            if t in ('question', 'unknown'):
                q = text or ev.get('summary') or 'unspecified_question'
                triggers.append({'type': 'question', 'text': q})
                self.knowledge_gaps.add(q[:128])
            if t in ('error', 'failure'):
                topic = (text or ev.get('type') or 'error').strip()
                freq[topic] = freq.get(topic, 0) + 1
            try:
                conf = float(ev.get('confidence', 1.0))
            except Exception:
                conf = 1.0
            if conf < 0.5:
                q = text or ev.get('summary') or f'low_conf_{t}'
                triggers.append({'type': 'low_confidence', 'text': q, 'confidence': conf})
                self.knowledge_gaps.add(q[:128])
        for topic, c in freq.items():
            if c >= 2:
                goal = f'Investigate repeated failures on: {topic}'
                self.learning_goals.append(goal)
                triggers.append({'type': 'learning_goal', 'text': goal})
        return triggers
    def register_question(self, question: Dict[str, Any]) -> None:
        """Record a detected question into the StateLogger (best-effort)."""
        try:
            rec = {'ts': time.time(), 'curiosity': question}
            if self.logger and hasattr(self.logger, 'log'):
                try:
                    self.logger.log({'curiosity': question}, {'source': 'CuriosityEngine'})
                except Exception:
                    try:
                        if hasattr(self.logger, 'snapshot'):
                            self.logger.snapshot({'curiosity': question}, tags={'phase': 'curiosity'})
                    except Exception:
                        pass
            else:
                import json, os
                os.makedirs('artifacts', exist_ok=True)
                with open('artifacts/curiosity_log.jsonl', 'a', encoding='utf-8') as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
        except Exception:
            pass
    def analyze_patterns(self, log_path: str='artifacts/conscious_state_log.jsonl') -> Dict[str, Any]:
        """Lightweight analysis over the conscious state log to detect topics and counts.
        Returns a small summary dict: {"by_keyword": {k:count}, "n_records": N}
        """
        summary = {'by_keyword': {}, 'n_records': 0}
        try:
            import json
            with open(log_path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    try:
                        o = json.loads(line)
                    except Exception:
                        continue
                    summary['n_records'] += 1
                    text = ''
                    if isinstance(o.get('intent'), dict):
                        text = text + ' ' + str(o.get('intent').get('text') or '')
                    snap = o.get('snapshot') or {}
                    if isinstance(snap, dict):
                        text = text + ' ' + str(snap.get('goal') or '')
                    for word in (text or '').split():
                        if len(word) < 3:
                            continue
                        w = word.lower().strip('.,"\'()[]')
                        summary['by_keyword'][w] = summary['by_keyword'].get(w, 0) + 1
        except Exception:
            pass
        return summary
    def generate_curiosity_questions(self, main_question: str, context: dict | None=None, max_questions: int=3) -> list[str]:
        """Produce a short list of curiosity / follow-up questions.
        Uses detect_curiosity_triggers when available, otherwise uses
        conservative fallbacks. Returns a list of question strings.
        """
        out = []
        try:
            events = []
            if isinstance(context, dict) and 'recent_events' in context:
                events = context.get('recent_events') or []
            events = [{'type': 'question', 'payload': {'text': main_question}}] + list(events)
            if hasattr(self, 'detect_curiosity_triggers'):
                raw = self.detect_curiosity_triggers(events)
                for r in raw:
                    if isinstance(r, dict):
                        txt = r.get('text') or r.get('payload') or ''
                    else:
                        txt = str(r)
                    if txt:
                        out.append(str(txt))
        except Exception:
            out = []
        if not out:
            try:
                out = [f'Could you clarify or give an example of: {main_question[:_AGL_PREVIEW_120]}?']
            except Exception:
                out = ['Can you clarify this question?']
        try:
            import os
            _CURIO_MAX = int(os.environ.get('AGL_CURIO_MAX_QUESTIONS', str(max_questions)))
        except Exception:
            _CURIO_MAX = max_questions
        return out[:_CURIO_MAX]
    def evaluate_curiosity_quality(self, questions: list) -> float:
        """Return a heuristic quality score in [0.0, 1.0] for a list of questions.
        Uses analyze_patterns for a slight boost when many records exist.
        """
        try:
            if not questions:
                return 0.0
            score = min(0.95, 0.25 + 0.25 * len(questions))
            if hasattr(self, 'analyze_patterns'):
                try:
                    summary = self.analyze_patterns()
                    if summary and summary.get('n_records', 0) > 10:
                        score = min(0.99, score + 0.1)
                except Exception:
                    pass
            return float(score)
        except Exception:
            return 0.5
def create_curiosity_engine(config: Optional[Dict[str, Any]]=None):
    logger = None
    try:
        from Core.C_Layer.state_logger import StateLogger as _CLS
        logger = _CLS()
    except Exception:
        try:
            from Core_Consciousness.State_Logger import StateLogger as _S2
            logger = _S2()
        except Exception:
            logger = None
    return CuriosityEngine(logger=logger)
