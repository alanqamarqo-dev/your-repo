import os, json, time, pathlib, subprocess, sys
from datetime import datetime, timezone

REPO = pathlib.Path(__file__).resolve().parents[1]
ART = pathlib.Path(os.getenv("AGL_ARTIFACTS_DIR") or REPO/"data")
ART.mkdir(parents=True, exist_ok=True)

def run_py(args, extra_env=None):
    env = os.environ.copy()
    if extra_env: env.update(extra_env)
    p = subprocess.run([sys.executable] + args, cwd=str(REPO), env=env, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def measure(tag, env_overrides):
    rc, out, err = run_py(["scripts/test_search_quality.py"], extra_env=env_overrides)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (ART/f"quality_{tag}_{stamp}.out.txt").write_text(out, encoding="utf-8")
    (ART/f"quality_{tag}_{stamp}.err.txt").write_text(err, encoding="utf-8")
    return {"tag": tag, "rc": rc, "stdout_tail": "\n".join(out.splitlines()[-30:])}

def main():
    # قبل — بدون embeddings
    base_env = {
        "PYTHONPATH": str(REPO),
        "AGL_ARTIFACTS_DIR": str(ART),
        "PYTHONIOENCODING": "utf-8",
    }
    print("[MEASURE] Baseline reindex (no embeddings)")
    run_py(["scripts/run_clean_reindex.py"], extra_env={**base_env, "AGL_EMBEDDINGS_ENABLE":"0"})
    base = measure("baseline", {**base_env, "AGL_EMBEDDINGS_ENABLE":"0"})

    # بعد — مع embeddings
    print("[MEASURE] Reindex with embeddings")
    run_py(["scripts/run_clean_reindex.py"], extra_env={**base_env, "AGL_EMBEDDINGS_ENABLE":"1", "AGL_RETRIEVER_BLEND_ALPHA":"0.60"})
    emb = measure("embeddings", {**base_env, "AGL_EMBEDDINGS_ENABLE":"1", "AGL_RETRIEVER_BLEND_ALPHA":"0.60"})

    report = {"ts": time.time(), "repo": str(REPO), "artifacts": str(ART), "results": [base, emb]}
    # allow an optional --tag to write tag-specific JSON reports
    tag = None
    for i, v in enumerate(sys.argv):
        if v == "--tag" and i + 1 < len(sys.argv):
            tag = sys.argv[i + 1]
            break
    fname = f"semantic_before_after_{tag}.json" if tag else "semantic_before_after.json"
    out_path = ART / fname
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[MEASURE] Done. Report ->", out_path)

if __name__ == "__main__":
    main()
