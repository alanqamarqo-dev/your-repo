# -*- coding: utf-8 -*-
"""
Run full pipeline: enable external info provider, fetch facts for the multi-domain follow-up prompt,
invoke core engines (SocialInteraction, StrategicThinking, CreativeInnovation, GeneralKnowledge),
aggregate outputs, recompute social score, and save a combined report.

This script is non-invasive: it does not modify existing tests or change prompts; it
orchestrates the available engines and knowledge base to produce a richer, aggregated
answer for analysis.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import importlib
from pprint import pformat


OUT = Path('artifacts/reports/multi_domain_full_pipeline.json')
OUT.parent.mkdir(parents=True, exist_ok=True)

# env-driven evidence limit (keep default behavior)
_AGL_EVIDENCE_LIMIT = int(os.environ.get('AGL_EVIDENCE_LIMIT', '3'))


def safe_import(name: str):
    try:
        return importlib.import_module(name)
    except Exception as e:
        return None


def ensure_provider():
    # Try to instantiate ExternalInfoProvider; if fails due to missing API key, enable mock mode
    try:
        from Core_Engines.External_InfoProvider import ExternalInfoProvider
    except Exception as e:
        return None, f'import_failed: {e}'
    try:
        prov = ExternalInfoProvider()
        return prov, None
    except Exception as e:
        # enable mock and retry
        os.environ['AGL_EXTERNAL_INFO_MOCK'] = '1'
        try:
            prov = ExternalInfoProvider()
            return prov, 'mock_enabled'
        except Exception as e2:
            return None, f'init_failed: {e2}'


def assemble_context(facts):
    # facts is list of dicts with 'text' and 'source'
    if not facts:
        return []
    ctx = []
    for f in facts:
        t = f.get('text') if isinstance(f, dict) else None
        if not t and isinstance(f, (list, tuple)) and len(f) > 1:
            t = f[1]
        if t:
            ctx.append(t)
    return ctx


def main():
    print('Running full pipeline...')

    # import the follow-up prompt from scripts.multi_domain_followup if available
    md = safe_import('scripts.multi_domain_followup')
    PROMPT = getattr(md, 'PROMPT', None) if md else None
    if not PROMPT:
        # fallback: short default
        PROMPT = "أعد إجابة موسعة ومنفّذة حول: 'صمم حلًا مبتكرًا لمشكلة ازدحام المرور في مدينة كبرى'"

    prov, perr = ensure_provider()
    provider_res = {'ok': False, 'error': 'no_provider'}
    if prov:
        try:
            provider_res = prov.fetch_facts(PROMPT, hints=['implementation','policy','costing','social'])
        except Exception as e:
            provider_res = {'ok': False, 'error': str(e)}
    else:
        provider_res = {'ok': False, 'error': perr}

    answer = provider_res.get('answer') if provider_res.get('ok') else None
    facts = provider_res.get('facts') or []

    # instantiate engines where available
    engines_out = {}

    # SocialInteractionEngine
    try:
        from Core_Engines.Social_Interaction import SocialInteractionEngine
        sie = SocialInteractionEngine()
        social_cues = sie.analyze_social_cues(answer or '')
        engines_out['social'] = {'cues': social_cues, 'empathic_reply': sie.empathic_reply(answer or '')}
    except Exception as e:
        engines_out['social'] = {'error': str(e)}

    # StrategicThinkingEngine
    try:
        from Core_Engines.Strategic_Thinking import StrategicThinkingEngine
        ste = StrategicThinkingEngine()
        roadmap = ste.roadmap('Reduce city traffic congestion', horizons=(30,90,365))
        scenarios = ste.scenario_analysis('Traffic congestion', ('demand', ['low','high']), ('infrastructure', ['low','high']))
        engines_out['strategic'] = {'roadmap': roadmap, 'scenarios': scenarios}
    except Exception as e:
        engines_out['strategic'] = {'error': str(e)}

    # CreativeInnovationEngine
    try:
        from Core_Engines.Creative_Innovation import CreativeInnovationEngine
        cie = CreativeInnovationEngine(seed=42)
        ideas = cie.generate_ideas("حل مشكلة ازدحام المرور في مدينة كبرى", n=5, constraints={'sustainability': True})
        engines_out['creative'] = {'ideas': ideas}
    except Exception as e:
        engines_out['creative'] = {'error': str(e)}

    # GeneralKnowledgeEngine
    try:
        from Core_Engines.General_Knowledge import GeneralKnowledgeEngine
        gke = GeneralKnowledgeEngine()
        gk_answer = gke.ask("أهم الأساليب المثبتة تقنياً لتخفيف ازدحام المرور في المدن", context=assemble_context(facts))
        engines_out['general_knowledge'] = gk_answer
    except Exception as e:
        engines_out['general_knowledge'] = {'error': str(e)}

    # Recompute social score using same heuristic as postprocess (lightweight)
    social_score = 0
    try:
        # reuse the postprocess logic if available
        pp = safe_import('scripts.postprocess_social_analysis')
        if pp and hasattr(pp, 'recompute_social_score'):
            social_score = pp.recompute_social_score(answer or '', engines_out.get('social', {}))
        else:
            # simple fallback: count keywords
            kws = ['القبول', 'مشاركة', 'عدالة', 'stakeholders', 'community']
            low = (answer or '').lower()
            hits = sum(1 for k in kws if k in low)
            social_score = min(20, hits * 4)
    except Exception:
        social_score = 0

    # assemble final combined 'synthesis' text (non-destructive: don't overwrite provider answer)
    synthesis = {
        'provider_answer': answer,
        'provider_ok': provider_res.get('ok', False),
        'provider_error': provider_res.get('error'),
        'facts_count': len(facts),
        'facts_sample': [ (f.get('source'), f.get('text')[:200]) for f in facts[:_AGL_EVIDENCE_LIMIT] ] if isinstance(facts, list) else [],
        'engines': engines_out,
        'social_score_via_engines': social_score
    }

    # compute an overall final percentage similar to previous scoring (best-effort)
    # start from existing scores if provider produced them via multi_domain_followup scoring
    base_scores = {}
    try:
        # try to load existing report to reuse other domain scores
        prev = Path('artifacts/reports/multi_domain_followup.json')
        if prev.exists():
            base_scores = json.load(prev.open('r', encoding='utf-8')).get('scores', {})
    except Exception:
        base_scores = {}

    creativity = base_scores.get('creativity', 0) or 0
    scientific = base_scores.get('scientific', 0) or 0
    economic = base_scores.get('economic', 0) or 0
    environmental = base_scores.get('environmental', 0) or 0
    bonus = base_scores.get('bonus', 0) or 0

    final = creativity + scientific + max(base_scores.get('social', 0) or 0, social_score) + economic + environmental + bonus
    pct = (final / 100.0) * 100.0

    report = {'synthesis': synthesis, 'final_percentage_with_engines': pct, 'final_components': {'creativity': creativity, 'scientific': scientific, 'social': max(base_scores.get('social', 0) or 0, social_score), 'economic': economic, 'environmental': environmental, 'bonus': bonus}}

    with OUT.open('w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print('Wrote full pipeline report to', OUT)
    print('Final percentage with engines:', f'{pct:.1f}%')


if __name__ == '__main__':
    main()
