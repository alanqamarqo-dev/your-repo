"""Rerun the 'impossible' questions through UnifiedAGISystem.

This script:
 - Reads `artifacts/unified_impossible_report.md`
 - Extracts code-blocks that contain the word 'سؤال:'
 - For each block, calls `UnifiedAGISystem.process_with_full_agi` and collects the result
 - Writes results to `artifacts/unified_impossible_rerun_results.json` and a Markdown summary

Designed to be robust when optional subsystems are missing.
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
import importlib.util
from datetime import datetime


BASE = Path(__file__).resolve().parents[1]
REPORT_MD = BASE / 'artifacts' / 'unified_impossible_report.md'
OUT_JSON = BASE / 'artifacts' / 'unified_impossible_rerun_results.json'
OUT_MD = BASE / 'artifacts' / 'unified_impossible_rerun_summary.md'


def load_unified_module():
    fp = BASE / 'repo-copy' / 'dynamic_modules' / 'unified_agi_system.py'
    spec = importlib.util.spec_from_file_location('unified_agi_system', str(fp))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def extract_question_blocks(md_text: str):
    parts = md_text.split('```')
    blocks = []
    # triple-backtick blocks are in odd indices
    for i in range(1, len(parts), 2):
        block = parts[i].strip()
        if 'سؤال:' in block or 'سual' in block:
            blocks.append(block)
    return blocks


async def run_block(system, text: str):
    try:
        res = await system.process_with_full_agi(text)
        return {'ok': True, 'result': res}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def main():
    if not REPORT_MD.exists():
        print('Report not found:', REPORT_MD)
        return 2

    md = REPORT_MD.read_text(encoding='utf-8', errors='ignore')
    blocks = extract_question_blocks(md)
    if not blocks:
        print('No question blocks found in report.')
        return 1

    print(f'Found {len(blocks)} question blocks — will rerun them.')

    # load unified module and create system
    mod = load_unified_module()
    create_fn = getattr(mod, 'create_unified_agi_system', None)
    if create_fn is None:
        print('create_unified_agi_system not found in module')
        return 3

    system = create_fn(engine_registry={})

    results = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        for i, blk in enumerate(blocks, start=1):
            print(f'[{i}/{len(blocks)}] Running question block (len={len(blk)} chars)')
            start = time.time()
            out = loop.run_until_complete(run_block(system, blk))
            duration = time.time() - start
            out_record = {
                'index': i,
                'text_preview': blk[:300],
                'duration_seconds': duration,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'output': out
            }
            results.append(out_record)

    finally:
        try:
            loop.close()
        except Exception:
            pass

    # write JSON
    try:
        OUT_JSON.write_text(json.dumps({'generated_at': datetime.utcnow().isoformat() + 'Z', 'results': results}, indent=2, ensure_ascii=False), encoding='utf-8')
        print('Wrote JSON results to', OUT_JSON)
    except Exception as e:
        print('Failed to write JSON:', e)

    # write markdown summary
    lines = [f'# Rerun summary — {datetime.utcnow().isoformat()}Z\n']
    for r in results:
        lines.append(f"## Question #{r['index']} (duration: {r['duration_seconds']:.2f}s)")
        lines.append('\n```\n'+ r['text_preview'][:1000] + '\n```\n')
        out = r['output']
        if out.get('ok'):
            # include a short preview of final_response if available
            resp = out['result'].get('final_response') if isinstance(out['result'], dict) else None
            if resp:
                preview = str(resp)[:800]
                lines.append('**Final response (preview):**\n')
                lines.append('\n```\n' + preview + '\n```\n')
            else:
                # dump small dict preview
                lines.append('**Result keys:** ' + ', '.join(sorted(out['result'].keys())) + '\n')
        else:
            lines.append('**Error:** ' + out.get('error', 'unknown') + '\n')

    try:
        OUT_MD.write_text('\n'.join(lines), encoding='utf-8')
        print('Wrote Markdown summary to', OUT_MD)
    except Exception as e:
        print('Failed to write Markdown:', e)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
