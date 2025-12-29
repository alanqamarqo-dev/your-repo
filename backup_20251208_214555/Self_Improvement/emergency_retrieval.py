import time
import json
from typing import List, Dict, Any, Optional

from .Knowledge_Graph import CognitiveIntegrationEngine  # type: ignore


class EmergencyRetrieval:
    """Emergency retrieval built from available CIE components and memory.

    Usage:
        cie = CognitiveIntegrationEngine(); cie.connect_engines(); er = EmergencyRetrieval(cie)
        res = er.retrieve(question, domain)
    """
    def __init__(self, cie: CognitiveIntegrationEngine):
        self.cie = cie
        # ensure adapters are connected
        try:
            self.cie.connect_engines()
        except Exception:
            pass
        self.components = self.scan_components()

    def scan_components(self) -> Dict[str, Any]:
        """Scan CIE for memory and knowledge-like adapters.
        Returns a dict with possible keys: 'memory', adapter_name->adapter_instance
        """
        comps: Dict[str, Any] = {}
        # memory/collective
        try:
            if getattr(self.cie, 'memory', None) is not None:
                comps['memory'] = self.cie.memory
            elif getattr(self.cie, 'collective', None) is not None:
                comps['collective'] = self.cie.collective
        except Exception:
            pass

        # gather adapters by name
        try:
            for a in getattr(self.cie, 'adapters', []) or []:
                try:
                    nm = getattr(a, 'name', None) or type(a).__name__
                    comps[str(nm)] = a
                except Exception:
                    continue
        except Exception:
            pass

        return comps

    def _query_memory(self, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        out = []
        try:
            mem = self.components.get('memory') or self.components.get('collective')
            if not mem:
                return out
            # try common interfaces
            if hasattr(mem, 'query_shared_memory'):
                words = [w for w in (question or '').split() if len(w) > 3][:6]
                recs = mem.query_shared_memory(keywords=words, limit=top_k)
                for r in recs:
                    out.append({'source': 'collective', 'text': json.dumps(r, ensure_ascii=False)})
                return out
            if hasattr(mem, 'recall'):
                rec = mem.recall(k=top_k)
                if isinstance(rec, dict):
                    # flatten
                    for k, v in rec.items():
                        if isinstance(v, list):
                            for it in v:
                                out.append({'source': 'memory', 'text': json.dumps(it, ensure_ascii=False)})
                return out
        except Exception:
            pass
        return out

    def _query_adapters(self, question: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        # prefer explicit retriever-like names
        pref_names = ['GK_retriever', 'retriever', 'Advanced_Retrieval', 'Semantic_Search_Engine', 'hosted_storyqa', 'hosted_llm']
        # iterate adapters preferring named order
        seen = set()
        for name in pref_names:
            a = self.components.get(name)
            if a is None:
                # try case-insensitive match
                for k, v in self.components.items():
                    if k.lower() == name.lower():
                        a = v; break
            if a is None:
                continue
            try:
                # call adapter.infer with a compact problem dict
                prob = {'title': question, 'question': question}
                r = a.infer(prob, context=[], timeout_s=3.0)
                # extract answer/snippets
                content = r.get('content') if isinstance(r, dict) else None
                text = ''
                if isinstance(content, dict):
                    # try common keys
                    for k in ('answer', 'snippets', 'text', 'result'):
                        if k in content:
                            v = content.get(k)
                            if isinstance(v, list):
                                text = text + ' ' + ' '.join([str(x) for x in v[:3]])
                            else:
                                text = text + ' ' + str(v)
                    if not text:
                        try:
                            text = json.dumps(content, ensure_ascii=False)
                        except Exception:
                            text = str(content)
                else:
                    text = str(r)
                results.append({'engine': getattr(a, 'name', name), 'text': text.strip(), 'raw': r})
                seen.add(getattr(a, 'name', name))
            except Exception:
                continue

        # as fallback, query any adapter that contains 'retriev' or 'knowledge' in name
        for k, a in list(self.components.items()):
            if k in ('memory', 'collective'): continue
            kn = k.lower()
            if any(tok in kn for tok in ('retriev', 'knowledge', 'search')) and k not in seen:
                try:
                    prob = {'title': question, 'question': question}
                    r = a.infer(prob, context=[], timeout_s=3.0)
                    content = r.get('content') if isinstance(r, dict) else None
                    text = ''
                    if isinstance(content, dict):
                        for kk in ('answer','snippets','text','result'):
                            if kk in content:
                                v = content.get(kk)
                                if isinstance(v, list):
                                    text = text + ' ' + ' '.join([str(x) for x in v[:3]])
                                else:
                                    text = text + ' ' + str(v)
                        if not text:
                            text = json.dumps(content, ensure_ascii=False)
                    else:
                        text = str(r)
                    results.append({'engine': getattr(a, 'name', k), 'text': text.strip(), 'raw': r})
                except Exception:
                    continue

        return results

    def merge_retrieval_results(self, memory_results: List[Dict[str, Any]], knowledge_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge simple retrieval outputs: dedupe and summarize snippets."""
        merged_texts = []
        seen = set()
        for m in (memory_results or []):
            t = (m.get('text') or '').strip()
            if t and t not in seen:
                merged_texts.append(t); seen.add(t)
        for k in (knowledge_results or []):
            t = (k.get('text') or '').strip()
            if t and t not in seen:
                merged_texts.append(t); seen.add(t)
        # produce short merged string
        merged = '\n'.join(merged_texts[:10])
        return {'merged': merged, 'memory_hits': len(memory_results or []), 'engine_hits': len(knowledge_results or [])}

    def retrieve(self, question: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """Run emergency retrieval: memory then adapters then merge."""
        start = time.time()
        mem_res = self._query_memory(question, top_k=6)
        adv_res = self._query_adapters(question, domain=domain)
        merged = self.merge_retrieval_results(mem_res, adv_res)
        return {'question': question, 'domain': domain, 'memory_results': mem_res, 'adapter_results': adv_res, 'merged': merged, 'elapsed_s': round(time.time()-start, 3)}


# Helper functions

def activate_existing_retrieval(cie: CognitiveIntegrationEngine):
    """Return a retrieval adapter instance from CIE if present (best-effort)."""
    try:
        cie.connect_engines()
    except Exception:
        pass
    for name in ('GK_retriever', 'retriever', 'Advanced_Retrieval', 'hosted_storyqa', 'hosted_llm'):
        for a in getattr(cie, 'adapters', []) or []:
            if getattr(a, 'name', '').lower() == name.lower():
                return a
    return None


def build_basic_retrieval(cie: CognitiveIntegrationEngine):
    """Build a basic retriever that queries the CIE collective memory if available."""
    class BasicRetriever:
        def __init__(self, mem):
            self.mem = mem
        def retrieve(self, question, top_k=5):
            try:
                if hasattr(self.mem, 'query_shared_memory'):
                    words = [w for w in (question or '').split() if len(w) > 3][:6]
                    return self.mem.query_shared_memory(keywords=words, limit=top_k)
                if hasattr(self.mem, 'recall'):
                    r = self.mem.recall(k=top_k)
                    out = []
                    for v in (r.get('stm', []) or []) + (r.get('ltm', []) or []):
                        out.append(v)
                    return out
            except Exception:
                return []
            return []
    mem = getattr(cie, 'memory', None) or getattr(cie, 'collective', None)
    return BasicRetriever(mem)
