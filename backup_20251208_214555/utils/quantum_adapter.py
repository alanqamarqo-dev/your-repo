"""Adapter to provide a stable `sample_hypotheses` interface around various brain/core implementations.
If the wrapped object already implements `sample_hypotheses`, calls are delegated.
Otherwise the adapter will try other methods and finally fall back to calling the local LLM endpoint.
"""
from typing import Any, List, Dict
import requests
import os
from utils.llm_tools import build_llm_url

class QuantumBrainAdapter:
    def __init__(self, core_obj: Any, fallback_model: str = None, timeout: int = 45):
        self._core = core_obj
        self._fallback_model = fallback_model or os.getenv('AGL_LLM_MODEL', 'qwen2.5:7b-instruct')
        try:
            self._timeout = int(os.getenv('AGL_HTTP_TIMEOUT', '45'))
        except Exception:
            self._timeout = timeout

    def sample_hypotheses(self, prompt: str, context: str = '') -> List[Dict[str, str]]:
        """Return a list of hypothesis-like dicts: [{'hypothesis': text}, ...]
        Delegates to wrapped core when possible, otherwise generates via LLM.
        """
        # 1) Direct delegate
        if hasattr(self._core, 'sample_hypotheses'):
            try:
                return self._core.sample_hypotheses(prompt, context=context)
            except Exception:
                pass

        # 2) Try a generic generate/infer method on the core
        for candidate in ('generate', 'infer', 'run', 'process_task'):
            if hasattr(self._core, candidate):
                try:
                    fn = getattr(self._core, candidate)
                    if callable(fn):
                        # try different calling conventions
                        try:
                            res = fn(prompt)
                        except TypeError:
                            try:
                                res = fn({'text': prompt, 'context': context})
                            except Exception:
                                res = None

                        if res:
                            # normalize to list of hypotheses
                            if isinstance(res, list):
                                return [{'hypothesis': str(x)} for x in res]
                            return [{'hypothesis': str(res)}]
                except Exception:
                    pass

        # 3) Fallback: call local LLM generate endpoint
        try:
            endpoint = build_llm_url('generate')
            payload = {
                'model': self._fallback_model,
                'prompt': f"Generate up to 3 concise hypotheses for the following prompt. Context: {context}\nPrompt: {prompt}\nHypotheses:\n1.",
                'stream': False,
                'options': {'temperature': 0.3, 'num_predict': 256}
            }
            resp = requests.post(endpoint, json=payload, timeout=self._timeout)
            if resp.status_code == 200:
                text = ''
                try:
                    # try common keys
                    body = resp.json()
                    text = body.get('response') or body.get('text') or body.get('result') or str(body)
                except Exception:
                    text = resp.text

                # split into lines and return first 3 non-empty lines as hypotheses
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                if not lines:
                    return [{'hypothesis': text}]
                # take up to 3
                return [{'hypothesis': lines[i]} for i in range(min(3, len(lines)))]
        except Exception:
            pass

        # ultimate fallback: single echo hypothesis
        return [{'hypothesis': str(prompt)}]

    def __getattr__(self, item: str) -> Any:
        # Delegate other attributes/methods to wrapped object
        return getattr(self._core, item)
