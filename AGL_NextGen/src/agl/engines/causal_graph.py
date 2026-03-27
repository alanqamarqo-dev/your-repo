from __future__ import annotations
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
from typing import Any, Dict, List, Tuple, Optional
import logging
logger = logging.getLogger('AGL.Causal_Graph')
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter('[%(levelname)s] %(name)s: %(message)s'))
    logger.addHandler(h)
logger.setLevel(logging.INFO)
class CausalGraphEngine:
    """
    يبني علاقات سببية مبسّطة من نص/وقائع.
    واجهة محرك موحّدة: يملك name و process_task(input: Dict)->Dict
    """
    def __init__(self, config: Optional[Dict[str, Any]]=None) -> None:
        self.name = 'CAUSAL_GRAPH'
        self.config = config or {}
        self.depth_level = "standard"

    def set_depth_level(self, level: str):
        """
        Sets the depth level for causal reasoning.
        """
        self.depth_level = level
        print(f"[{self.name}] CAUSAL DEPTH LEVEL SET TO: {level}")

    @staticmethod
    def _extract_pairs(text: str) -> List[Tuple[str, str]]:
        """
        استخراج بدائي لعلاقات سبب→نتيجة بالاعتماد على مؤشرات لغوية عربية/إنجليزية.
        نسخة محسنة تفصل الجمل لتجنب الخلط بين السياقات.
        """
        import re
        if not text:
            return []
            
        # 1. تقسيم النص إلى جمل (Split into sentences)
        # نستخدم علامات الترقيم: نقطة، علامة تعجب، استفهام، فاصلة عربية، سطر جديد
        sentences = re.split(r'[.!?;،\n]+', text)
        
        cues = ['يسبب', 'يؤدي إلى', 'ينتج عنه', 'because', 'causes', 'leads to', 'results in']
        pairs: List[Tuple[str, str]] = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            for cue in cues:
                # نستخدم مسافات حول الكلمة المفتاحية لضمان أنها كلمة كاملة وليست جزءاً من كلمة
                # لكن للتبسيط سنبحث عنها كما هي مع التأكد من وجودها
                if cue in sentence:
                    parts = sentence.split(cue, 1) # Split only on the first occurrence
                    if len(parts) >= 2:
                        cause = parts[0].strip()
                        effect = parts[1].strip()
                        
                        # تنظيف بسيط (Cleanup)
                        if len(cause) > 120: cause = cause[-120:]
                        if len(effect) > 160: effect = effect[:160]
                        
                        if cause and effect:
                            pairs.append((cause, effect))
                            # نكتفي بأول علاقة نجدها في الجملة لمنع التكرار
                            break
        return pairs

    def abstract_merge(self, concept_a: Dict, concept_b: Dict) -> Dict:
        """
        🔗 [MULTIMODAL ABSTRACTION]
        Merges two disparate concepts to find their 'higher order' parent.
        Example: 'Circle' + 'Day Cycle' -> 'Cyclic Nature'
        """
        name_a = concept_a.get('name', 'A')
        name_b = concept_b.get('name', 'B')
        
        print(f"🔗 [ABSTRACT] Attempting to merge '{name_a}' and '{name_b}'...")
        
        # 1. Find overlapping properties
        props_a = set(concept_a.get('properties', []))
        props_b = set(concept_b.get('properties', []))
        common = props_a.intersection(props_b)
        
        # 2. Synthesize new Abstract Node
        if common:
            new_name = f"Meta_{name_a}_{name_b}"
            confidence = len(common) / max(len(props_a), len(props_b))
            return {
                "name": new_name,
                "type": "Abstract_Universal",
                "derived_from": [name_a, name_b],
                "common_law": list(common),
                "confidence": confidence
            }
        else:
            return {"error": "No abstraction possible. Concepts are orthogonal."}

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload المتوقع:
          - "text": نص حر أو ملخص واقعي
          - اختيارياً: "events": قائمة أحداث لتركيب علاقات زمنية/سببية لاحقاً
        """
        import re

        text = (payload or {}).get('text', '') or (payload or {}).get('query', '') or ''
        t = str(text or "")
        t_l = t.lower()

        # Hard-gate support: simple numeric interventions for linear models.
        # Expected patterns resemble:
        #   Y = 2*X + 1 ; do(X=4)
        m_do = re.search(r"do\s*\(\s*x\s*=\s*([-+]?\d+(?:\.\d+)?)\s*\)", t_l)
        m_eq = re.search(
            r"y\s*=\s*([-+]?\d+(?:\.\d+)?)\s*\*\s*x\s*([+-])\s*([-+]?\d+(?:\.\d+)?)",
            t_l,
        )
        m_eq2 = re.search(r"y\s*=\s*x\s*([+-])\s*([-+]?\d+(?:\.\d+)?)", t_l)
        if m_do and (m_eq or m_eq2):
            try:
                x_val = float(m_do.group(1))
                if m_eq:
                    a = float(m_eq.group(1))
                    sign = m_eq.group(2)
                    b = float(m_eq.group(3))
                    y_val = (a * x_val) + (b if sign == "+" else -b)
                    eq_repr = f"y = {a:g}*x {sign} {b:g}"
                else:
                    sign = m_eq2.group(1)
                    b = float(m_eq2.group(2))
                    y_val = x_val + (b if sign == "+" else -b)
                    eq_repr = f"y = x {sign} {b:g}"

                # produce an explanatory text containing do/x/y terms
                y_out = int(round(y_val)) if abs(y_val - round(y_val)) < 1e-9 else y_val
                answer_text = (
                    f"do(X={x_val:g}) => باستخدام النموذج {eq_repr} نحسب y={y_out}. "
                    f"because التدخل يثبت x عند {x_val:g} ثم نحسب y مباشرة من المعادلة."
                )
                return {
                    'engine': self.name,
                    'ok': True,
                    'mode': 'intervention_numeric',
                    'x': x_val,
                    'y': float(y_val),
                    'text': answer_text,
                }
            except Exception:
                # fall back to edge extraction
                pass

        pairs = self._extract_pairs(t)
        edges = [{'cause': c, 'effect': e, 'confidence': 0.55} for c, e in pairs]
        result = {'engine': self.name, 'edges': edges, 'nodes': list({n for pair in pairs for n in pair})}
        logger.debug('Causal edges: %s', result['edges'])
        return result
def create_engine(config: Optional[Dict[str, Any]]=None) -> CausalGraphEngine:
    return CausalGraphEngine(config=config)
import json
import os
from typing import List, Dict
class CausalGraph:
    def __init__(self, path: str='artifacts/causal_graph.json'):
        self.path = path
        self.nodes = {}
        self.edges = []
        self._load()
    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                    self.nodes = data.get('nodes', {})
                    self.edges = data.get('edges', [])
        except Exception:
            self.nodes = {}
            self.edges = []
    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as fh:
            json.dump({'nodes': self.nodes, 'edges': self.edges}, fh, ensure_ascii=False, indent=2)
    def upsert_from_hypotheses(self, hyps: List[Dict]):
        for h in hyps:
            hid = h.get('id')
            label = h.get('hypothesis')[:_AGL_PREVIEW_120]
            if hid not in self.nodes:
                self.nodes[hid] = {'label': label, 'domain': h.get('domain')}
            for s in h.get('support', []):
                self.edges.append({'src': s, 'dst': hid, 'rel': 'supports', 'confidence': h.get('confidence', 0.5)})
