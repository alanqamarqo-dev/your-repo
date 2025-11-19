#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect what the unified AGI test's evaluators returned for each question.
This is a small helper (non-invasive) to run alongside the existing test file.
"""
import importlib.util, json, os

mod_path = os.path.join(os.path.dirname(__file__), 'AGL_AGI_UnifiedTest.py')
spec = importlib.util.spec_from_file_location('agl_unified', mod_path)
mod = importlib.util.module_from_spec(spec) # type: ignore
spec.loader.exec_module(mod) # type: ignore

out = {
    'winograd_answers': [],
    'arc_answers': [],
    'tom_answers': []
}

for s,q,ans in mod.WINOGRAD:
    got = mod.reasoning_eval(s, q)
    out['winograd_answers'].append({'prompt': s, 'question': q, 'expected': ans, 'got': got})

for name, seq, y in mod.ARC:
    got = mod.arc_infer(seq)
    out['arc_answers'].append({'name': name, 'seq': seq, 'expected': y, 'got': got})

for story, ans in mod.TOM:
    got = mod.tom_infer(story)
    out['tom_answers'].append({'story': story, 'expected': ans, 'got': got})

print(json.dumps(out, ensure_ascii=False, indent=2))
