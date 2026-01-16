from typing import Any, Dict, Optional, List
import os
import requests
import json

# limits for sample examples and graph edge samples used by analyzer
try:
    _AGL_ADV_META_EXAMPLES_LIMIT = int(os.environ.get('AGL_ADV_META_EXAMPLES_LIMIT', '5'))
except Exception:
    _AGL_ADV_META_EXAMPLES_LIMIT = 5
try:
    _AGL_ADV_META_EDGE_SAMPLE = int(os.environ.get('AGL_ADV_META_EDGE_SAMPLE', '4'))
except Exception:
    _AGL_ADV_META_EDGE_SAMPLE = 4
# controlled by AGL_ADV_META_EXAMPLES_LIMIT (default 5) and AGL_ADV_META_EDGE_SAMPLE (default 4)

# Configurable top-N for meta-reasoner summary (fallback to 3 for backward compatibility)
_META_TOP = int(os.environ.get('AGL_META_TOP_LIMIT', os.environ.get('AGL_ROUTER_RESULT_LIMIT', '3')))

class AdvancedMetaReasonerEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = "AdvancedMetaReasoner"
        self.config = config or {}
        self.llm_base_url = os.environ.get("AGL_LLM_URL", "http://localhost:11434")
        self.model = os.environ.get("AGL_LLM_MODEL", "qwen2.5:14b")

    def _call_llm_direct(self, system_prompt: str, user_prompt: str) -> str:
        """Direct call to Ollama."""
        url = f"{self.llm_base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.5, "num_predict": 1024}
        }
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json()['message']['content']
        except:
            pass
        return ""

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload expects:
          - ranked_hypotheses: List[{"hypothesis": str, "score": float}]
          - context_info: Optional[dict]
        returns:
          - plan: next steps (route suggestions)
          - calibrations: light tweaks for confidence/thresholds
        """
        if "meta_meta_abstraction" in payload:
            return self.recursive_meta_abstraction(payload["meta_meta_abstraction"])

        ranked: List[Dict[str, Any]] = payload.get("ranked_hypotheses") or []
        top = ranked[:_META_TOP]

        suggestions = []
        for item in top:
            h = item.get("hypothesis") if isinstance(item, dict) else None
            s = float(item.get("score", 0)) if isinstance(item, dict) else 0.0
            if not h:
                continue
            if s >= 0.7:
                suggestions.append({"action": "validate_with_RAG", "target": h, "priority": "high"})
                suggestions.append({"action": "generate_counter_example", "target": h})
            else:
                suggestions.append({"action": "seek_more_evidence", "target": h, "priority": "medium"})

        plan = {
            "next_steps": suggestions,
            "route": ["Causal_Graph", "Hypothesis_Generator", "Meta_Learning", "AdvancedMetaReasoner"]
        }
        calibrations = {
            "confidence_threshold": 0.65,
            "fallback_if_no_llm": True,
            "notes": "ارفع العتبة إذا ازداد الضجيج؛ اخفضها في سيناريوهات قليلة البيانات."
        }
        return {"engine": self.name, "ok": True, "plan": plan, "calibrations": calibrations}

    def recursive_meta_abstraction(self, concept_layer: List[str]) -> Dict[str, Any]:
        """
        [UPGRADE 2026] Meta-Meta Abstraction (TRUE AI)
        Takes a list of abstract concepts and attempts to find a Higher Order Principle
        that governs them all.
        """
        print(f"🌌 [META-META] Abstracting higher pattern from {len(concept_layer)} concepts...")
        
        system_prompt = (
            "You are a Meta-Reasoning Engine. Your goal is to find the single 'Higher Order Principle' that unifies the provided concepts. "
            "Think philosophically and abstractly. "
            "Return a JSON object with keys: 'higher_order_principle' (string), 'confidence' (float), 'explanation' (string)."
            "Do NOT return markdown. Return RAW JSON."
        )
        user_prompt = f"Concepts: {concept_layer}. Find the unifying principle."

        response = self._call_llm_direct(system_prompt, user_prompt)
        
        # Parse JSON
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
                
            data = json.loads(response)
            data["level"] = "Meta-Meta-2-Real"
            data["derived_from"] = concept_layer
            return data
        except Exception as e:
            return {
                "higher_order_principle": "Entropy_Reduction (Fallback)",
                "confidence": 0.1,
                "error": str(e)
            }

def create_engine(config: Optional[Dict[str, Any]] = None) -> AdvancedMetaReasonerEngine:
    return AdvancedMetaReasonerEngine(config=config)
"""Advanced meta-reasoner: analyze thinking quality using traces and long-term memory.

Provides:
- analyze_thinking_quality() -> dict: aggregates trace statistics and simple quality metrics
- generate_self_improvement_plan(max_actions=5) -> list: simple ranked actions
"""
from pathlib import Path
import json, statistics, time
from typing import List, Dict, Any
# optional import for graph-based checks
try:
    from agl.engines.causal_graph import CausalGraph
except Exception:
    try:
        from Core_Engines.Causal_Graph import CausalGraph
    except Exception:
        CausalGraph = None


TRACE_PATH = Path('artifacts') / 'traces' / 'trace_events.jsonl'
LONG_TERM = Path('artifacts') / 'memory' / 'long_term.jsonl'


def _read_jsonl(path: Path, limit: int = 1000) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out[-limit:]


def analyze_thinking_quality(limit: int = 200) -> Dict[str, Any]:
    """Analyze recent traces and long-term memory to compute simple quality signals.

    Returns a dict with counts, distribution of confidences, contradictions count,
    and simple heuristics like coverage and stability.
    """
    traces = _read_jsonl(TRACE_PATH, limit)
    mem = _read_jsonl(LONG_TERM, limit)

    stats: Dict[str, Any] = {}
    stats['n_traces'] = len(traces)
    stats['n_memory_entries'] = len(mem)

    # compute confidence distribution
    confs = []
    types = {}
    for t in traces:
        types[t.get('type')] = types.get(t.get('type'), 0) + 1
        try:
            c = t.get('payload', {}).get('confidence')
            if isinstance(c, (int, float)):
                confs.append(float(c))
        except Exception:
            pass

    stats['by_type'] = types
    stats['conf_mean'] = statistics.mean(confs) if confs else None
    stats['conf_median'] = statistics.median(confs) if confs else None
    stats['conf_std'] = statistics.pstdev(confs) if confs and len(confs) > 1 else 0.0

    # contradictions heuristic: count reasoning.check events with contradictions>0
    contradictions = 0
    for t in traces:
        if t.get('type') == 'reasoning.check':
            try:
                contradictions += int(t.get('payload', {}).get('contradictions') or 0)
            except Exception:
                pass
    stats['contradictions'] = contradictions

    # coverage heuristic: distinct domains / memory topics
    domains = {}
    for entry in mem:
        dom = entry.get('domain') or entry.get('base') or 'unknown'
        domains[dom] = domains.get(dom, 0) + 1
    stats['domain_counts'] = domains

    # simple signal: drift = fraction of low-confidence events
    low_conf = sum(1 for c in confs if c is not None and c < 0.4)
    stats['low_conf_frac'] = (low_conf / len(confs)) if confs else None

    stats['analyzed_at'] = time.time()

    # textual contradiction heuristic: look for opposing keywords in traces and memory
    neg_pairs = [('increase', 'decrease'), ('increases', 'decreases'), ('positive', 'negative'), ('high', 'low'), ('cause', 'prevent'), ('supports', 'contradict')]
    texts = []
    for t in traces:
        p = t.get('payload', {}) or {}
        for k in ('rationale', 'note', 'summary', 'hypothesis'):
            v = p.get(k)
            if isinstance(v, str) and v:
                texts.append(v.lower())
    for m in mem:
        try:
            s = json.dumps(m).lower()
            texts.append(s)
        except Exception:
            pass

    textual_conflicts = []
    for a, b in neg_pairs:
        has_a = any(a in t for t in texts)
        has_b = any(b in t for t in texts)
        if has_a and has_b:
            textual_conflicts.append({'pair': (a, b), 'examples': [t for t in texts if a in t or b in t][:_AGL_ADV_META_EXAMPLES_LIMIT]})

    stats['textual_contradictions'] = len(textual_conflicts)
    stats['textual_conflict_examples'] = textual_conflicts

    # graph-based checks if available
    graph_issues = []
    if CausalGraph is not None:
        try:
            cg = CausalGraph()
            incoming = {}
            for e in getattr(cg, 'edges', []) or []:
                dst = e.get('dst')
                incoming.setdefault(dst, []).append(e)
            for dst, edges in incoming.items():
                confs = [float(e.get('confidence') or 0.0) for e in edges]
                avg = (sum(confs) / len(confs)) if confs else 0.0
                # flag nodes with multiple low-confidence supports
                if len(edges) > 1 and avg < 0.4:
                    graph_issues.append({'node': dst, 'n_edges': len(edges), 'avg_conf': avg, 'sample_edges': edges[:_AGL_ADV_META_EDGE_SAMPLE]})
        except Exception:
            graph_issues = []

    stats['graph_issues'] = graph_issues
    return stats


def generate_self_improvement_plan(max_actions: int = 5) -> List[Dict[str, Any]]:
    """Generate a simple improvement plan based on thinking quality.

    Uses analyze_thinking_quality() and emits candidate actions ranked heuristically.
    """
    q = analyze_thinking_quality()
    actions: List[Dict[str, Any]] = []

    # If contradictions exist, prioritize consistency analysis
    if q.get('contradictions', 0) > 0:
        actions.append({
            'title': 'Investigate contradictions in causal reasoning',
            'reason': f"Found {q.get('contradictions')} contradiction events in recent traces",
            'action': 'run_consistency_audit',
            'impact_score': 0.9,
        })

    # If many low-confidence events, collect more data or increase validation
    low_conf = q.get('low_conf_frac')
    if (low_conf is not None) and (isinstance(low_conf, (int, float)) and low_conf > 0.25):
        actions.append({
            'title': 'Increase validation and data collection',
            'reason': f"{q.get('low_conf_frac'):.2f} of recent decisions have low confidence",
            'action': 'collect_additional_data_and_tests',
            'impact_score': 0.8,
        })

    # If memory shows domain imbalance, suggest targeted harvesting
    domain_counts = q.get('domain_counts', {}) or {}
    if domain_counts:
        sorted_domains = sorted(domain_counts.items(), key=lambda kv: kv[1])
        if len(sorted_domains) > 0:
            least = sorted_domains[0]
            actions.append({
                'title': 'Targeted fact harvesting',
                'reason': f"Domain '{least[0]}' underrepresented ({least[1]} entries)",
                'action': 'harvest_domain_facts',
                'impact_score': 0.6,
                'metadata': {'domain': least[0]}
            })

    # fallback: add a test-coverage action if traces are small
    if q.get('n_traces', 0) < 20:
        actions.append({
            'title': 'Increase trace instrumentation coverage',
            'reason': 'Too few trace events for reliable meta-reasoning',
            'action': 'add_tracing_to_more_components',
            'impact_score': 0.4,
        })

    # sort by impact_score desc and return top-N
    actions = sorted(actions, key=lambda a: a.get('impact_score', 0.0), reverse=True)[:max_actions]
    return actions


if __name__ == '__main__':
    print(json.dumps(analyze_thinking_quality(), indent=2, ensure_ascii=False))
