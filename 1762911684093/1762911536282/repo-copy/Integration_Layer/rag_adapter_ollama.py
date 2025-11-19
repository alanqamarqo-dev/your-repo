import os
import json
import subprocess
import http.client
from typing import Any, Dict, List


def _ollama_http(prompt: str, base_url: str, model: str, timeout: int = 30, *,
                 num_predict: int = 64, num_ctx: int = 2048, temperature: float = 0.3,
                 keep_alive: str | None = "5m", stream: bool = False) -> str:
    # Build a payload that includes a system-prompt-prefixed prompt and generation options.
    payload_obj = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "num_predict": num_predict,
        "temperature": temperature,
        # some Ollama variants accept max_context_size or num_ctx
        "max_context_size": num_ctx,
    }
    if keep_alive:
        payload_obj["keep_alive"] = keep_alive

    payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
    host_port = base_url.replace("http://", "").replace("https://", "")
    if '/' in host_port:
        host_port = host_port.split('/')[0]
    host, port = host_port.split(":")
    conn = http.client.HTTPConnection(host, int(port), timeout=timeout)
    conn.request("POST", "/api/generate", payload, {"Content-Type": "application/json"})
    res = conn.getresponse()
    data = res.read()
    conn.close()
    if res.status != 200:
        raise RuntimeError(f"Ollama HTTP {res.status}: {data[:200]!r}")
    obj = json.loads(data.decode("utf-8"))
    # many ollama variations return {'response': '...'} or {'text': '...'}
    if isinstance(obj, dict):
        return obj.get('response') or obj.get('text') or json.dumps(obj)
    return str(obj)


def _ollama_cli(prompt: str, model: str, timeout: int = 30) -> str:
    # Some model variants reject the `--format text` flag; try it first and
    # fall back to a no-format invocation if it fails with a marshal/json error.
    def _run_with_args(args):
        return subprocess.run(
            args,
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )

    cp = _run_with_args(["ollama", "run", model, "--format", "text"])
    if cp.returncode != 0:
        stderr = cp.stderr.decode("utf-8", "ignore")
        # If the error looks like a JSON/Marshal issue, retry without --format
        if "MarshalJSON" in stderr or "invalid character" in stderr or "json:" in stderr:
            cp2 = _run_with_args(["ollama", "run", model])
            if cp2.returncode == 0:
                return cp2.stdout.decode("utf-8", "ignore").strip()
            # otherwise, raise the original helpful stderr
            raise RuntimeError(cp2.stderr.decode("utf-8", "ignore"))
        raise RuntimeError(stderr)
    return cp.stdout.decode("utf-8", "ignore").strip()


class OllamaRAG:
    def __init__(self, base_url: str | None, model: str, timeout: int = 30):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def answer(self, query: str, contexts: List[dict] | None = None) -> Dict[str, Any]:
        # Compose a system prompt and user prompt to bias for Arabic and concise answers.
        system_prompt = (os.getenv('AGL_LLM_SYSTEM_PROMPT') or
                         'أجب بالعربية الفصحى باختصار ودقّة. إن كانت المصادر غير متاحة فاذكر ذلك.')
        user_text = query
        if contexts:
            joined = "\n\n".join([c.get("text", "") for c in contexts if isinstance(c, dict)])
            user_text = f"Context:\n{joined}\n\nQuestion:\n{query}\n\nAnswer succinctly:"

        full_prompt = system_prompt + "\n\n" + user_text

        # Read generation tuning options from environment (overrideable)
        try:
            num_predict = int(os.getenv('AGL_LLM_NUM_PREDICT') or os.getenv('AGL_LLM_NUM_PREDICT_S') or 64)
        except Exception:
            num_predict = 64
        try:
            num_ctx = int(os.getenv('AGL_LLM_NUM_CTX') or 2048)
        except Exception:
            num_ctx = 2048
        try:
            temp = float(os.getenv('AGL_LLM_TEMPERATURE') or 0.3)
        except Exception:
            temp = 0.3
        keep_alive = os.getenv('AGL_LLM_KEEP_ALIVE') or '5m'
        stream = (os.getenv('AGL_LLM_STREAM', '0') in ('1', 'true', 'True'))

        # try HTTP first if base_url provided
        if self.base_url:
            try:
                txt = _ollama_http(full_prompt, self.base_url, self.model, self.timeout,
                                   num_predict=num_predict, num_ctx=num_ctx, temperature=temp,
                                   keep_alive=keep_alive, stream=stream)
                return {"answer": txt, "sources": ["ollama_http"], "engine": "ollama_http"}
            except Exception:
                pass
        # fallback to CLI (we still prefix with system prompt)
        txt = _ollama_cli(full_prompt, self.model, self.timeout)
        return {"answer": txt, "sources": ["ollama_cli"], "engine": "ollama_cli"}


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--base', default=os.getenv('OLLAMA_API_URL'))
    p.add_argument('--model', default=os.getenv('AGL_LLM_MODEL') or os.getenv('AGL_OLLAMA_KB_MODEL'))
    p.add_argument('query', nargs='?', default='What is graphene used for?')
    args = p.parse_args()
    o = OllamaRAG(args.base, args.model)
    print(o.answer(args.query))
