import os
import subprocess
import shlex
from pathlib import Path
import streamlit as st

# Simple Streamlit dashboard for AGL / Genesis Alpha
# - Shows LLM config from env
# - Tails recent test log (if present)
# - Provides a smoke ping button (runs scripts/smoke_llm_ping.py)

st.set_page_config(page_title="AGL Genesis Alpha Dashboard", layout="wide")

st.title("AGL — Genesis Alpha Dashboard")

col1, col2 = st.columns([2, 1])

with col1:
    st.header("System Overview")
    base = os.getenv("AGL_LLM_BASEURL") or os.getenv("OLLAMA_API_URL") or "http://localhost:11434"
    model = os.getenv("AGL_LLM_MODEL", "qwen2.5:7b-instruct")
    llm_type = os.getenv("AGL_LLM_TYPE", "openai")
    timeout = os.getenv("AGL_HTTP_TIMEOUT", "30")

    st.markdown(f"**LLM Base URL:** `{base}`")
    st.markdown(f"**LLM Model:** `{model}`")
    st.markdown(f"**LLM Type:** `{llm_type}`")
    st.markdown(f"**HTTP Timeout (s):** `{timeout}`")

    st.subheader("Recent system log")
    log_path = Path("repo-copy_test_run.log")
    if not log_path.exists():
        # Also check repo-copy/logs
        alt = Path("repo-copy/logs/last_run.log")
        if alt.exists():
            log_path = alt

    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-400:]
            st.code("".join(lines[-200:]), language="text")
        except Exception as e:
            st.error(f"Failed to read log: {e}")
    else:
        st.info("No run log found in repository root. Run tests or the system to generate logs.")

    st.subheader("Quick Actions")
    ping_col, run_col = st.columns(2)

    if ping_col.button("Run LLM smoke ping"):
        st.info("Running smoke ping... this may take a few seconds.")
        try:
            # Prefer bundled script if available
            script = Path("scripts/smoke_llm_ping.py")
            if script.exists():
                cmd = f"python {str(script)} --base {shlex.quote(base)} --model {shlex.quote(model)}"
            else:
                # fallback to calling quick_llm_ping if present
                cmd = f"python scripts/quick_llm_ping.py --base {shlex.quote(base)} --model {shlex.quote(model)}"

            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            out = proc.stdout or proc.stderr or "(no output)"
            st.code(out, language="text")
        except subprocess.TimeoutExpired:
            st.error("Smoke ping timed out.")
        except Exception as e:
            st.error(f"Error running smoke ping: {e}")

    if run_col.button("Run AGI quick tests (1-4)"):
        st.info("Launching AGI quick tests (this runs `tmp_run_agi_tests.py`). Output will stream to a log file.")
        try:
            # Launch the test runner and capture output to repo-copy_test_run.log
            cmd = f"python tmp_run_agi_tests.py"
            with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as p:
                # stream a bit of output to the UI
                lines = []
                for i, line in enumerate(p.stdout):
                    lines.append(line)
                    if i < 200:
                        st.text(line.rstrip())
                p.wait(timeout=600)
            # Save truncated output to log file
            with open("repo-copy_test_run.log", "w", encoding="utf-8") as out_f:
                out_f.write("".join(lines[-1000:]))
            st.success("Tests finished — log written to repo-copy_test_run.log")
        except subprocess.TimeoutExpired:
            st.error("Test runner timed out (600s).")
        except Exception as e:
            st.error(f"Failed to run tests: {e}")

with col2:
    st.header("System Health")
    # Lightweight checks
    try:
        import socket

        host = base.split("//")[-1].split(":")[0]
        port = int(base.split(":")[-1]) if ":" in base and base.endswith("11434") or ":" in base else 11434
        s = socket.socket()
        s.settimeout(1.0)
        try:
            s.connect((host, port))
            st.success(f"LLM host reachable: {host}:{port}")
        except Exception:
            st.error(f"LLM host not reachable: {host}:{port}")
        finally:
            s.close()
    except Exception:
        st.info("Skipping socket check (environment may be restricted).")

    st.markdown("---")
    st.subheader("Env Vars")
    env_keys = ["AGL_LLM_BASEURL", "AGL_LLM_MODEL", "AGL_LLM_TYPE", "AGL_HTTP_TIMEOUT", "AGL_LLM_ENDPOINT"]
    for k in env_keys:
        st.text(f"{k} = {os.getenv(k, '')}")

    st.markdown("---")
    st.caption("Built-in quick dashboard: expand with charts and real-time sockets. Run with: `streamlit run web_dashboard.py` from repo root.")
