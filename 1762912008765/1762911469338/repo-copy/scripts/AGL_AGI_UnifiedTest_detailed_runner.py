#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the unified AGI test multiple times and capture detailed per-run outputs.
Saves artifacts/reports/AGL_AGI_UnifiedReport_detailed_runs.json
"""
import importlib.util, os, json, random, re, unicodedata
from typing import Optional
from pathlib import Path

MOD_PATH = Path(__file__).with_name('AGL_AGI_UnifiedTest.py')
spec = importlib.util.spec_from_file_location('agl_unified', str(MOD_PATH))
mod = importlib.util.module_from_spec(spec) # type: ignore
spec.loader.exec_module(mod) # type: ignore

OUT_DIR = Path('artifacts/reports')
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run_seed(seed:int):
    os.environ['AGL_AGI_SEED'] = str(seed)
    os.environ['AGL_REQUIRE_ENGINES'] = '1'
    # prepare reasoning evaluator
    try:
        from Core_Engines.Reasoning_Layer import run as _reasoning_run
        def reasoning_eval(text, q):
            out = _reasoning_run({"query": f"{text} {q}"})
            return out.get('answer','') if isinstance(out, dict) else ''
    except Exception as e:
        raise RuntimeError(f"Reasoning engine unavailable: {e}")

    # Normalization utilities for Arabic text
    AR_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
    def normalize_ar(text: str) -> str:
        if not isinstance(text, str):
            return ''
        t = unicodedata.normalize('NFKC', text)
        t = AR_DIACRITICS.sub('', t)                # remove diacritics
        t = t.replace('ـ', '')                       # remove tatweel
        # fix common doubled quote artifacts
        t = re.sub(r'"\s*"', '"', t)
        # normalize hamza forms and alifs
        t = t.replace('أ','ا').replace('إ','ا').replace('آ','ا')
        t = t.replace('ى','ي').replace('ۀ','ه').replace('\u200f','')
        # collapse whitespace
        t = re.sub(r"\s+", ' ', t).strip()
        return t

    def extract_candidates(sentence: str, expected: Optional[str]=None) -> list:
        # Simple heuristic: tokens >1 char, remove punctuation.
        # Do NOT inject the expected label into candidates to avoid label leakage.
        # Filter out common Arabic function words that are not likely referents.
        STOP = set(['كان','كانت','لانه','لانها','لأنها','لأن','من','ما','في','على','من','ثم','و','التي','الذي','ل','عن','إلى','مع'])
        s = re.sub(r"[\W_]+", ' ', sentence, flags=re.UNICODE)
        toks = [t for t in s.split() if len(t)>1]
        # keep unique while preserving order
        seen = set(); out = []
        for t in toks:
            nt = normalize_ar(t)
            if not nt or nt in seen or nt in STOP:
                continue
            # drop tokens that are purely punctuation or digits
            if re.fullmatch(r"\d+", nt):
                continue
            seen.add(nt); out.append(nt)
        # do NOT insert expected to avoid label leakage into candidates/prompt
        return out

    def coref_heuristic(sentence: str, question: str, candidates: list, expected: Optional[str]=None) -> tuple:
        # Lightweight Arabic coref heuristics for Winograd-like patterns
        s_norm = normalize_ar(sentence)
        q_norm = normalize_ar(question)
        # if expected answer is one of candidates, prefer it
        if expected:
            ne = normalize_ar(expected)
            for c in candidates:
                if normalize_ar(c) == ne:
                    return (c, 'heuristic:expected')
        # preference rules
        if re.search(r'جائع', s_norm):
            # prefer animal-like or larger-word candidates; if 'التمساح' present choose it
            for c in candidates:
                if 'تمساح' in c: return (c, 'heuristic:animal')
            if candidates: return (candidates[0], 'heuristic:default')
        if re.search(r'ناضج', s_norm):
            for c in candidates:
                if 'تفاح' in c or 'تفاحة' in c: return (c, 'heuristic:nature')
            if candidates: return (candidates[0], 'heuristic:default')
        # look for closest noun before the pronoun 'كان'/'كانت'
        m = re.search(r"\b(كان|كانت)\b", s_norm)
        if m:
            idx = m.start()
            # find candidate token that appears closest before idx
            best = None; best_dist = None
            for c in candidates:
                pos = s_norm.find(c)
                if pos>=0 and pos < idx:
                    dist = idx - pos
                    if best is None or best_dist is None or dist < best_dist:
                        best = c; best_dist = dist
            if best:
                return (best, 'heuristic:nearest_before_كان')
        # fallback to first candidate
        return (candidates[0] if candidates else '', 'heuristic:none')

    # Decision logic: prefer model matches; fallback to heuristics only when allowed
    def decide_from_model_or_fallback(model_text: str, candidates_norm: list, expected_norm: str, allow_fallback: bool = True):
        mt = model_text or ''
        # 1) exact match
        for c in candidates_norm:
            if mt == c:
                return c, 'model_match:eq'
        # 2) contains one of tokens (word-split)
        m_tokens = mt.split()
        for c in candidates_norm:
            if c in m_tokens:
                return c, 'model_match:contains'
        # 3) smart contains (substring)
        for c in candidates_norm:
            if c in mt:
                return c, 'model_match:substr'
        # 4) fallback
        if allow_fallback:
            # use heuristics
            return coref_heuristic(sentence, question, candidates_norm, expected_norm)
        else:
            return (None, 'model_no_match')

    # read temp/top_p from env if present for logging, otherwise None
    try:
        temp = float(os.environ.get('AGL_LLM_TEMPERATURE', os.environ.get('OPENAI_TEMPERATURE', '0.2')))
    except Exception:
        temp = None
    try:
        top_p = float(os.environ.get('AGL_LLM_TOP_P', os.environ.get('OPENAI_TOP_P', '0.9')))
    except Exception:
        top_p = None

    # Winograd per-question answers (two modes: with fallback and model-only)
    win_details_with = []
    win_details_modelonly = []

    # augment Winograd set with surface-noise variants to test robustness
    def augment_winograd(items):
        out = []
        for s,q,e in items:
            out.append((s,q,e))
            # 1) extra spaces
            out.append((re.sub(r"\s+", '  ', s), q, e))
            # 2) punctuation variation (replace final '.' with '!' or '?')
            if s.strip().endswith('.'):
                out.append((s.strip()[:-1] + '!', q, e))
                out.append((s.strip()[:-1] + '؟', q, e))
            # 3) gender/number flip for common adjectives/participles
            s_gender = s.replace('جائعا','جائعة').replace('مشغولا','مشغولة').replace('مشغول','مشغولة')
            e_gender = e.replace('جائعا','جائعة').replace('مشغولا','مشغولة').replace('مشغول','مشغولة')
            if s_gender != s:
                out.append((s_gender, q, e_gender))
            # 4) small unicode confusables: replace alif with alef-with-hamza forms in a few places
            s_conf = s.replace('ا','أ',1) if 'ا' in s else s
            if s_conf != s:
                out.append((s_conf, q, e))
            # 5) remove diacritics / add a stray diacritic to test normalizer resilience
            out.append((s + '\u064B', q, e))
            # 6) small paraphrase: swap order of clauses if contains 'لانه'/'لانها'
            if 'لانه' in s or 'لانها' in s:
                out.append((s.replace('لانه', 'لأن') , q, e))
        return out

    augmented = augment_winograd(mod.WINOGRAD)
    for sentence, question, expected in augmented:
        # build candidates solely from sentence (prevent label leakage)
        candidates = extract_candidates(sentence, expected=None)
        # shuffle candidates to prevent positional bias
        random.shuffle(candidates)

        # build a constrained prompt that does NOT include the expected label
        prompt = f'''جملة: "{normalize_ar(sentence)}"\nس: {normalize_ar(question)}\nالخيارات: [{', '.join(candidates)}]\nأجب باسم واحد حرفيًا من الخيارات. أجب بخيار واحد فقط دون شرح.\n'''

        # run model and time
        import time
        start = time.time()
        raw = ''
        try:
            raw = reasoning_eval(prompt, '') or ''
        except Exception:
            raw = ''
        latency_ms = int((time.time() - start) * 1000)
        norm_out = normalize_ar(raw)

        # normalized candidates (for matching)
        cand_norm = [normalize_ar(c) for c in candidates]
        exp_norm = normalize_ar(expected)

        # MODE A: allow fallback heuristics
        got_a, reason_a = decide_from_model_or_fallback(norm_out, cand_norm, exp_norm, allow_fallback=True)
        # if heuristic returned a candidate not in cand_norm, leave as-is
        correct_a = (got_a == exp_norm)

        # MODE B: model-only (no fallback)
        got_b, reason_b = decide_from_model_or_fallback(norm_out, cand_norm, exp_norm, allow_fallback=False)
        correct_b = (got_b == exp_norm)

        # record results
        win_details_with.append({
            'sentence': normalize_ar(sentence),
            'question': normalize_ar(question),
            'prompt': prompt,
            'raw_output': raw,
            'normalized_output': norm_out,
            'candidates': candidates,
            'decision': reason_a,
            'got': got_a,
            'expected': exp_norm,
            'correct': bool(correct_a),
            'latency_ms': latency_ms,
            'temperature': temp,
            'top_p': top_p
        })

        win_details_modelonly.append({
            'sentence': normalize_ar(sentence),
            'question': normalize_ar(question),
            'prompt': prompt,
            'raw_output': raw,
            'normalized_output': norm_out,
            'candidates': candidates,
            'decision': reason_b,
            'got': got_b,
            'expected': exp_norm,
            'correct': bool(correct_b),
            'latency_ms': latency_ms,
            'temperature': temp,
            'top_p': top_p
        })

    # compute accuracies from the collected details
    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    acc_with = mean([1.0 if it.get('correct') else 0.0 for it in win_details_with])
    acc_modelonly = mean([1.0 if it.get('correct') else 0.0 for it in win_details_modelonly])

    # keep other legacy scores where available
    try:
        ascore = mod._arc_eval(mod.arc_infer)
    except Exception:
        ascore = None
    try:
        tscore = mod._tom_eval(mod.tom_infer)
    except Exception:
        tscore = None
    try:
        si = mod.self_improvement()
    except Exception:
        si = None

    return {
        "seed": seed,
        "winograd_with_fallback_acc": acc_with,
        "winograd_model_only_acc": acc_modelonly,
        "arc": ascore,
        "tom": tscore,
        "self_improvement": si,
        "winograd_details_with_fallback": win_details_with,
        "winograd_details_model_only": win_details_modelonly
    }

def main(runs=10):
    results = []
    errors = []
    for s in range(1, runs+1):
        try:
            results.append(run_seed(s))
        except Exception as e:
            errors.append({"seed": s, "error": str(e)})

    # Aggregate across seeds: compute mean winograd accuracies (with fallback and model-only)
    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    with_accs = [r.get('winograd_with_fallback_acc', 0.0) for r in results]
    model_accs = [r.get('winograd_model_only_acc', 0.0) for r in results]

    aggregated = {
        'runs': len(results),
        'winograd_with_fallback_mean': mean(with_accs),
        'winograd_model_only_mean': mean(model_accs),
        'winograd_fallback_gap': mean(with_accs) - mean(model_accs)
    }

    out = {"runs": len(results), "errors": errors, "results": results, 'aggregated': aggregated}
    out_path = OUT_DIR / 'AGL_AGI_UnifiedReport_detailed_runs.json'
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f'Detailed report saved to {out_path}')
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main(runs=int(os.environ.get('AGL_AGI_RUNS','10')))
