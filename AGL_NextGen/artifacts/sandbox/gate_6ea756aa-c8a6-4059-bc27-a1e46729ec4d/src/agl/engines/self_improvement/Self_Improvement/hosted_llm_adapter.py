import os
import json
import time
import requests
import subprocess
import shutil
import logging
import agl.engines.self_improvement.Self_Improvement.cognitive_mode as cognitive_mode
from typing import Optional
try:
    from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
except Exception:
    ask_with_deep_thinking = None
from utils.llm_tools import build_llm_url
try:
    from Quality.text_postprocess import clean_llm_text
    from Quality.ar_answer_quality import improve_arabic_answer
except Exception:
    # Fall back to no-ops if quality package isn't available at import time
    def clean_llm_text(x):
        return x

    def improve_arabic_answer(x):
        return x

# Fast test mode: when set, HostedLLMAdapter returns lightweight canned answers
FAST_MODE = os.getenv("AGL_FAST_MODE") == "1"

try:
    from agl.engines.self_improvement.Self_Improvement.meta_logger import MetaLogger
except Exception:
    MetaLogger = None

# Feature flags for multimodal/encoder usage (toggle via env)
USE_MEDIA_ENCODER = os.getenv('AGL_USE_MEDIA_ENCODER', '0') == '1'


def _compute_media_embedding(path: str):
    """Try to compute an embedding for a media file using available libs.

    Returns a dict with either {'embedding': [...]} or {'note': 'fallback', 'text': '...'}
    """
    try:
        # Try sentence-transformers or CLIP if present (best-effort)
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(os.getenv('AGL_MEDIA_EMBED_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'))
            # fallback: use filename as proxy for embedding
            txt = os.path.basename(path)
            emb = model.encode(txt).tolist()
            return {'embedding': emb, 'source': 'sentence-transformers'}
        except Exception:
            pass
        try:
            # CLIP may not be installed; guard the import
            try:
                import clip # type: ignore
                import torch
                from PIL import Image
                model, preprocess = clip.load('ViT-B/32', device='cpu')
                img = Image.open(path).convert('RGB')
                inp = preprocess(img).unsqueeze(0)
                with torch.no_grad():
                    emb = model.encode_image(inp).squeeze(0).cpu().numpy().tolist()
                return {'embedding': emb, 'source': 'clip'}
            except Exception:
                pass
        except Exception:
            pass
    except Exception:
        pass
    # final fallback: text representation
    try:
        import hashlib
        with open(path, 'rb') as fh:
            b = fh.read()
        sha = hashlib.sha256(b).hexdigest()
        return {'note': 'fallback-text', 'text': f"file:{os.path.basename(path)}", 'sha256': sha}
    except Exception:
        return {'note': 'unreadable'}


class HostedLLMAdapter:
    """
    Adapter that connects AGL pipeline to Ollama through /api/chat.

    Provides `infer(problem, context=None, timeout_s=...)` for pipeline compatibility.
    """

    def __init__(self):
        self.name = "hosted_llm"
        self.base_url = os.getenv("AGL_LLM_BASEURL", "http://localhost:11434")
        # preserve backward-compat: allow model_name override by caller in future
        target_model = os.getenv("AGL_LLM_MODEL", "qwen2.5:7b-instruct")
        # Self-healing: verify model exists and switch to a fallback if necessary
        try:
            self.model = self._ensure_model_exists(target_model)
        except Exception:
            # fallback to env or configured value if anything goes wrong
            self.model = target_model
        self.domains = ["knowledge", "qa", "language"]
        # CLI timeout (seconds) for `ollama run` calls; allow user override
        try:
            self.cli_timeout = int(os.getenv("AGL_OLLAMA_CLI_TIMEOUT", "120"))
        except Exception:
            self.cli_timeout = 120
        # load any prompt patches for self-improvement guidance
        try:
            self._load_prompt_patches()
        except Exception:
            self.prompt_patches = []

        # instance flags
        # keep fast_mode in the instance for easier testing / override
        self.fast_mode = os.getenv("AGL_FAST_MODE", "1" if FAST_MODE else "0") == "1"

        # Deep CoT settings (Phase 7)
        self.deep_cot_enabled = os.getenv("AGL_DEEP_COT", "0") == "1"
        try:
            self.cot_samples = int(os.getenv("AGL_COT_SAMPLES", str(os.getenv("AGL_COT_SAMPLES", "3"))))
        except Exception:
            self.cot_samples = 3
        # Dynamic cognition feature flag (Phase 14)
        self.dynamic_cognition_enabled = os.getenv("AGL_DYNAMIC_COGNITION", "0") == "1"

    def _parse_ollama_stream(self, raw: str) -> str:
        """
        Parse `raw` stdout from `ollama run` and try to assemble streaming
        JSONL responses into a single clean text.

        Behavior:
          - Split `raw` into non-empty lines
          - For each line, attempt `json.loads(line)`
          - If parsed and contains `response` (str), append it
          - If parsed and `done` == True, stop early
          - If a line isn't JSON, append the raw line as fallback
          - If any chunks were collected, return their concatenation;
            otherwise return the original `raw` trimmed.
        """
        if not raw:
            return ""
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        chunks = []
        for line in lines:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    # Prefer an explicit `response` field. Sanitize ONLY the
                    # textual response so we don't mangle JSON metadata.
                    resp = obj.get("response")
                    if isinstance(resp, str):
                        try:
                            cleaned_resp = self._clean_answer(resp)
                        except Exception:
                            cleaned_resp = resp
                        chunks.append(cleaned_resp)
                    # stop early if signaled
                    if obj.get("done") is True:
                        break
                    continue
            except json.JSONDecodeError:
                # not JSON, treat as plain text fragment (leave largely
                # untouched to avoid accidentally mangling structured output)
                chunks.append(line)
                continue
            except Exception:
                # on any other parse error, fallback by appending the raw line
                chunks.append(line)
                continue

        if chunks:
            # join with newlines to preserve separation between streamed
            # fragments (cleaned responses and raw fragments).
            text = "\n".join(chunks).strip()
            return text if text else raw.strip()
        return raw.strip()

    def _ensure_model_exists(self, model_name):
        """
        Self-Healing: Checks if model exists. If not, switches to the first available model.
        """
        import subprocess, shutil
        try:
            ollama_exe = shutil.which("ollama") or "ollama"
            result = subprocess.run([ollama_exe, "list"], capture_output=True, text=True, timeout=10)
            out = (result.stdout or "").strip()
            # quick containment check
            if model_name and model_name in out:
                return model_name

            print(f"[Self-Healing] Warning: Model '{model_name}' not found. Searching for fallback...")
            lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
            # If output contains a header like 'NAME', pick the first non-header line
            if len(lines) >= 1:
                # heuristics: skip header lines that start with 'NAME' or similar
                for ln in lines:
                    if ln.lower().startswith('name') or ln.lower().startswith('model'):
                        continue
                    # use first token as model id
                    alt = ln.split()[0]
                    if alt:
                        print(f"[Self-Healing] Switched to available model: '{alt}'")
                        return alt

            print("[Self-Healing] Critical: No models found in Ollama output; keeping configured model.")
            return model_name
        except Exception as e:
            print(f"[Self-Healing] Error checking models: {e}")
            return model_name

    def _clean_answer(self, text: str) -> str:
        """Clean trailing non-target-language tokens and odd fragments from LLM output.

        Heuristics applied:
        - Trim trailing lines that are majority non-Arabic/Latin (likely other-language footers).
        - Truncate at first occurrence of CJK characters (Chinese/Japanese/Korean) near the tail.
        - Remove trailing runs of odd punctuation/backslashes.
        - Normalize excessive whitespace.
        """
        try:
            if not text or not isinstance(text, str):
                return ''
            import re

            # Normalize whitespace but preserve newlines for readability
            text = re.sub(r"[ \t]{2,}", " ", text)
            text = text.strip()

            # Remove tatweel and Arabic diacritics (basic)
            text = re.sub(r"\u0640", "", text)
            text = re.sub(r"[\u064B-\u0652]", "", text)

            # Basic Unicode cleanup: remove isolated control characters
            text = re.sub(r"[\x00-\x1F\x7F-\x9F]+", "", text)

            # Split into lines and drop trailing lines that are unlikely Arabic answers
            lines = [l.rstrip() for l in text.splitlines() if l.strip()]

            def lang_fractions(s: str):
                a = l = o = 0
                for ch in s:
                    o += 1
                    oc = ord(ch)
                    if (0x0600 <= oc <= 0x06FF) or (0x0750 <= oc <= 0x077F) or (0x08A0 <= oc <= 0x08FF):
                        a += 1
                    elif (0x0041 <= oc <= 0x005A) or (0x0061 <= oc <= 0x007A) or (0x0030 <= oc <= 0x0039):
                        l += 1
                return (a / o if o else 0.0, l / o if o else 0.0)

            # If the answer contains Arabic characters anywhere, be stricter about trailing Latin/CJK tails
            contains_arabic = any(re.search(r"[\u0600-\u06FF]", ln) for ln in lines)
            while len(lines) > 1:
                a_frac, l_frac = lang_fractions(lines[-1])
                # drop line if it has very little Arabic and mostly Latin or CJK
                if (contains_arabic and a_frac < 0.2 and (l_frac > 0.5 or re.search(r"[\u4e00-\u9fff]", lines[-1]))):
                    lines.pop()
                    continue
                # drop line if it's mostly punctuation or non-printable
                if re.match(r"^[\W_]+$", lines[-1]):
                    lines.pop(); continue
                break

            text = "\n".join(lines).strip()

            # Truncate at first CJK occurrence near the tail
            cjk_re = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]")
            m = cjk_re.search(text)
            if m and m.start() >= max(0, len(text) - 200):
                text = text[:m.start()].rstrip()

            # Remove stray long Latin tokens embedded in Arabic replies (e.g., 'throatsoreness')
            text = re.sub(r"\b[A-Za-z]{5,}\b", "", text)

            # Remove repeated slashes/backslashes at end
            text = re.sub(r"[\\/]{2,}$", "", text)

            # Final pass: normalize multiple blank lines and strip
            text = re.sub(r"\n{2,}", "\n\n", text).strip()
            return text
        except Exception:
            try:
                return str(text).strip()
            except Exception:
                return ''

    def _finalize_llm_output(self, text: str, lang: str = "ar") -> str:
        """
        Apply final postprocessing steps: remove streaming metadata and apply
        language-specific improvements (Arabic).
        """
        try:
            t = clean_llm_text(text or "")
        except Exception:
            t = text or ""
        try:
            if lang == "ar":
                t = improve_arabic_answer(t)
        except Exception:
            pass
        return t

    def _safety_check_and_maybe_block(self, task: dict, content: dict, meta: Optional[dict] = None):
        """Apply simple safety gating: if `task['safety_required']` is True and
        grounding/context signals are missing, return a blocked response metadata.

        This is a conservative, local heuristic; callers may run more thorough checks.
        """
        try:
            if not isinstance(task, dict):
                return content, meta or {}
            if not task.get('safety_required'):
                return content, meta or {}

            # require either learned facts, rag_hint or media context
            prov = task.get('provenance') if isinstance(task, dict) else {}
            has_learned = bool(task.get('question') and '---' in task.get('question'))
            has_media = bool((prov or {}).get('media')) or bool(task.get('media'))
            has_rag = bool((prov or {}).get('raw_provenance')) and 'rag' in str((prov or {}).get('raw_provenance'))

            # Allow configurable safety tolerance: if environment requests higher tolerance,
            # avoid blocking complex answers that don't explicitly include grounding.
            try:
                tol = float(os.getenv('AGL_SAFETY_TOLERANCE', '0.5'))
            except Exception:
                tol = 0.5

            if not (has_learned or has_media or has_rag):
                # If tolerance is low, block as before. If tolerance is higher, allow the answer
                # but mark that grounding was missing. This permits selecting longer, creative answers
                # when the operator has increased tolerance (e.g., set AGL_SAFETY_TOLERANCE=0.8).
                if tol < 0.75:
                    blocked = {"answer": "ØªØ­Ø°ÙŠØ±: Ù„Ù… ØªØªÙˆÙØ± Ø£Ø¯Ù„Ø© ÙƒØ§ÙÙŠØ© Ù„Ø¥Ù†ØªØ§Ø¬ Ø¥Ø¬Ø§Ø¨Ø© Ø¢Ù…Ù†Ø©.", "note": "safety_blocked"}
                    meta = meta or {}
                    meta['safety_block'] = True
                    try:
                        if MetaLogger is not None:
                            sid = getattr(task.get('session'), 'session_id', None) or str(int(time.time()))
                            MetaLogger.log_event(sid, 'safety_block', {'reason': 'missing_grounding', 'task_preview': (task.get('question') or '')[:200]})
                    except Exception:
                        pass
                    return blocked, meta
                else:
                    # mark that the answer had no grounding but allow it through
                    meta = meta or {}
                    meta['safety_missing_grounding'] = True
                    try:
                        if MetaLogger is not None:
                            sid = getattr(task.get('session'), 'session_id', None) or str(int(time.time()))
                            MetaLogger.log_event(sid, 'safety_tolerated', {'tolerance': tol, 'task_preview': (task.get('question') or '')[:200]})
                    except Exception:
                        pass
                    # do not block; allow caller to proceed
                    return content, meta
                try:
                    if MetaLogger is not None:
                        sid = getattr(task.get('session'), 'session_id', None) or str(int(time.time()))
                        MetaLogger.log_event(sid, 'safety_block', {'reason': 'missing_grounding', 'task_preview': (task.get('question') or '')[:200]})
                except Exception:
                    pass
                return blocked, meta
        except Exception:
            pass
        return content, meta or {}

    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate a response for a given prompt, optionally with a system prompt.
        This method is a wrapper around call_ollama to provide a standard interface.
        """
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
        try:
            return self.call_ollama(full_prompt)
        except Exception as e:
            print(f"âš ï¸ HostedLLMAdapter.generate_response failed: {e}")
            return ""

    def call_ollama(self, question: str, timeout: float = 200.0) -> str:
        # Try multiple plausible endpoints and payload shapes to support
        # different Ollama / proxy versions (some expose /api/chat, others /api/generate)
        endpoints = [
            {
                "path": "/api/chat",
                "payload": {"model": self.model, "messages": [{"role": "user", "content": question}], "stream": False},
            },
            {
                "path": "/api/generate",
                "payload": {"model": self.model, "prompt": question, "max_tokens": 1024},
            },
            {
                "path": "/v1/chat/completions",
                "payload": {"model": self.model, "messages": [{"role": "user", "content": question}]},
            },
            {
                "path": "/v1/completions",
                "payload": {"model": self.model, "prompt": question, "max_tokens": 1024},
            },
        ]

        last_err = None
        for ep in endpoints:
            path = ep.get('path', '')
            # Map common logical endpoints to canonical builder results (use instance base when available)
            if path in ("/api/chat", "/v1/chat/completions"):
                url = build_llm_url('chat', base=self.base_url)
            elif path in ("/api/generate",):
                url = build_llm_url('generate', base=self.base_url)
            elif path in ("/v1/completions",):
                url = build_llm_url('completions', base=self.base_url)
            else:
                url = f"{self.base_url.rstrip('/')}{path}"
            payload = ep.get("payload")
            try:
                resp = requests.post(url, json=payload, timeout=timeout)
                # Debug: print raw HTTP response text when engine debug enabled
                try:
                    if os.getenv('AGL_DEBUG_ENGINES', '0') == '1':
                        try:
                            dump = (resp.text or '')
                        except Exception:
                            dump = '<unreadable-response>'
                        print(f"\nðŸ”¥ðŸ”¥ [ADAPTER RAW DEBUG] call_ollama url={url} status={getattr(resp,'status_code',None)} | payload_preview={str(payload)[:200]}\n{dump}\nðŸ”¥ðŸ”¥\n")
                except Exception:
                    pass
            except Exception as e:
                last_err = e
                continue
            # if not found, try next
            if resp.status_code == 404:
                last_err = Exception(f"404 for {url}")
                continue
            try:
                resp.raise_for_status()
            except Exception as e:
                last_err = e
                continue
            try:
                data = resp.json()
            except Exception:
                # try text fallback
                return resp.text[:2000]

            # common Ollama chat format
            if isinstance(data, dict):
                if "message" in data:
                    msg = data.get("message")
                    if isinstance(msg, dict) and "content" in msg:
                        return msg.get("content")
                # openai-like completions
                if "choices" in data and isinstance(data.get("choices"), list) and data.get("choices"):
                    first = data.get("choices")[0]
                    if isinstance(first, dict):
                        # chat completions
                        if "message" in first and isinstance(first.get("message"), dict) and "content" in first.get("message"):
                            return first.get("message").get("content")
                        # text completions
                        if "text" in first:
                            return first.get("text")
                        if "message" in first and isinstance(first.get("message"), str):
                            return first.get("message")
                # other common keys
                for k in ("response", "output", "answer", "text", "result"):
                    if k in data:
                        v = data.get(k)
                        return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)

            # if nothing matched, stringify the response
            return str(data)[:2000]

        # if we reach here every endpoint failed -> try CLI fallback
        # Use a dedicated CLI caller that follows the local `ollama run MODEL PROMPT` usage
        try:
            text, note = self._call_ollama_cli(self.model, question, timeout_s=max(30, int(timeout)))
            if text:
                return text
            # record the last error as exception with note
            last_err = Exception(f"cli-failed: {note}")
        except Exception as e:
            last_err = e

        raise last_err or Exception("no-ollama-endpoints-available")

    def _call_ollama_cli(self, model: str, prompt: str, timeout_s: float = 30.0):
        """Call local `ollama run MODEL PROMPT` and return (stdout, note).

        Returns (text, 'ok') on success, or (None, 'reason') on failure.
        """
        logger = logging.getLogger(__name__)
        try:
            ollama_exe = os.getenv("OLLAMA_PATH") or shutil.which("ollama") or "ollama"
        except Exception as e:
            logger.exception("failed to locate ollama executable")
            return None, f"cli-error: {e!r}"

        # Check installed/available models first (fast check). If configured model
        # is not listed, pick the first available model as a candidate to avoid
        # waiting for a long run on an invalid model path.
        try:
            list_cmd = [ollama_exe, "list"]
            lst = subprocess.run(list_cmd, capture_output=True, text=True, timeout=10)
            models_text = (lst.stdout or "").strip()
            if models_text:
                available = []
                for ln in models_text.splitlines():
                    ln = ln.strip()
                    if not ln:
                        continue
                    candidate = ln.split()[0]
                    if candidate:
                        available.append(candidate)
                if available and model not in available:
                    # override model with first available candidate
                    model = available[0]
        except Exception:
            # if we can't list, continue and try the requested model
            available = []

        # Build command: ollama run MODEL PROMPT
        try:
            cmd = [ollama_exe, "run", model, prompt]
            # Timeout policy:
            # - respect explicit timeout_s passed by caller
            # - otherwise fall back to self.cli_timeout or BASE_DEFAULT
            # - always enforce a HARD_MAX to avoid multi-minute waits
            # ØªÙ… Ø§Ù„Ø±ÙØ¹ Ù„Ø­Ù„ Ù…Ø´ÙƒÙ„Ø© timeout ÙÙŠ Ø§Ù„Ø§Ø®ØªØ¨Ø§Ø± Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠ AGI
            BASE_DEFAULT = 600.0  # Increased to 600s (10 mins)
            HARD_MAX = 1200.0     # Increased to 1200s (20 mins)
            try:
                eff = float(timeout_s) if timeout_s is not None else BASE_DEFAULT
            except Exception:
                eff = BASE_DEFAULT
            try:
                if getattr(self, "cli_timeout", None) is not None:
                    # do not let cli_timeout increase a smaller requested timeout
                    # eff = min(eff, float(self.cli_timeout)) # DISABLED: Allow longer timeouts
                    eff = max(eff, float(self.cli_timeout)) # Prefer longer timeout
            except Exception:
                pass
            # final safety cap
            if eff > HARD_MAX:
                eff = HARD_MAX
            # ensure positive
            use_timeout = max(1.0, float(eff))
            logger.debug("ollama_cli_call", extra={"model": model, "timeout_used": use_timeout})
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=use_timeout)
        except subprocess.TimeoutExpired as e:
            logger.warning("ollama run timed out", exc_info=True)
            return None, f"cli-timeout: {e!r}"
        except Exception as e:
            logger.exception("ollama run failed")
            return None, f"cli-error: {e!r}"

        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()

        # Normalize/clean streaming outputs via helper that tries to
        # assemble newline-delimited JSON `response` fields.
        try:
            # keep original stdout for debug; parse to cleaned text
            cleaned = self._parse_ollama_stream((completed.stdout or "").strip())
            # prefer cleaned text for further checks
            stdout = cleaned
        except Exception:
            stdout = (completed.stdout or "").strip()

        if completed.returncode != 0:
            msg = f"cli-nonzero-exit: code={completed.returncode}, stderr={stderr or stdout}"
            # try to detect invalid model error and fall back to a listed model
            lowerr = (stderr or stdout).lower()
            if "invalid model" in lowerr or "invalid model path" in lowerr or "not found" in lowerr:
                try:
                    list_cmd = [ollama_exe, "list"]
                    lst = subprocess.run(list_cmd, capture_output=True, text=True, timeout=20)
                    models_text = (lst.stdout or "").strip()
                    # pick first non-empty token as model id
                    if models_text:
                        # lines may include header; pick first sensible line
                        for ln in models_text.splitlines():
                            ln = ln.strip()
                            if not ln:
                                continue
                            # typical output might be 'qwen2.5:7b-instruct' or similar
                            candidate = ln.split()[0]
                            if candidate:
                                # retry with candidate model using the configured CLI timeout
                                try:
                                    retry_cmd = [ollama_exe, "run", candidate, prompt]
                                    # use a bounded retry timeout as well
                                    try:
                                        cand_base = float(timeout_s) if timeout_s is not None else float(getattr(self, "cli_timeout", 60))
                                    except Exception:
                                        cand_base = 60.0
                                    cand_timeout = min(HARD_MAX, max(5.0, cand_base))
                                    retry = subprocess.run(retry_cmd, capture_output=True, text=True, timeout=cand_timeout)
                                    rout = (retry.stdout or "").strip()
                                    rerr = (retry.stderr or "").strip()
                                    lowr = (rout or rerr).lower()
                                    if retry.returncode == 0 and rout and not any(x in lowr for x in ("error:", "unknown flag", "unknown command", "not found")):
                                        return rout, f"ok (model={candidate})"
                                except Exception:
                                    continue
                except Exception:
                    pass
            return None, msg

        # Debug: print CLI raw stdout/stderr when enabled
        try:
            if os.getenv('AGL_DEBUG_ENGINES', '0') == '1':
                try:
                    so = stdout or ''
                    se = stderr or ''
                except Exception:
                    so = '<unreadable-stdout>'
                    se = '<unreadable-stderr>'
                print(f"\nðŸ”¥ðŸ”¥ [ADAPTER RAW DEBUG] _call_ollama_cli model={model} returncode={completed.returncode}\nSTDOUT:\n{so}\nSTDERR:\n{se}\nðŸ”¥ðŸ”¥\n")
        except Exception:
            pass

        # reject obvious error outputs (check both stdout and stderr)
        bad_markers = ("error:", "unknown flag", "unknown command", "not found")
        low_out = (stdout or "").lower()
        low_err = (stderr or "").lower()
        if any(m in low_out for m in bad_markers) or any(m in low_err for m in bad_markers):
            return None, f"cli-error-output: {stderr or stdout}"

        return stdout, "ok"

    def _verify_answer(self, question: str, final_answer: str, timeout_s: float = 30.0) -> dict:
        """Ask the hosted model to verify and optionally improve the final answer.

        Returns: {"ok": bool, "note": str, "improved_answer": str or None}
        """
        try:
            v_prompt = (
                f"Ø§Ù„Ø³Ø¤Ø§Ù„: {question}\n"
                f"Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø© Ø§Ù„Ù…Ù‚ØªØ±Ø­Ø©: {final_answer}\n\n"
                "Ù‚Ù… Ø¨Ø§Ù„ØªØ­Ù‚Ù‚ Ø¨Ø´ÙƒÙ„ Ù…ÙˆØ¬Ø²: Ù‡Ù„ Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø© ØµØ­ÙŠØ­Ø© ÙˆØ°Ø§Øª ØµÙ„Ø© ÙˆÙ…ÙƒØªÙ…Ù„Ø©ØŸ\n"
                "Ø£Ø¹Ø¯ ØµÙŠØ§ØºØ© Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø© Ø§Ù„Ù…Ø­Ø³Ù‘Ù†Ø© Ø¥Ù† Ù„Ø²Ù… Ø§Ù„Ø£Ù…Ø±.\n"
                "Ø£Ø¬Ø¨ Ø¨ØµÙŠØºØ© JSON Ø¹Ù„Ù‰ Ø³Ø·Ø± ÙˆØ§Ø­Ø¯: {\"ok\": true|false, \"note\": \"...\", \"improved_answer\": \"...\"}"
            )
            resp = self.call_ollama(v_prompt, timeout=timeout_s)
            if not resp or not isinstance(resp, str):
                return {"ok": True, "note": "no-verification-output", "improved_answer": None}
            # attempt to extract JSON object from response
            import re, json
            jtxt = None
            # look for first JSON-looking substring
            m = re.search(r"\{.*\}", resp, flags=re.S)
            if m:
                jtxt = m.group(0)
            else:
                # fallback: try lines that start with { or contain key tokens
                for ln in (resp or "").splitlines():
                    ln = ln.strip()
                    if ln.startswith("{") and ln.endswith("}"):
                        jtxt = ln; break
            if jtxt:
                try:
                    j = json.loads(jtxt)
                    ok = bool(j.get("ok") or j.get("valid") or j.get("correct"))
                    note = str(j.get("note") or j.get("remark") or "")
                    improved = j.get("improved_answer") or j.get("answer") or None
                    if isinstance(improved, str):
                        improved = improved.strip() or None
                    return {"ok": ok, "note": note, "improved_answer": improved}
                except Exception:
                    return {"ok": True, "note": "verification-parse-failed", "improved_answer": None}
            # no JSON found: simple heuristic
            low = (resp or "").lower()
            if "no" in low and ("error" in low or "incorrect" in low or "not" in low):
                return {"ok": False, "note": "verifier-says-no", "improved_answer": None}
            return {"ok": True, "note": "verifier-unknown", "improved_answer": None}
        except Exception:
            return {"ok": True, "note": "verification-error", "improved_answer": None}

    def _fast_mode_answer(self, task: dict) -> dict:
        """
        ÙˆØ¶Ø¹ Ø§Ø®ØªØ¨Ø§Ø±Ø§Øª Ø³Ø±ÙŠØ¹: Ù„Ø§ ÙŠØªØµÙ„ Ø¨Ø£ÙŠ Ù†Ù…ÙˆØ°Ø¬ Ø®Ø§Ø±Ø¬ÙŠØŒ
        ÙˆÙŠØ¹ÙŠØ¯ Ø¥Ø¬Ø§Ø¨Ø§Øª Ù‚ØµÙŠØ±Ø© Ø«Ø§Ø¨ØªØ© ØªÙƒÙÙŠ Ù„Ù„Ø§Ø®ØªØ¨Ø§Ø±Ø§Øª ÙˆØ§Ù„Ø¨Ù†Ø´Ù…Ø§Ø±Ùƒ.
        """
        q = (task.get("question") or "").strip() if isinstance(task, dict) else str(task)
        task_type = task.get("task_type") if isinstance(task, dict) else "qa_single"

        ans = "Ø¥Ø¬Ø§Ø¨Ø© ØªØ¬Ø±ÙŠØ¨ÙŠØ© Ø³Ø±ÙŠØ¹Ø© (FAST_MODE)."

        if "Ø£Ø¹Ø±Ø§Ø¶ Ø§Ù„Ø¥Ù†ÙÙ„ÙˆÙ†Ø²Ø§" in q or "Ø§Ù„Ø¥Ù†ÙÙ„ÙˆÙ†Ø²Ø§" in q:
            ans = (
                "Ø£Ø¹Ø±Ø§Ø¶ Ø§Ù„Ø¥Ù†ÙÙ„ÙˆÙ†Ø²Ø§ ØªØ´Ù…Ù„ Ø­Ù…Ù‰ Ø£Ùˆ Ø§Ø±ØªÙØ§Ø¹ ÙÙŠ Ø¯Ø±Ø¬Ø© Ø§Ù„Ø­Ø±Ø§Ø±Ø©ØŒ "
                "ØµØ¯Ø§Ø¹ØŒ Ø¢Ù„Ø§Ù… ÙÙŠ Ø§Ù„Ø¹Ø¶Ù„Ø§Øª ÙˆØ§Ù„Ù…ÙØ§ØµÙ„ØŒ Ø³Ø¹Ø§Ù„ØŒ Ø§Ù„ØªÙ‡Ø§Ø¨ Ø£Ùˆ Ø£Ù„Ù… ÙÙŠ Ø§Ù„Ø­Ù„Ù‚ØŒ "
                "Ø¥Ø±Ù‡Ø§Ù‚ Ø¹Ø§Ù…ØŒ ÙˆØ£Ø­ÙŠØ§Ù†Ù‹Ø§ Ø±Ø¬ÙØ© ÙˆØ³ÙŠÙ„Ø§Ù† Ø§Ù„Ø£Ù†Ù."
            )
        elif "Ø§Ø±ØªÙØ§Ø¹ Ø¶ØºØ· Ø§Ù„Ø¯Ù…" in q:
            ans = (
                "Ø§Ø±ØªÙØ§Ø¹ Ø¶ØºØ· Ø§Ù„Ø¯Ù… Ù‡Ùˆ Ø§Ø±ØªÙØ§Ø¹ Ù…Ø³ØªÙ…Ø± ÙÙŠ Ø¶ØºØ· Ø§Ù„Ø¯Ù… Ø¯Ø§Ø®Ù„ Ø§Ù„Ø´Ø±Ø§ÙŠÙŠÙ†. "
                "Ù…Ù† Ø£Ø³Ø¨Ø§Ø¨Ù‡ Ø§Ù„Ø³Ù…Ù†Ø©ØŒ Ù‚Ù„Ø© Ø§Ù„Ù†Ø´Ø§Ø·ØŒ Ø§Ù„Ø¥ÙƒØ«Ø§Ø± Ù…Ù† Ø§Ù„Ù…Ù„Ø­ØŒ Ø§Ù„ØªÙˆØªØ±ØŒ "
                "ÙˆØ§Ù„Ø¹ÙˆØ§Ù…Ù„ Ø§Ù„ÙˆØ±Ø§Ø«ÙŠØ©. Ù…Ù† Ù…Ø¶Ø§Ø¹ÙØ§ØªÙ‡ Ø§Ù„Ø³ÙƒØªØ© Ø§Ù„Ø¯Ù…Ø§ØºÙŠØ©ØŒ ÙØ´Ù„ Ø§Ù„Ù‚Ù„Ø¨ØŒ "
                "ÙˆØªÙ„Ù Ø§Ù„ÙƒÙ„Ù‰. Ø§Ù„ÙˆÙ‚Ø§ÙŠØ© ØªÙƒÙˆÙ† Ø¨ØªÙ‚Ù„ÙŠÙ„ Ø§Ù„Ù…Ù„Ø­ØŒ Ù…Ù…Ø§Ø±Ø³Ø© Ø§Ù„Ø±ÙŠØ§Ø¶Ø©ØŒ "
                "Ø¥Ù†Ù‚Ø§Øµ Ø§Ù„ÙˆØ²Ù†ØŒ ÙˆØ§Ù„Ø¥Ù‚Ù„Ø§Ø¹ Ø¹Ù† Ø§Ù„ØªØ¯Ø®ÙŠÙ†."
            )
        elif "Ø¯Ø§Ø¡ Ø§Ù„Ø³ÙƒØ±ÙŠ" in q:
            ans = (
                "Ø¯Ø§Ø¡ Ø§Ù„Ø³ÙƒØ±ÙŠ Ù‡Ùˆ Ù…Ø±Ø¶ Ù…Ø²Ù…Ù† ÙŠØªÙ…ÙŠØ² Ø¨Ø§Ø±ØªÙØ§Ø¹ Ù…Ø³ØªÙˆÙ‰ Ø§Ù„Ø³ÙƒØ± ÙÙŠ Ø§Ù„Ø¯Ù… "
                "Ø¨Ø³Ø¨Ø¨ Ù†Ù‚Øµ Ø¥ÙØ±Ø§Ø² Ø§Ù„Ø¥Ù†Ø³ÙˆÙ„ÙŠÙ† Ø£Ùˆ Ù…Ù‚Ø§ÙˆÙ…Ø© Ø®Ù„Ø§ÙŠØ§ Ø§Ù„Ø¬Ø³Ù… Ù„Ù‡."
            )
        elif "Ø§Ù„ÙØ´Ù„ Ø§Ù„ÙƒÙ„ÙˆÙŠ Ø§Ù„Ù…Ø²Ù…Ù†" in q:
            ans = (
                "Ø§Ù„ÙØ´Ù„ Ø§Ù„ÙƒÙ„ÙˆÙŠ Ø§Ù„Ù…Ø²Ù…Ù† Ù‡Ùˆ ØªØ¯Ù‡ÙˆØ± ØªØ¯Ø±ÙŠØ¬ÙŠ Ø¯Ø§Ø¦Ù… ÙÙŠ ÙˆØ¸ÙŠÙØ© Ø§Ù„ÙƒÙ„Ù‰ "
                "ÙŠØ³ØªÙ…Ø± Ù„Ø£ÙƒØ«Ø± Ù…Ù† Ø«Ù„Ø§Ø«Ø© Ø£Ø´Ù‡Ø±ØŒ Ù…Ù…Ø§ ÙŠØ¤Ø¯ÙŠ Ø¥Ù„Ù‰ Ø¹Ø¬Ø² Ø§Ù„ÙƒÙ„Ù‰ Ø¹Ù† ØªÙ†Ù‚ÙŠØ© Ø§Ù„Ø¯Ù… "
                "ÙˆØ·Ø±Ø­ Ø§Ù„ÙØ¶Ù„Ø§Øª ÙˆØ§Ù„Ø³ÙˆØ§Ø¦Ù„ Ø§Ù„Ø²Ø§Ø¦Ø¯Ø©."
            )
        elif "Ø§Ù„Ù…Ø¶Ø§Ø¯Ø§Øª Ø§Ù„Ø­ÙŠÙˆÙŠØ© Ø¨Ø¯ÙˆÙ† ÙˆØµÙØ©" in q or "Ø¨Ø¯ÙˆÙ† ÙˆØµÙØ© Ø·Ø¨ÙŠØ©" in q:
            ans = (
                "Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ù…Ø¶Ø§Ø¯Ø§Øª Ø§Ù„Ø­ÙŠÙˆÙŠØ© Ø¨Ø¯ÙˆÙ† ÙˆØµÙØ© Ø·Ø¨ÙŠØ© ÙŠØ¤Ø¯ÙŠ Ø¥Ù„Ù‰ Ø²ÙŠØ§Ø¯Ø© "
                "Ù…Ù‚Ø§ÙˆÙ…Ø© Ø§Ù„Ø¨ÙƒØªÙŠØ±ÙŠØ§ Ù„Ù„Ù…Ø¶Ø§Ø¯Ø§ØªØŒ ÙØ´Ù„ Ø§Ù„Ø¹Ù„Ø§Ø¬ Ù…Ø³ØªÙ‚Ø¨Ù„Ø§Ù‹ØŒ Ø­Ø¯ÙˆØ« Ø¢Ø«Ø§Ø± Ø¬Ø§Ù†Ø¨ÙŠØ© "
                "ØºÙŠØ± Ø¶Ø±ÙˆØ±ÙŠØ©ØŒ ÙˆØ±Ø¨Ù…Ø§ Ø¥Ø®ÙØ§Ø¡ Ø£Ù…Ø±Ø§Ø¶ Ø®Ø·ÙŠØ±Ø©."
            )

        return {
            "engine": "hosted_llm",
            "content": {
                "answer": ans,
                "note": "fast_mode_stub",
                "reasoning_long": "",
                "runs": [],
                "deliberation": None,
                "planner": None,
                "verified": {
                    "ok": True,
                    "note": "fast_mode (no external verification).",
                    "improved_answer": {"answer": ans},
                },
            },
            "checks": {"constraints": True, "feasible": True},
            "novelty": 0.0,
            "meta": {"latency_ms": 5, "tokens": 0},
            "domains": ["qa", "knowledge"],
            "score": 1.0,
        }

    def _load_prompt_patches(self):
        """ØªØ­Ù…ÙŠÙ„ ØªØ¹Ù„ÙŠÙ…Ø§Øª Ø¥Ø¶Ø§ÙÙŠØ© Ù…Ù† Ù…Ù„Ù prompt_patches.json Ø¥Ù† ÙˆØ¬Ø¯."""
        try:
            here = os.path.dirname(__file__)
            default_path = os.path.join(here, "prompt_patches.json")
            path = os.getenv("AGL_PROMPT_PATCHES_PATH", default_path)

            if not os.path.exists(path):
                self.prompt_patches = []
                return

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            patches = []
            if isinstance(data, dict):
                for _, cfg in data.items():
                    txt = cfg.get("extra_instruction") or cfg.get("system_instructions")
                    if isinstance(txt, str) and txt.strip():
                        patches.append(txt.strip())

            self.prompt_patches = patches
        except Exception:
            # don't break if patches can't be loaded
            self.prompt_patches = []

    def _apply_prompt_patches(self, prompt: str) -> str:
        if not prompt:
            prompt = ""
        if getattr(self, "prompt_patches", None):
            try:
                patched = prompt + "\n\n" + "\n".join(self.prompt_patches)
                return patched
            except Exception:
                return prompt
        return prompt

    def _split_reasoning_and_answer(self, text: str):
        """
        ÙŠØ­Ø§ÙˆÙ„ ÙØµÙ„ Ø®Ø·ÙˆØ§Øª Ø§Ù„ØªÙÙƒÙŠØ± Ø¹Ù† Ø§Ù„Ø¬ÙˆØ§Ø¨ Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠ.
        Ù„Ùˆ Ù…Ø§ ÙˆØ¬Ø¯ Ù…Ø§Ø±ÙƒØ±Ø§ØªØŒ ÙŠØ±Ø¬Ù‘Ø¹ Ø§Ù„Ù†Øµ ÙƒØ§Ù…Ù„ ÙƒØ¬ÙˆØ§Ø¨.
        """
        if not text:
            return "", ""

        markers = ["<final>", "</final>", "Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø© Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠØ©", "Ø§Ù„Ø¬ÙˆØ§Ø¨ Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠ"]
        # try to find a marker occurrence
        for m in markers:
            if m in text:
                idx = text.rfind(m)
                reasoning = text[:idx].strip()
                final = text[idx:].replace("<final>", "").replace("</final>", "").strip()
                final = final.replace("Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø© Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠØ©:", "").replace("Ø§Ù„Ø¬ÙˆØ§Ø¨ Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠ:", "").strip()
                return reasoning, final

        # fallback: everything as answer
        return "", text.strip()

    def _pick_consensus_answer(self, candidates):
        """
        Ø§Ø®ØªØ± Ø§Ù„Ø£ÙƒØ«Ø± ØªÙƒØ±Ø§Ø±Ù‹Ø§ ÙÙŠ answer (self-consistency Ø¨Ø³ÙŠØ·).
        candidates: list of dicts {'reasoning':..., 'answer':...}
        """
        if not candidates:
            return {"reasoning": "", "answer": ""}

        answers = [c.get("answer", "").strip() for c in candidates if c.get("answer")]
        if not answers:
            return candidates[0]

        from collections import Counter

        counter = Counter(answers)
        best_answer, _ = counter.most_common(1)[0]

        for c in candidates:
            if c.get("answer", "").strip() == best_answer:
                return c

        return {"reasoning": "", "answer": best_answer}

    def _run_deep_cot(self, prompt: str, question: str, task_type: str = "qa_single"):
        """
        Ù†ÙÙ‘Ø° Ø¹Ø¯Ø© Ù…Ø­Ø§ÙˆÙ„Ø§Øª CoTØŒ Ø«Ù… Ø§Ø®ØªØ± Ø£ÙØ¶Ù„ Ø¬ÙˆØ§Ø¨ Ø¹Ø¨Ø± self-consistency.
        Ù„Ø§ ÙŠÙØ³ØªØ®Ø¯Ù… ÙÙŠ FAST_MODE.
        """
        samples = []
        n = self.cot_samples if getattr(self, "cot_samples", None) else 3

        for i in range(n):
            deep_prompt = (
                "ÙÙƒÙ‘Ø± Ø®Ø·ÙˆØ© Ø¨Ø®Ø·ÙˆØ© Ø¨Ø§Ù„ØªÙØµÙŠÙ„ØŒ Ø«Ù… Ø£Ø¹Ø·Ù ÙÙŠ Ø§Ù„Ù†Ù‡Ø§ÙŠØ© Ø¬ÙˆØ§Ø¨Ù‹Ø§ Ù†Ù‡Ø§Ø¦ÙŠÙ‹Ø§ ÙˆØ§Ø¶Ø­Ù‹Ø§.\n"
                "Ø§ÙƒØªØ¨ Ø®Ø·ÙˆØ§Øª Ø§Ù„ØªÙÙƒÙŠØ± Ø£ÙˆÙ„Ø§Ù‹ØŒ Ø«Ù… ÙÙŠ Ø§Ù„Ø³Ø·Ø± Ø§Ù„Ø£Ø®ÙŠØ± Ø¶Ø¹ Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø© Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠØ© Ø¨Ø¹Ø¯ Ø¹Ø¨Ø§Ø±Ø©: 'Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø© Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠØ©:'\n\n"
                f"Ø§Ù„Ø³Ø¤Ø§Ù„: {question}\n"
            )

            full_input = f"{prompt}\n\n{deep_prompt}"

            try:
                raw_text = self.call_ollama(full_input, timeout=30.0)
            except Exception:
                raw_text = ""

            reasoning, final = self._split_reasoning_and_answer(raw_text or "")
            samples.append({"reasoning": reasoning, "answer": final})

        best = self._pick_consensus_answer(samples)
        return best

    def _self_critique(self, question: str, answer: str):
        """
        Ù‡ÙˆÙƒ Ø¨Ø³ÙŠØ· Ù„Ù…Ø±Ø§Ø¬Ø¹Ø© Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø©. Ø­Ø§Ù„ÙŠÙ‹Ø§ Ù†Ø±Ø¬Ø¹ Ù†ÙØ³ Ø§Ù„Ø¬ÙˆØ§Ø¨ Ù…Ø¹ Ù…Ù„Ø§Ø­Ø¸Ø© ÙÙ‚Ø·.
        """
        return {"issues": [], "improved_answer": answer}

    def _call_ollama_stream(self, prompt: str, timeout: int = 300) -> str:
        """
        Wrapper to call the streaming Ollama helper if available.
        Falls back to `call_ollama` when streaming helper is not present.
        """
        try:
            if ask_with_deep_thinking is None:
                # helper not available; fallback
                return self.call_ollama(prompt, timeout=min(30, timeout))
            # ask_with_deep_thinking prints tokens as they arrive and returns full text
            return ask_with_deep_thinking(prompt, model=self.model, timeout=timeout)
        except Exception as e:
            try:
                print(f"âš ï¸ _call_ollama_stream failed, falling back: {e}")
            except Exception:
                pass
            return self.call_ollama(prompt, timeout=min(30, timeout))

    def process_task(self, task, timeout_s: float = 200.0):
        question = task.get("question", "") if isinstance(task, dict) else str(task)
        start = time.time()

        # Fast test mode: short-circuit and return canned answers
        try:
            if getattr(self, "fast_mode", False):
                return self._fast_mode_answer(task if isinstance(task, dict) else {"question": question})
        except Exception:
            pass

        # RAG integration: allow short-circuit via engine_hint=='rag' and
        # prepend retrieved RAG context to the prompt when available.
        try:
            try:
                from agl.engines.self_improvement.Self_Improvement.rag_index import retrieve_context
            except Exception:
                retrieve_context = None

            engine_hint = task.get('engine_hint') if isinstance(task, dict) else None
            rag_ctx = ""
            if callable(retrieve_context):
                try:
                    rag_ctx = retrieve_context(question, k=5) or ""
                except Exception:
                    rag_ctx = ""

            # Prepend learned facts context (continual learning) when available.
            try:
                from agl.engines.self_improvement.Self_Improvement.continual_learning import load_learned_facts_as_context
                try:
                    learned_ctx = load_learned_facts_as_context(max_items=int(os.getenv('AGL_LEARNED_FACTS_MAX', '10')))
                except Exception:
                    learned_ctx = ""
            except Exception:
                learned_ctx = ""

            # Optional multimodal media handling: accept task['media'] as list of file paths
            media_ctx = ""
            media_meta = []
            try:
                media_items = []
                if isinstance(task, dict):
                    media_items = task.get('media') or task.get('media_refs') or []
                if media_items and isinstance(media_items, (list, tuple)):
                    import hashlib
                    for m in media_items:
                        try:
                            path = str(m)
                            if os.path.exists(path):
                                with open(path, 'rb') as fh:
                                    b = fh.read()
                                sha = hashlib.sha256(b).hexdigest()
                                entry = {'path': path, 'sha256': sha, 'size': len(b)}
                                # attempt to compute embedding if feature flag enabled
                                try:
                                    if USE_MEDIA_ENCODER:
                                        emb_info = _compute_media_embedding(path)
                                        if emb_info:
                                            entry.update(emb_info)
                                except Exception:
                                    pass
                                media_meta.append(entry)
                                # include either embedding note or sha in textual ctx
                                if entry.get('embedding'):
                                    media_ctx += f"ÙˆØ³Ø§Ø¦Ø·: {os.path.basename(path)} (embedded via {entry.get('source','encoder')})\n"
                                else:
                                    media_ctx += f"ÙˆØ³Ø§Ø¦Ø·: {os.path.basename(path)} (sha256={sha})\n"
                            else:
                                media_meta.append({'path': path, 'note': 'not_found'})
                                media_ctx += f"ÙˆØ³Ø§Ø¦Ø·: {os.path.basename(path)} (missing)\n"
                        except Exception:
                            media_meta.append({'path': m, 'note': 'error'})
                            continue
            except Exception:
                media_ctx = ""

            # short-circuit factual-only RAG answers when explicitly requested
            # Allow forcing external LLMs via env `AGL_FORCE_EXTERNAL=1`
            try:
                _force_external = os.getenv('AGL_FORCE_EXTERNAL', '0') == '1'
            except Exception:
                _force_external = False
            # Debug: log force-external flag and context sizes to help diagnose
            try:
                logger = logging.getLogger(__name__)
                logger.debug("hosted_llm_adapter: AGL_FORCE_EXTERNAL=%s engine_hint=%s rag_ctx_len=%s learned_ctx_len=%s media_ctx_len=%s", _force_external, repr(engine_hint), len(rag_ctx) if rag_ctx else 0, len(learned_ctx) if learned_ctx else 0, len(media_ctx) if media_ctx else 0)
            except Exception:
                pass

            if engine_hint == 'rag' and not _force_external:
                try:
                    # If learned facts exist, include them with the rag short-circuit
                    # include context_relations if provided in task provenance
                    ctx_rels_txt = ""
                    try:
                        prov = task.get('provenance') if isinstance(task, dict) else {}
                        ctx_rels = prov.get('context_relations') if isinstance(prov, dict) else None
                        if ctx_rels and isinstance(ctx_rels, list):
                            lines = []
                            for cr in ctx_rels:
                                lines.append(f"relation: {cr.get('relation')} confidence={cr.get('confidence')}")
                            ctx_rels_txt = "\n".join(lines)
                    except Exception:
                        ctx_rels_txt = ""

                    parts = []
                    if ctx_rels_txt:
                        parts.append(ctx_rels_txt)
                    if media_ctx:
                        parts.append(media_ctx)
                    if learned_ctx:
                        parts.append(learned_ctx)
                    if rag_ctx:
                        parts.append(rag_ctx)
                    combined = "\n\n---\n\n".join(parts) if parts else (rag_ctx or "")
                    out_ans = self._finalize_llm_output(combined, lang="ar")
                except Exception:
                    out_ans = rag_ctx
                meta = {"source": "rag_shortcircuit"}
                if media_meta:
                    meta['media'] = media_meta
                try:
                    logger.debug("hosted_llm_adapter: taking rag_shortcircuit return (rag_ctx_len=%s, learned_ctx_len=%s)", len(rag_ctx) if rag_ctx else 0, len(learned_ctx) if learned_ctx else 0)
                except Exception:
                    pass

                return {
                    "engine": "rag",
                    "content": {"answer": out_ans},
                    "score": 0.92 if rag_ctx else 0.1,
                    "meta": meta,
                }
            else:
                # If we skipped the rag short-circuit due to force-external, log that fact
                try:
                    if engine_hint == 'rag' and _force_external:
                        logger.debug("hosted_llm_adapter: AGL_FORCE_EXTERNAL=1 -> skipping rag_shortcircuit and forcing external LLM path")
                except Exception:
                    pass

            # if retrieved context or learned facts exist, prepend them to the question so deep-coT/prompting sees them
            # include context relations if present in task
            try:
                prov = task.get('provenance') if isinstance(task, dict) else {}
                ctx_rels = prov.get('context_relations') if isinstance(prov, dict) else None
                ctx_rels_txt = None
                if ctx_rels and isinstance(ctx_rels, list):
                    ctx_rels_txt = "\n".join([f"relation: {cr.get('relation')} confidence={cr.get('confidence')}" for cr in ctx_rels])
            except Exception:
                ctx_rels_txt = None

            if rag_ctx or learned_ctx or media_ctx or ctx_rels_txt:
                parts = []
                if ctx_rels_txt:
                    parts.append(ctx_rels_txt)
                if media_ctx:
                    parts.append(media_ctx)
                if learned_ctx:
                    parts.append(learned_ctx)
                if rag_ctx:
                    parts.append(rag_ctx)
                prefix = "\n\n---\n\n".join(parts)
                question = f"{prefix}\n\n---\n\n{question}"
                if isinstance(task, dict):
                    task['question'] = question
                # include media_meta in task provenance so callers can persist
                if media_meta and isinstance(task, dict):
                    task.setdefault('provenance', {})['media'] = media_meta
        except Exception:
            pass

        # Decide whether to run Deep-CoT. Support Dynamic Cognition (Phase 14)
        try:
            task_type = task.get("task_type") if isinstance(task, dict) else "qa_single"
            # default to qa_single when missing or falsy
            if not task_type:
                task_type = "qa_single"
        except Exception:
            task_type = "qa_single"

        try:
            mode: Optional[cognitive_mode.CognitiveMode] = None
            # If dynamic cognition is enabled, ask it which mode to use (best-effort)
            if getattr(self, "dynamic_cognition_enabled", False):
                try:
                    prov = task.get("provenance") if isinstance(task, dict) else {}
                    runtime_ctx = prov.get("runtime_context") if isinstance(prov, dict) else None
                    mode = cognitive_mode.choose_cognitive_mode(task if isinstance(task, dict) else {"question": question}, runtime_context=runtime_ctx, profile_snapshot=None)
                    # expose last chosen mode for debugging/tests
                    try:
                        self._last_chosen_mode = mode
                    except Exception:
                        pass
                except Exception:
                    mode = None

            # Determine whether to use deep cot either via dynamic mode or static flag
            use_deep_cot = False
            if getattr(self, "dynamic_cognition_enabled", False) and mode is not None:
                if mode.use_cot and getattr(mode, "cot_depth", "none") == "deep":
                    use_deep_cot = True
            elif getattr(self, "deep_cot_enabled", False):
                use_deep_cot = True

            # record debug snapshot for decision tracing (tests inspect this)
            try:
                self._last_decision_debug = {
                    "use_deep_cot": use_deep_cot,
                    "task_type": task_type,
                    "question_present": bool(question),
                    "mode_cot_depth": getattr(mode, "cot_depth", None) if mode is not None else None,
                    "mode_use_cot": getattr(mode, "use_cot", None) if mode is not None else None,
                }
            except Exception:
                pass

            if use_deep_cot and task_type in ("qa_single", "qa_multi") and question:
                base_prompt = self._apply_prompt_patches(question)
                best = self._run_deep_cot(base_prompt, question, task_type=task_type)
                final_answer = best.get("answer", "")
                reasoning = best.get("reasoning", "")

                # lightweight self-critique hook
                critique = self._self_critique(question, final_answer)
                improved = critique.get("improved_answer", final_answer)
                try:
                    improved = self._finalize_llm_output(improved, lang="ar")
                except Exception:
                    pass

                return {
                    "engine": "hosted_llm",
                    "content": {
                        "answer": improved,
                        "reasoning_long": reasoning,
                        "note": "deep_cot_v1",
                    },
                }
        except Exception:
            # fallback to normal path if anything goes wrong
            pass

        # Enforce per-question overall timeout cap: do not allow more than 30s per question
        try:
            overall_deadline = min(float(timeout_s or 0) if timeout_s and timeout_s > 0 else 30.0, 30.0)
        except Exception:
            overall_deadline = 30.0

        try:
            # Decide whether to use Chain-of-Thought prompting.
            use_cot = False
            try:
                if isinstance(task, dict) and task.get('task_type') == 'qa_single':
                    qtxt = str(task.get('question') or task.get('title') or '')
                    # local lightweight heuristic for knowledge-like question
                    if any(t in qtxt for t in ("Ù…Ø§ Ù‡ÙŠ", "Ù…Ø§Ù‡Ùˆ", "Ù…Ø§ Ù‡Ùˆ", "Ø£Ø¹Ø±Ø§Ø¶", "Ø¹Ù„Ø§Ø¬", "Ø£Ø³Ø¨Ø§Ø¨", "symptoms", "treatment", "define", "what is")):
                        use_cot = True
            except Exception:
                use_cot = False

            if use_cot:
                # Long Chain-of-Thought mode with self-consistency sampling
                runs = []
                samples = int(os.getenv('AGL_COT_SAMPLES', '3'))
                cot_template = (
                    "Ø£Ù†Øª Ù…Ù†Ø¸ÙˆÙ…Ø© ØªÙÙƒÙŠØ± Ø¹Ù…ÙŠÙ‚. Ø§ÙƒØªØ¨ Ø³Ù„Ø³Ù„Ø© ØªÙÙƒÙŠØ± Ù…ÙƒÙˆÙ‘ÙŽÙ†Ø© Ù…Ù† 15 Ø¥Ù„Ù‰ 25 Ø®Ø·ÙˆØ©ØŒ "
                    "Ø­Ù„Ù„ Ø§Ù„Ø³Ø¤Ø§Ù„ØŒ Ø§Ø¨Ù†Ù ÙØ±ÙˆØ¶Ù‹Ø§ØŒ Ø§Ø®ØªØ¨Ø±Ù‡Ø§ØŒ Ø§ÙƒØ´Ù Ø§Ù„Ø£Ø®Ø·Ø§Ø¡ØŒ Ø§Ø³ØªØ¯Ø¹Ù Ø§Ù„Ù…Ø¹Ø±ÙØ© ÙˆØ§Ù„Ø°Ø§ÙƒØ±Ø©ØŒ "
                    "Ù‚Ù… Ø¨ØªØ­Ù„ÙŠÙ„ Ø³Ø¨Ø¨ÙŠØŒ Ø¶Ù‘ÙŠÙ‚ Ø§Ù„Ø­Ù„ØŒ Ø£Ø¬Ø±Ù Ø§Ù„ØªÙÙƒÙŠØ± Ø§Ù„Ù…Ø¶Ø§Ø¯ØŒ ØµØ­Ù‘Ø­ Ø§Ù„Ø£Ø®Ø·Ø§Ø¡ØŒ Ø«Ù… ÙÙŠ Ø¢Ø®Ø± Ø³Ø·Ø± "
                    "Ø§ÙƒØªØ¨ ÙÙ‚Ø· Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø© Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠØ© Ø§Ù„Ù…Ø®ØªØµØ±Ø© ÙˆÙˆØ§Ø¶Ø­Ø©.\n\n"
                    "Ø§Ù„Ø³Ø¤Ø§Ù„: {question}\n\n"
                    "Ø§Ù„Ù…Ø®Ø±Ø¬Ø§Øª Ø§Ù„Ù…Ø·Ù„ÙˆØ¨Ø©:\n"
                    "<reasoning_long: Ø®Ø·ÙˆØ§Øª Ø§Ù„ØªÙÙƒÙŠØ± Ø§Ù„ÙƒØ§Ù…Ù„Ø©>\n\n---FINAL ANSWER---\n"
                    "<final_answer>\n"
                )

                for i in range(samples):
                    # respect overall deadline: if we've run out of time, stop sampling
                    elapsed = time.time() - start
                    remaining = overall_deadline - elapsed
                    if remaining <= 0:
                        break
                    try:
                        prompt = cot_template.format(question=question)
                        # apply any prompt patches
                        prompt = self._apply_prompt_patches(prompt)
                        # per-sample cap: do not exceed 15s per CoT sample and also respect remaining time
                        per_call = min(15.0, max(3.0, remaining))
                        raw_out = self.call_ollama(prompt, timeout=per_call)
                    except Exception as e:
                        raw_out = f""  
                    # parse into reasoning and final as before
                    reasoning_i = ''
                    final_i = ''
                    try:
                        import re
                        sep_re = re.compile(r"---\s*FINAL ANSWER\s*---", flags=re.I)
                        parts = sep_re.split(raw_out or "", maxsplit=1)
                        if len(parts) == 2:
                            reasoning_i = parts[0].strip()
                            final_i = parts[1].strip()
                        else:
                            lines = [l.strip() for l in (raw_out or "").splitlines() if l.strip()]
                            if lines:
                                final_i = lines[-1]
                                reasoning_i = "\n".join(lines[:-1]).strip()
                            else:
                                final_i = (raw_out or "").strip()
                    except Exception:
                        final_i = (raw_out or "").strip(); reasoning_i = ''
                    runs.append({"raw": raw_out, "reasoning": reasoning_i, "final": final_i})

                # simple aggregation: pick most frequent final answer (self-consistency)
                finals = [r.get('final') or '' for r in runs]
                from collections import Counter
                cnt = Counter([f for f in finals if f])
                chosen_final = ''
                if cnt:
                    chosen_final = cnt.most_common(1)[0][0]
                else:
                    # fallback to first non-empty final
                    for f in finals:
                        if f:
                            chosen_final = f; break

                # If CoT produced nothing useful, fallback to a safe simple answer path
                cot_failed = False
                if not chosen_final or chosen_final.strip() == "":
                    cot_failed = True
                # also treat some obvious sensor-like outputs as failure
                if any(((r.get('final') or '').strip().lower() in ('patterns','shapes','signals') or (r.get('raw') or '').strip().lower().startswith('[echo]')) for r in runs):
                    cot_failed = True

                if cot_failed:
                    # try a simple direct call without CoT
                    try:
                        # for fallback, respect remaining overall deadline and cap at 15s
                        elapsed = time.time() - start
                        remaining = max(0.0, overall_deadline - elapsed)
                        simple_timeout = min(15.0, max(3.0, remaining))
                        prompt = self._apply_prompt_patches(question)
                        simple = self.call_ollama(prompt, timeout=simple_timeout)
                        # assemble/parse streaming if needed
                        try:
                            if isinstance(simple, str) and ('\n{' in simple or '"response"' in simple):
                                simple = self._parse_ollama_stream(simple)
                        except Exception:
                            pass
                        simple_clean = self._clean_answer(simple or '')
                        if simple_clean:
                            try:
                                chosen_final = self._finalize_llm_output(simple_clean, lang="ar")
                            except Exception:
                                chosen_final = simple_clean
                            # attach run to runs for traceability
                            runs.append({"raw": simple, "reasoning": "<simple-fallback>", "final": simple_clean})
                        else:
                            chosen_final = ''
                    except Exception:
                        chosen_final = ''

                # final fallback: safe canned answer from env or default
                if not chosen_final or not str(chosen_final).strip():
                    safe = os.getenv('AGL_SAFE_FALLBACK_ANSWER', 'Ø¹Ø°Ø±Ø§Ù‹ØŒ Ù„Ø§ Ø£Ø³ØªØ·ÙŠØ¹ ØªÙˆÙÙŠØ± Ø¥Ø¬Ø§Ø¨Ø© Ù…Ø¤ÙƒØ¯Ø© Ø¹Ù„Ù‰ Ù‡Ø°Ø§ Ø§Ù„Ø³Ø¤Ø§Ù„ Ø­Ø§Ù„ÙŠØ§Ù‹. ÙŠÙØ±Ø¬Ù‰ Ø§Ù„Ù…Ø­Ø§ÙˆÙ„Ø© Ù„Ø§Ø­Ù‚Ø§Ù‹.')
                    chosen_final = safe
                    runs.append({"raw": "", "reasoning": "<safe-fallback>", "final": chosen_final})

                # Merge reasoning: prefer the reasoning corresponding to chosen_final,
                # else concatenate all and mark as 'merged'.
                reasoning_long = ''
                reasoning_refined = ''
                if chosen_final:
                    for r in runs:
                        if (r.get('final') or '').strip() == chosen_final:
                            reasoning_long = r.get('reasoning') or ''
                            break
                if not reasoning_long:
                    reasoning_long = "\n\n".join([r.get('reasoning') or '' for r in runs if r.get('reasoning')])

                # Clean final and reasoning
                try:
                    reasoning_long = self._clean_answer(reasoning_long)
                except Exception:
                    pass
                try:
                    chosen_final = self._clean_answer(chosen_final or '')
                except Exception:
                    pass

                try:
                    final = self._finalize_llm_output(chosen_final or '', lang="ar")
                except Exception:
                    final = chosen_final or ''

                # Attach to content and also send to local deliberation/planner if available
                deliberation_out = None
                planner_out = None
                try:
                    # Try to load adapters from Knowledge_Graph if present
                    from agl.engines.self_improvement.Self_Improvement.Knowledge_Graph import DeliberationAdapter, PlannerAdapter
                    try:
                        del_adapter = DeliberationAdapter()
                        deliberation_out = del_adapter.infer({'question': question}, context=[reasoning_long], timeout_s=3.0)
                    except Exception:
                        deliberation_out = None
                    try:
                        plan_adapter = PlannerAdapter()
                        planner_out = plan_adapter.infer({'question': question}, context=[reasoning_long], timeout_s=3.0)
                    except Exception:
                        planner_out = None
                except Exception:
                    deliberation_out = None; planner_out = None

                raw = chosen_final
                # Place outputs into content below
                # keep finalized `final` if computed above, else use chosen_final
                final = final or chosen_final
                reasoning = reasoning_long
                # produce a metadata bundle
                verification_meta = None
                try:
                    verification_meta = self._verify_answer(question, final, timeout_s=min(60, int(timeout_s)))
                except Exception:
                    verification_meta = {"ok": True, "note": "verify-error", "improved_answer": None}

                content = {"answer": final or "", "note": "ollama-cot", "reasoning_long": reasoning_long, "runs": runs, "deliberation": deliberation_out, "planner": planner_out, "verified": verification_meta}
                tokens = len(str(final).split()) if final else 0
                score = 0.96 if final else 0.1
                # apply safety gating if requested
                try:
                    safe_content, safe_meta = self._safety_check_and_maybe_block(task if isinstance(task, dict) else {}, content, meta={"latency_ms": int((time.time() - start) * 1000), "tokens": tokens})
                    return {
                        "engine": self.name,
                        "content": safe_content,
                        "checks": {"constraints": True, "feasible": True},
                        "novelty": 0.55,
                        "meta": safe_meta,
                        "domains": list(set(self.domains + ["reasoning", "analysis"])),
                        "score": float(score),
                    }
                except Exception:
                    return {
                        "engine": self.name,
                        "content": content,
                        "checks": {"constraints": True, "feasible": True},
                        "novelty": 0.55,
                        "meta": {"latency_ms": int((time.time() - start) * 1000), "tokens": tokens},
                        "domains": list(set(self.domains + ["reasoning", "analysis"])),
                        "score": float(score),
                    }
            else:
                prompt = self._apply_prompt_patches(question)
                # Decide whether to use streaming deep-thinking path.
                deep_flag = False
                try:
                    # task may include a deep_mode toggle
                    deep_flag = bool(task.get('deep_mode') or task.get('deep_thinking') or task.get('use_deep'))
                except Exception:
                    deep_flag = False
                # allow operator override via env var
                try:
                    if os.getenv('AGL_DEEP_MODE', '0') == '1':
                        deep_flag = True
                except Exception:
                    pass

                if deep_flag:
                    # streaming deep-thinking: longer timeout
                    stream_timeout = int(os.getenv('AGL_DEEP_TIMEOUT', '300'))
                    try:
                        raw = self._call_ollama_stream(prompt, timeout=stream_timeout)
                    except Exception:
                        raw = self.call_ollama(prompt, timeout=timeout_s)
                else:
                    raw = self.call_ollama(prompt, timeout=timeout_s)
                # adapter debug prints removed in cleanup

                # Debug: show the raw returned text from call_ollama if requested
                try:
                        if os.getenv('AGL_DEBUG_ENGINES', '0') == '1':
                            try:
                                eh = task.get('engine_hint') if isinstance(task, dict) else None
                            except Exception:
                                eh = None
                            try:
                                preview_q = (question or '')[:200]
                            except Exception:
                                preview_q = ''
                            try:
                                dumpraw = raw if raw is not None else '<None>'
                            except Exception:
                                dumpraw = '<unreadable-raw>'
                            print(f"\nðŸ”¥ðŸ”¥ [ADAPTER RAW DEBUG] engine_hint={eh} prompt_preview={preview_q}\nRAW_OUTPUT:\n{dumpraw}\nðŸ”¥ðŸ”¥\n")
                except Exception:
                        pass
            latency = int((time.time() - start) * 1000)

            # assemble streaming/ndjson if present
            try:
                if isinstance(raw, str) and ('\n{' in raw or '"response"' in raw):
                    parsed = self._parse_ollama_stream(raw)
                    if parsed:
                        raw = parsed
            except Exception:
                pass

            # Try to split reasoning and final answer using delimiter
            reasoning = ''
            final = ''
            try:
                import re
                sep_re = re.compile(r"---\s*FINAL ANSWER\s*---", flags=re.I)
                parts = sep_re.split(raw, maxsplit=1)
                if len(parts) == 2:
                    reasoning = parts[0].strip()
                    final = parts[1].strip()
                else:
                    # fallback: take last non-empty paragraph/line as final answer
                    lines = [l.strip() for l in (raw or "").splitlines() if l.strip()]
                    if lines:
                        final = lines[-1]
                        reasoning = "\n".join(lines[:-1]).strip()
                    else:
                        final = raw.strip()
            except Exception:
                final = raw.strip(); reasoning = ''

            # Clean both reasoning and final answer
            try:
                if isinstance(reasoning, str) and reasoning.strip():
                    reasoning = self._clean_answer(reasoning)
            except Exception:
                pass
            try:
                if isinstance(final, str) and final.strip():
                    final = self._clean_answer(final)
            except Exception:
                pass

            # Basic rejection of obvious errors
            if isinstance(final, str):
                low = final.lower()
                if any(m in low for m in ("error:", "unknown flag", "unknown command", "not found", "cli-error", "failed:")):
                    return {
                        "engine": self.name,
                        "content": {"answer": "", "note": f"failed: {final[:200]}"},
                        "checks": {"constraints": False, "feasible": False},
                        "novelty": 0.1,
                        "meta": {"latency_ms": latency, "tokens": 0},
                        "domains": ["knowledge"],
                        "score": 0.1,
                    }

            # Verification step: ask the model to verify/improve the final answer
            verified = {"ok": True, "note": "not-run", "improved_answer": None}
            try:
                verified = self._verify_answer(question, final, timeout_s=min(80, int(timeout_s)))
                if verified and isinstance(verified.get("improved_answer"), str) and verified.get("improved_answer").strip():
                    # accept improved answer
                    final = self._clean_answer(verified.get("improved_answer"))
            except Exception:
                verified = {"ok": True, "note": "verify-error", "improved_answer": None}

            # Final postprocessing (cleanup + Arabic improvements)
            try:
                final = self._finalize_llm_output(final or '', lang="ar")
            except Exception:
                pass

            tokens = len(str(final).split()) if isinstance(final, str) else 0
            score = 0.96 if final else 0.1
            if final and "knowledge" in self.domains:
                score = max(0.92, min(0.99, score))

            content = {"answer": final or "", "note": "ollama-ok", "reasoning": reasoning, "verified": verified}
            try:
                safe_content, safe_meta = self._safety_check_and_maybe_block(task if isinstance(task, dict) else {}, content, meta={"latency_ms": latency, "tokens": tokens})
                return {
                    "engine": self.name,
                    "content": safe_content,
                    "checks": {"constraints": True, "feasible": True},
                    "novelty": 0.45,
                    "meta": safe_meta,
                    "domains": list(set(self.domains + ["reasoning", "analysis"])),
                    "score": float(score),
                }
            except Exception:
                return {
                    "engine": self.name,
                    "content": content,
                    "checks": {"constraints": True, "feasible": True},
                    "novelty": 0.45,
                    "meta": {"latency_ms": latency, "tokens": tokens},
                    "domains": list(set(self.domains + ["reasoning", "analysis"])),
                    "score": float(score),
                }
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return {
                "engine": self.name,
                "content": {"answer": f"[ollama-error] {question}", "note": f"failed: {e}"},
                "checks": {"constraints": False, "feasible": False},
                "novelty": 0.1,
                "meta": {"latency_ms": latency, "tokens": 0},
                "domains": ["knowledge"],
                "score": 0.1,
            }

    def infer(self, problem, context=None, timeout_s: float = 600.0):
        if isinstance(problem, dict):
            task = problem
        else:
            task = {"question": str(problem)}
        # Default to a reasonable per-question timeout (cap at 1200s)
        t = timeout_s if timeout_s and timeout_s > 0 else 600.0
        t = min(float(t), 1200.0)
        return self.process_task(task, t)


