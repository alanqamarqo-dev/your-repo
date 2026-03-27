import time
import json
import os
import urllib.request
import urllib.parse
import random
import re
from typing import List, Dict, Any, Optional

from .Knowledge_Graph import CognitiveIntegrationEngine  # type: ignore

# --- Polymorphic Search Constants ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
]

SEARCH_ENGINES = [
    ("https://lite.duckduckgo.com/lite/?q={}", "DuckDuckGo Lite", r'<a class="result-link" href="(.*?)">(.*?)</a>'),
    ("https://www.bing.com/search?q={}", "Bing", r'<a class="tilk" href="(.*?)".*?>(.*?)</a>'),
    ("https://search.brave.com/search?q={}", "Brave", r'<a href="(.*?)".*?class="snippet-title".*?>(.*?)</a>'),
    ("https://html.duckduckgo.com/html/?q={}", "DuckDuckGo HTML", r'<a class="result__a" href="(.*?)">(.*?)</a>'),
    ("https://www.ecosia.org/search?q={}", "Ecosia", r'<a href="(.*?)" class="result-title".*?>(.*?)</a>'),
    ("https://www.qwant.com/?q={}", "Qwant", r'url":"(.*?)","title":"(.*?)"'),
    ("https://api.search.yahoo.com/search?p={}", "Yahoo API", r'<url>(.*?)</url><title>(.*?)</title>')
]

AIRGAP_REQUEST_FILE = os.path.join("artifacts", "airgap_search_requests.json")
AIRGAP_RESPONSE_FILE = os.path.join("artifacts", "airgap_search_responses.json")


class EmergencyRetrieval:
    """Emergency retrieval built from available CIE components and memory.
    
    Enhanced with 'Emerging' capabilities:
    1. Polymorphic Search: Attempts to bypass network restrictions using rotating agents/engines.
    2. Airgap Bridge: Falls back to file-based requests if network is unreachable.

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

    def _clean_html(self, raw_html: str) -> str:
        return re.sub(r'<.*?>', '', raw_html)

    def _search_external(self, query: str) -> List[Dict[str, Any]]:
        """Attempts to search the external web using polymorphic strategies."""
        results = []
        print(f"🌐 [Emerging] Attempting external search for: '{query}'")
        
        # 1. Try Polymorphic Search (Direct Network)
        for url_template, name, regex_pattern in SEARCH_ENGINES:
            target_url = url_template.format(urllib.parse.quote(query))
            agent = random.choice(USER_AGENTS)
            
            try:
                req = urllib.request.Request(
                    target_url, 
                    headers={
                        'User-Agent': agent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5'
                    }
                )
                
                # Random sleep to mimic human behavior
                time.sleep(random.uniform(0.5, 1.5))
                
                with urllib.request.urlopen(req, timeout=4) as response:
                    html = response.read().decode('utf-8', errors='ignore')
                    
                    matches = re.findall(regex_pattern, html)
                    if matches:
                        for match in matches[:3]:
                            link, title = match
                            # Basic cleanup
                            if link.startswith('/url?q='):
                                link = link.split('/url?q=')[1].split('&')[0]
                            link = urllib.parse.unquote(link)
                            title = self._clean_html(title)
                            
                            if link.startswith('http'):
                                results.append({"source": f"external_{name}", "title": title, "url": link, "text": f"{title} ({link})"})
                        
                        if len(results) >= 3:
                            print(f"   ✅ Connected via {name}")
                            return results
            except Exception:
                continue # Try next engine silently

        # 2. Fallback to Airgap Bridge if network failed
        if not results:
            print("   ⚠️ Network unreachable. Falling back to Airgap Bridge.")
            self._airgap_request(query)
            # Check if we have any pending responses from previous runs
            results = self._check_airgap_responses(query)
            
        return results

    def _airgap_request(self, query: str):
        """Writes a search request to the airgap file."""
        requests = []
        if os.path.exists(AIRGAP_REQUEST_FILE):
            try:
                with open(AIRGAP_REQUEST_FILE, 'r', encoding='utf-8') as f:
                    requests = json.load(f)
            except:
                pass
                
        # Check if already requested recently
        for r in requests:
            if r.get('query') == query and r.get('status') == 'pending':
                return

        requests.append({
            "id": int(time.time()),
            "query": query,
            "status": "pending",
            "timestamp": time.ctime()
        })
        
        os.makedirs(os.path.dirname(AIRGAP_REQUEST_FILE), exist_ok=True)
        with open(AIRGAP_REQUEST_FILE, 'w', encoding='utf-8') as f:
            json.dump(requests, f, indent=2, ensure_ascii=False)
        print(f"   📡 Request queued in {AIRGAP_REQUEST_FILE}")

    def _check_airgap_responses(self, query: str) -> List[Dict[str, Any]]:
        """Checks for responses in the airgap response file."""
        if not os.path.exists(AIRGAP_RESPONSE_FILE):
            return []
            
        results = []
        try:
            with open(AIRGAP_RESPONSE_FILE, 'r', encoding='utf-8') as f:
                responses = json.load(f)
            
            for r in responses:
                # Fuzzy match or exact match
                if query.lower() in r.get('query', '').lower() or r.get('query', '').lower() in query.lower():
                    for item in r.get('results', []):
                        results.append({
                            "source": "airgap_bridge",
                            "text": f"{item.get('title')} - {item.get('snippet')} ({item.get('url')})",
                            "raw": item
                        })
        except Exception:
            pass
        return results

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

    def merge_retrieval_results(self, memory_results: List[Dict[str, Any]], knowledge_results: List[Dict[str, Any]], external_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge simple retrieval outputs: dedupe and summarize snippets."""
        merged_texts = []
        seen = set()
        
        # Prioritize external results if available
        for e in (external_results or []):
            t = (e.get('text') or '').strip()
            if t and t not in seen:
                merged_texts.append(f"[EXTERNAL] {t}"); seen.add(t)

        for m in (memory_results or []):
            t = (m.get('text') or '').strip()
            if t and t not in seen:
                merged_texts.append(t); seen.add(t)
        for k in (knowledge_results or []):
            t = (k.get('text') or '').strip()
            if t and t not in seen:
                merged_texts.append(t); seen.add(t)
        # produce short merged string
        merged = '\n'.join(merged_texts[:15])
        return {
            'merged': merged, 
            'memory_hits': len(memory_results or []), 
            'engine_hits': len(knowledge_results or []),
            'external_hits': len(external_results or [])
        }

    def retrieve(self, question: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """Run emergency retrieval: memory then adapters then external then merge."""
        start = time.time()
        
        # 1. Internal Search
        mem_res = self._query_memory(question, top_k=6)
        adv_res = self._query_adapters(question, domain=domain)
        
        # 2. External Search (Emerging Capability)
        # Only trigger if internal results are weak OR explicitly requested
        ext_res = []
        if len(mem_res) + len(adv_res) < 2 or "search" in question.lower() or "internet" in question.lower():
            ext_res = self._search_external(question)

        merged = self.merge_retrieval_results(mem_res, adv_res, ext_res)
        
        return {
            'question': question, 
            'domain': domain, 
            'memory_results': mem_res, 
            'adapter_results': adv_res, 
            'external_results': ext_res,
            'merged': merged, 
            'elapsed_s': round(time.time()-start, 3)
        }


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
