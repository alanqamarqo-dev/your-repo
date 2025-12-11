#!/usr/bin/env python3
"""Simple entry script to run a query through HostedLLMAdapter with RAG and learned_facts context.

This is a lightweight runner for smoke testing the integration.
"""
import argparse
import json
import os
from typing import Optional
from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter
from Self_Improvement.meta_logger import MetaLogger
from Integration_Layer.agl_state import AGLState
from Integration_Layer.executive_agent import ExecutiveAgent
# optional: bridge access for fallback visibility
try:
    from Core_Memory.bridge_singleton import get_bridge
except Exception:
    get_bridge = None
import time
import json
import pathlib
import re


def is_relevant(query, text):
    """Simple relevance check: return True if any non-stopword token
    from `query` appears in `text`. Unicode-aware; very lightweight.
    """
    try:
        q_words = set([w.strip().lower() for w in re.findall(r"\w+", str(query), flags=re.UNICODE) if w.strip()])
        stop_words = {"ما", "هو", "هي", "عن", "في", "من", "كيف", "هل", "ماهي", "ما هي", "ماهو", "ما هو"}
        keywords = {w for w in q_words if w not in stop_words}
        if not keywords:
            # Conservative policy: if no keywords were extracted from the query,
            # do NOT treat DB entries as relevant to avoid hallucinating answers.
            return False
        t_words = set([w.strip().lower() for w in re.findall(r"\w+", str(text), flags=re.UNICODE) if w.strip()])
        for kw in keywords:
            if kw in t_words:
                return True
        return False
    except Exception:
        return False


def run_query(question: str, project: str = 'default', media: Optional[list] = None):
    state = AGLState(question=question, project=project)
    meta = MetaLogger.start_session(state)
    # attach session id to state for snapshot logging
    try:
        state.session_id = meta.get('session_id')
    except Exception:
        pass

    adapter = HostedLLMAdapter()
    # ask adapter to prefer RAG short-circuit
    task = {"question": question, "task_type": "qa_single", "engine_hint": "rag"}
    if media:
        task['media'] = media
    out = adapter.process_task(task, timeout_s=30.0)

    # normalize
    if isinstance(out, dict):
        answer = out.get('content', {}).get('answer') or out.get('answer') or ''
    else:
        answer = str(out)

    # record an engine call in state
    out_meta = getattr(out, 'meta', None) or (out.get('meta') if isinstance(out, dict) else {})
    state.record_engine_call(getattr(adapter, 'name', 'hosted_llm'), answer, meta=out_meta)
    # ingest media metadata into state if present
    try:
        if isinstance(out_meta, dict) and out_meta.get('media'):
            for m in out_meta.get('media'):
                state.add_media_ctx(m)
    except Exception:
        pass

    # take an end-of-session snapshot
    try:
        state.tick('end_session')
    except Exception:
        pass

    # trigger learning/persist if needed (reward loop)
    try:
        learn_info = state.trigger_learning_if_needed(answer, provenance=getattr(out, 'meta', None) or (out.get('meta') if isinstance(out, dict) else {}))
        try:
            if MetaLogger is not None and state.session_id:
                MetaLogger.log_event(state.session_id, 'learning_trigger', learn_info)
        except Exception:
            pass
    except Exception:
        learn_info = {}

    # finish session and persist metadata
    MetaLogger.finish_session(meta, state)

    print('--- ANSWER ---')
    print(answer)
    # If the adapter produced no visible answer, fall back to semantic retrieval
    if not answer or str(answer).strip() == '':
        # If adapter returned empty, try forensic DB read (data/memory.sqlite or artifacts backup)
        try:
            repo_root = os.path.dirname(os.path.dirname(__file__))
            db_candidates = [
                os.path.join(repo_root, 'data', 'memory.sqlite'),
                os.path.join(repo_root, 'artifacts', 'medical_seed.sqlite'),
                os.path.join(repo_root, 'artifacts', 'memory.sqlite'),
            ]
            found = None
            for p in db_candidates:
                try:
                    if os.path.exists(p):
                        found = p
                        break
                except Exception:
                    continue
            if found:
                try:
                    import sqlite3
                    conn = sqlite3.connect(found)
                    cur = conn.cursor()
                    cur.execute("SELECT payload FROM events LIMIT 1")
                    r = cur.fetchone()
                    conn.close()
                    if r and r[0]:
                        payload_text = r[0]
                        # try to parse JSON
                        try:
                            import json as _json
                            parsed = _json.loads(payload_text)
                            text = parsed.get('text') if isinstance(parsed, dict) else None
                        except Exception:
                            text = payload_text
                        if text:
                            # only print fallback if relevant to the query
                            if is_relevant(question, text):
                                print('\n--- FALLBACK DB LTM ANSWER ---')
                                print(text)
                                answer = text
                            else:
                                print('\n--- NO ANSWER FOUND IN DB (not relevant) ---')
                except Exception:
                    pass
        except Exception:
            pass
        except Exception:
            pass
    return answer





def main():
    p = argparse.ArgumentParser()
    p.add_argument('--question', '-q', required=False)
    p.add_argument('--project', default='default')
    p.add_argument('--media', help='Comma-separated media file paths', default=None)
    p.add_argument('--bench', action='store_true', help='Run benchmark suite instead of single query')
    p.add_argument('--tasks', help='Optional JSONL file with benchmark tasks', default=None)
    p.add_argument('--plan', action='store_true', help='Run multi-step planning (generate hypotheses)')
    args = p.parse_args()
    # If not running benchmark, require a question
    if not args.bench and not args.question:
        p.error('the following arguments are required: --question/-q')
    if args.bench:
        # Run basic benchmark: either from tasks file or a built-in small suite
        if args.tasks and pathlib.Path(args.tasks).exists():
            tasks = []
            with open(args.tasks, 'r', encoding='utf-8') as fh:
                for ln in fh:
                    try:
                        j = json.loads(ln)
                        tasks.append(j.get('question') or j.get('q') or j.get('prompt'))
                    except Exception:
                        continue
        else:
            tasks = [
                "ما هي أعراض الإنفلونزا؟",
                "ما أسباب ارتفاع ضغط الدم؟",
                "ما هو الفشل الكلوي المزمن؟",
            ]

        results = []
        for q in tasks:
            print(f"Running benchmark question: {q}")
            media_list = [p.strip() for p in (args.media or '').split(',') if p.strip()] if args.media else None
            a = run_query(q, args.project, media=media_list)
            results.append({'question': q, 'answer': a})

        ts = int(time.time())
        out_json = pathlib.Path('artifacts') / f'bench_report_{ts}.json'
        out_md = pathlib.Path('reports') / f'bench_summary_{ts}.md'
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, 'w', encoding='utf-8') as fh:
            json.dump(results, fh, ensure_ascii=False, indent=2)
        with open(out_md, 'w', encoding='utf-8') as fh:
            fh.write('# Benchmark Summary\n')
            fh.write(f'Generated: {time.ctime(ts)}\n\n')
            for r in results:
                fh.write('## Question\n')
                fh.write(r['question'] + '\n\n')
                fh.write('### Answer\n')
                fh.write(r['answer'] + '\n\n')

        print(f'Wrote bench report to {out_json} and summary to {out_md}')
    else:
        media_list = [p.strip() for p in (args.media or '').split(',') if p.strip()] if args.media else None
        if args.plan:
            agent = ExecutiveAgent(n_variants=3)
            variants, best = agent.run_plan(args.question, project=args.project, media=media_list)
            print('--- HYPOTHESES ---')
            for v in variants:
                print(f"[{v['idx']}] score={v['score']['score']:.3f} instr={v['instr']}\n{v['answer']}\n---\n")
            if best:
                print('--- SELECTED BEST ---')
                print(f"idx={best['idx']} score={best['score']['score']:.3f}\n{best['answer']}")
                # Ensure a final user-facing answer is printed for visibility.
                try:
                    final = best.get('answer')
                    if isinstance(final, dict):
                        # common shapes: {'content': {'answer': '...'}} or {'answer': '...'}
                        final_text = final.get('content', {}).get('answer') if final.get('content') else final.get('answer')
                    else:
                        final_text = str(final)
                    print('\n--- FINAL ANSWER ---')
                    if final_text:
                        print(final_text)
                    else:
                        printed = False
                        if variants and len(variants) > 0:
                            v0 = variants[0].get('answer')
                            if v0:
                                print(v0)
                                printed = True
                        if not printed:
                            # As a last-resort forensic fallback, read the DB and print stored LTM text
                            try:
                                repo_root = os.path.dirname(os.path.dirname(__file__))
                                db_candidates = [
                                    os.path.join(repo_root, 'data', 'memory.sqlite'),
                                    os.path.join(repo_root, 'artifacts', 'medical_seed.sqlite'),
                                    os.path.join(repo_root, 'artifacts', 'memory.sqlite'),
                                ]
                                found = None
                                for p in db_candidates:
                                    try:
                                        if os.path.exists(p):
                                            found = p
                                            break
                                    except Exception:
                                        continue
                                if found:
                                    import sqlite3
                                    conn = sqlite3.connect(found)
                                    cur = conn.cursor()
                                    cur.execute("SELECT payload FROM events LIMIT 1")
                                    r = cur.fetchone()
                                    conn.close()
                                    if r and r[0]:
                                        try:
                                            import json as _json
                                            parsed = _json.loads(r[0])
                                            text = parsed.get('text') if isinstance(parsed, dict) else None
                                        except Exception:
                                            text = r[0]
                                        if text:
                                            # only print DB final answer if relevant to the question
                                            if is_relevant(args.question, text):
                                                print('\n--- FINAL ANSWER (FROM DB) ---')
                                                print(text)
                                                printed = True
                                            else:
                                                print('\n--- FINAL ANSWER (FROM DB) SKIPPED (not relevant) ---')
                            except Exception:
                                pass
                        if not printed:
                            print('(no answer text available)')
                except Exception:
                    # best-effort: if anything fails, still print the raw best object
                    try:
                        print('\n--- FINAL ANSWER (raw) ---')
                        print(best['answer'])
                    except Exception:
                        pass
        else:
            run_query(args.question, args.project, media=media_list)


if __name__ == '__main__':
    main()
