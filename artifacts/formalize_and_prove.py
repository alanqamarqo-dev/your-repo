"""formalize_and_prove.py
Reads `unified_impossible_results.json`, extracts hypotheses,
asks the repo's AutomatedTheoremProver to attempt proofs, and
writes results to JSON and a short Markdown summary.

Run from PowerShell: `python .\artifacts\formalize_and_prove.py`
"""
import json
import re
from pathlib import Path

REPO_COPY = Path(__file__).resolve().parents[1] / "repo-copy"
ARTIFACTS = Path(__file__).resolve().parents[0]

INPUT = ARTIFACTS / "unified_impossible_results.json"
OUT_JSON = ARTIFACTS / "unified_impossible_formal_proofs.json"
OUT_MD = ARTIFACTS / "unified_impossible_formal_proofs.md"


def try_extract_json(s: str):
    """Try to find a JSON object inside a string (best-effort).
    Returns parsed JSON or None."""
    if not isinstance(s, str):
        return None
    s = s.strip()
    # direct parse
    try:
        return json.loads(s)
    except Exception:
        pass

    # attempt to find a JSON block that contains "hypothesis"
    m = re.search(r"\{.*\"hypothesis\".*\}", s, flags=re.S)
    if m:
        candidate = m.group(0)
        try:
            return json.loads(candidate)
        except Exception:
            # try to fix trailing commas / newlines by simple cleanup
            fixed = re.sub(r",\s*\}", "}", candidate)
            try:
                return json.loads(fixed)
            except Exception:
                return None

    return None


def main():
    if not INPUT.exists():
        print(f"Input not found: {INPUT}")
        return

    data = json.loads(INPUT.read_text(encoding="utf-8"))

    # import the prover from repo-copy
    import sys
    sys.path.insert(0, str(REPO_COPY))
    try:
        from Scientific_Systems.Automated_Theorem_Prover import AutomatedTheoremProver
    except Exception as e:
        print(f"Failed to import AutomatedTheoremProver: {e}")
        return

    prover = AutomatedTheoremProver()

    results = []

    # data may be a list of entries or a dict with 'results'
    entries = data if isinstance(data, list) else data.get('results') or data.get('entries') or [data]

    for idx, entry in enumerate(entries, start=1):
        entry_output = None
        # try common places
        for key in ("output", "final_response", "response", "result", "answer"):
            if isinstance(entry, dict) and key in entry:
                entry_output = entry[key]
                break

        if entry_output is None and isinstance(entry, str):
            entry_output = entry

        parsed = try_extract_json(entry_output) if entry_output else None

        hypotheses = []
        if parsed and isinstance(parsed, dict) and 'hypothesis' in parsed:
            hy = parsed.get('hypothesis')
            if isinstance(hy, list):
                hypotheses = hy
        else:
            # fallback: try to find simple "Hypothesis: ..." lines
            if isinstance(entry_output, str):
                found = re.findall(r"(?i)hypothesis\s*[:\-]\s*(.+)$", entry_output, flags=re.M)
                for f in found:
                    hypotheses.append({'hypothesis': f.strip(), 'reasoning': None})

        if not hypotheses:
            # nothing to prove for this entry
            results.append({'index': idx, 'note': 'no_hypotheses_found'})
            continue

        item_results = {'index': idx, 'hypotheses': []}
        for h in hypotheses[:5]:
            statement = None
            if isinstance(h, dict):
                statement = h.get('hypothesis') or h.get('statement') or str(h)
            else:
                statement = str(h)

            statement = (statement or '').strip()
            if not statement:
                item_results['hypotheses'].append({'statement': None, 'error': 'empty'})
                continue

            try:
                proof = prover.prove_theorem(statement, assumptions=[])
            except Exception as e:
                item_results['hypotheses'].append({'statement': statement, 'error': str(e)})
                continue

            item_results['hypotheses'].append({'statement': statement, 'proof': proof})

        results.append(item_results)

    # write JSON
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    # write a short markdown summary
    with OUT_MD.open('w', encoding='utf-8') as f:
        f.write('# Formal Proof Attempts\n\n')
        for r in results:
            f.write(f"## Question {r.get('index')}\n")
            if r.get('note'):
                f.write(f"- Note: {r.get('note')}\n\n")
                continue
            for h in r.get('hypotheses', []):
                stmt = h.get('statement')
                if not stmt:
                    f.write('- Empty hypothesis\n')
                    continue
                prov = h.get('proof') or {}
                is_proven = prov.get('is_proven') if isinstance(prov, dict) else None
                f.write(f"- Hypothesis: `{stmt}`\n")
                f.write(f"  - Proven: {is_proven}\n")
                steps = (prov.get('proof_steps') if isinstance(prov, dict) else None) or []
                if steps:
                    f.write(f"  - Steps: {len(steps)} steps (showing up to 3)\n")
                    for s in steps[:3]:
                        content = s.get('content') if isinstance(s, dict) else str(s)
                        f.write(f"    - {content}\n")
                else:
                    f.write('  - Steps: none\n')
            f.write('\n')

    print(f"Done. Results: {OUT_JSON} and {OUT_MD}")


if __name__ == '__main__':
    main()
