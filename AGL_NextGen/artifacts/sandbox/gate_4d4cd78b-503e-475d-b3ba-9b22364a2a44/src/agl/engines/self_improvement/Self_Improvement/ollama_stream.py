import os
import requests
import json
from typing import Optional
from utils.llm_tools import build_llm_url


def ask_with_deep_thinking(prompt: str, model: Optional[str] = None, timeout: int = 300) -> str:
    """
    Stream responses from a local Ollama instance using the /api/generate endpoint.

    - prompt: the user prompt to send (e.g. "كلب يطير").
    - model: optional model name; will fallback to env var AGL_OLLAMA_MODEL or 'qwen2.5:7b-instruct' as default.
    - timeout: request timeout in seconds (default 300s for deep thinking).

    Returns the full concatenated response as a string. Prints tokens as they arrive.
    If Ollama is not reachable or streaming format differs, returns an error string.
    """
    model = model or os.environ.get('AGL_OLLAMA_MODEL') or 'qwen2.5:7b-instruct'
    # Allow explicit Ollama URL override; otherwise use canonical generator endpoint
    base_override = os.environ.get('AGL_OLLAMA_URL') or os.environ.get('AGL_LLM_BASEURL')
    url = build_llm_url('generate', base=base_override)

    data = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_ctx": int(os.environ.get('AGL_OLLAMA_NUM_CTX', '4096')),
            "temperature": float(os.environ.get('AGL_OLLAMA_TEMPERATURE', '0.6'))
        }
    }

    print("جاري التفكير...", end="", flush=True)

    try:
        # Use stream=True and a long timeout
        with requests.post(url, json=data, stream=True, timeout=timeout) as response:
            if response.status_code != 200:
                # Try to show helpful error
                try:
                    text = response.text
                except Exception:
                    text = '<no-response-body>'
                return f"Error: {response.status_code} - {text}"

            full_response = ""
            # Ollama may stream JSON lines; iterate lines conservatively
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                # Some servers send lines like: b'{"response":"token","done":false}'
                try:
                    body = json.loads(line)
                except Exception:
                    # Not JSON: print raw chunk and append
                    chunk = line if isinstance(line, str) else line.decode('utf-8', errors='replace')
                    print(chunk, end="", flush=True)
                    full_response += chunk
                    continue

                token = body.get('response') or body.get('token') or body.get('text') or ''
                if token:
                    print(token, end="", flush=True)
                    full_response += token

                # If Ollama signals completion
                if body.get('done') is True or body.get('type') == 'done':
                    print("\n[تم الانتهاء]")
                    break

            return full_response

    except requests.exceptions.Timeout:
        return "نفذ الوقت! التفكير العميق استغرق وقتاً أطول من المسموح."
    except requests.exceptions.ConnectionError as e:
        return f"اتصال فشل: {e} - تأكد من تشغيل Ollama على {url}"
    except Exception as e:
        return f"حدث خطأ تقني: {e}"


if __name__ == '__main__':
    # Quick CLI tester (safe: will error if Ollama not running)
    test_prompt = os.environ.get('AGL_TEST_PROMPT', 'لماذا السماء زرقاء؟ فكر بعمق.')
    out = ask_with_deep_thinking(test_prompt)
    print('\n--- 결과 ---')
    print(out)
