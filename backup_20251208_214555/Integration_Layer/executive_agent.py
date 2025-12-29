#!/usr/bin/env python3
"""ExecutiveAgent: orchestration for multi-step planning / hypothesis generation.

Provides a compact, testable class that uses `HostedLLMAdapter` to generate
several hypothesis variants, scores them via `AGLState.evaluate_and_score`,
logs hypotheses and snapshots via `MetaLogger`, and can trigger learning.

This is a direct refactor of the previous shim `run_multistep_plan()`.
"""
from typing import List, Dict, Any, Optional
import time

from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter
from Integration_Layer.agl_state import AGLState
from Self_Improvement.meta_logger import MetaLogger
import os
import time


class ExecutiveAgent:
    def __init__(self, n_variants: int = 3, variant_instructions: Optional[List[str]] = None):
        self.n_variants = n_variants
        self.adapter = HostedLLMAdapter()
        if variant_instructions is None:
            self.variant_instructions = [
                "أعد الصياغة باختصار ووضوح.",
                "أعد الصياغة بصيغة علمية ورسمية.",
                "أعد الصياغة مشفوعة بتحليل سببي موجز.",
            ]
        else:
            self.variant_instructions = variant_instructions

    def _generate_variant(self, question: str, instr: str, media: Optional[List[str]] = None) -> Dict[str, Any]:
        task_q = f"{question}\n\n{instr}\n"
        task = {"question": task_q, "task_type": "qa_single", "engine_hint": "rag"}
        if media:
            task['media'] = media
        # allow env override for timeout (useful for long-running engines)
        try:
            env_to = float(os.getenv('AGL_TIMEOUT', '30'))
        except Exception:
            env_to = 30.0
        out = self.adapter.process_task(task, timeout_s=env_to)
        ans = ''
        meta_out = {}
        content_out = None
        if isinstance(out, dict):
            ans = out.get('content', {}).get('answer') or out.get('answer') or ''
            meta_out = out.get('meta') or {}
            content_out = out.get('content') or {}
        else:
            ans = str(out)

        # If RAG produced no useful answer (short-circuit), retry with a
        # fallback creative/external hint so the LLM can author an answer.
        try:
            short_circuit = False
            if not ans or (isinstance(ans, str) and not ans.strip()):
                short_circuit = True
            # also detect common rag short-circuit markers in meta
            if isinstance(meta_out, dict):
                src = meta_out.get('source') or meta_out.get('reason') or ''
                if isinstance(src, str) and 'rag_shortcircuit' in src:
                    short_circuit = True
            if short_circuit:
                try:
                    print("⚠️ RAG returned empty/short-circuit for variant; retrying with fallback engine_hint='external'")
                except Exception:
                    pass
                # Prepare fallback task - allow the adapter to be creative
                try:
                    fb_task = dict(task)
                    fb_task['engine_hint'] = os.getenv('AGL_FALLBACK_HINT', 'external')
                    # non-breaking hint; some adapters accept allow_hallucination
                    fb_task['allow_hallucination'] = True
                    out_fb = self.adapter.process_task(fb_task, timeout_s=env_to)
                    if isinstance(out_fb, dict):
                        ans_fb = out_fb.get('content', {}).get('answer') or out_fb.get('answer') or out_fb.get('text') or ''
                        meta_fb = out_fb.get('meta') or {}
                        content_fb = out_fb.get('content') or {}
                    else:
                        ans_fb = str(out_fb)
                        meta_fb = {}
                        content_fb = None

                    if ans_fb and str(ans_fb).strip():
                        ans = ans_fb
                        # merge some meta info to indicate fallback
                        try:
                            if isinstance(meta_out, dict):
                                meta_out['fallback'] = meta_fb or {'used': fb_task.get('engine_hint')}
                            else:
                                meta_out = meta_fb or {'used': fb_task.get('engine_hint')}
                        except Exception:
                            meta_out = meta_fb or {'used': fb_task.get('engine_hint')}
                        content_out = content_fb
                except Exception:
                    # fallback attempt failed silently; continue with original out
                    pass
        except Exception:
            pass

        # Debug: print per-variant adapter output when enabled
        try:
            if str(os.getenv('AGL_DEBUG_ENGINES', '0')) == '1':
                tstamp = time.strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n--- ENGINE DEBUG [{tstamp}] variant_idx={instr} ---")
                try:
                    # print the full raw adapter output for inspection
                    print("raw_adapter_output:")
                    print(out)
                except Exception:
                    print("(raw adapter output not printable)")
                try:
                    print("extracted_answer:", repr(ans))
                except Exception:
                    pass
                try:
                    print("meta_out:", meta_out)
                except Exception:
                    pass
                # also print any engine_trace inside meta or content
                try:
                    et = None
                    if isinstance(out, dict):
                        et = out.get('meta', {}) or out.get('content', {}).get('engine_trace') or out.get('engine_trace')
                    if et:
                        print("engine_trace:")
                        print(et)
                except Exception:
                    pass
                print("--- END ENGINE DEBUG ---\n")
        except Exception:
            pass
        return {'answer': ans, 'meta': meta_out, 'content': content_out, 'instr': instr, 'raw': out}

    def run_plan(self, question: str, project: str = 'default', media: Optional[List[str]] = None) -> (List[Dict[str, Any]], Optional[Dict[str, Any]]): # type: ignore
        """Run the multi-step planning flow and return (variants, best_variant).

        - Generates `n_variants` paraphrase/analysis variants
        - Scores each using an `AGLState` instance
        - Logs hypotheses and snapshots
        - Triggers learning if the selected best passes thresholds
        """
        state = AGLState(question=question, project=project)
        # start session metadata
        meta = MetaLogger.start_session(state)
        try:
            state.session_id = meta.get('session_id')
        except Exception:
            pass

        variants = []
        for i in range(self.n_variants):
            instr = self.variant_instructions[i % len(self.variant_instructions)]
            v = self._generate_variant(question, instr, media=media)
            ans = v.get('answer')
            meta_out = v.get('meta') or {}
            # record engine call
            state.record_engine_call(getattr(self.adapter, 'name', 'hosted_llm'), ans, meta=meta_out)
            # ingest media metadata to state
            try:
                if isinstance(meta_out, dict) and meta_out.get('media'):
                    for m in meta_out.get('media'):
                        state.add_media_ctx(m)
            except Exception:
                pass

            # try to gather evidence from provenance
            try:
                rawp = meta_out.get('raw_provenance') if isinstance(meta_out, dict) else None
                if rawp and isinstance(rawp, dict):
                    did = rawp.get('doc_id') or rawp.get('source')
                    snippet = rawp.get('snippet') or ''
                    if did:
                        state.add_evidence(str(did), snippet, score=float(rawp.get('score', 0.5)))
            except Exception:
                pass

            # Prefer scoring on the richer reasoning text when available to avoid
            # penalizing short cleaned answers that hide detailed reasoning.
            try:
                content = v.get('content') or {}
                # prefer 'reasoning_long', fall back to 'reasoning', then to raw content
                if isinstance(content, dict):
                    reasoning_long = content.get('reasoning_long') or content.get('reasoning') or content.get('raw')
                else:
                    reasoning_long = None
                # If no structured reasoning field, try raw adapter output
                if not reasoning_long and v.get('raw'):
                    try:
                        # raw may be a dict or string
                        raw = v.get('raw')
                        if isinstance(raw, dict):
                            reasoning_long = raw.get('content', {}).get('reasoning') or raw.get('content', {}).get('reasoning_long') or raw.get('content', {}).get('answer')
                        else:
                            reasoning_long = str(raw)
                    except Exception:
                        reasoning_long = None
                score_input = (reasoning_long + "\n\n" + ans).strip() if reasoning_long else ans
            except Exception:
                score_input = ans
            score_info = state.evaluate_and_score(score_input, provenance=meta_out)
            variant = {'idx': i, 'instr': instr, 'answer': ans, 'meta': meta_out, 'score': score_info}
            variants.append(variant)

            # log hypothesis event
            try:
                if MetaLogger is not None and state.session_id:
                    MetaLogger.log_event(state.session_id, 'hypothesis', {'idx': i, 'instr': instr, 'score': score_info})
            except Exception:
                pass

        # select best
        best = None
        best_score = -1.0
        for v in variants:
            s = float(v.get('score', {}).get('score', 0.0))
            if s > best_score:
                best_score = s
                best = v

        # trigger learning/persistence if best selected
        if best:
            try:
                linfo = state.trigger_learning_if_needed(best.get('answer', ''), provenance=best.get('meta') or {})
                try:
                    if MetaLogger is not None and state.session_id:
                        MetaLogger.log_event(state.session_id, 'selected_hypothesis', {'best_idx': best.get('idx'), 'score': best_score, 'learn_info': linfo})
                except Exception:
                    pass
            except Exception:
                pass

        # final snapshot and finish
        try:
            state.tick('plan_complete')
        except Exception:
            pass
        MetaLogger.finish_session(meta, state)
        return variants, best
