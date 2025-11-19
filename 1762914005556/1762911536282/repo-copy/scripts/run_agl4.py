from __future__ import annotations
import subprocess, sys, os
from pathlib import Path
import json, time

# ensure repository root is on sys.path so 'infra' package imports work when
# running this script from the scripts/ directory or via 'py scripts\run_agl4.py'
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infra.adaptive.AdaptiveMemory import save_theory_items
from infra.adaptive.MetaController import tune_after_cycle
from infra.adaptive.EvolutionTracker import snapshot


def run_p(cmd):
    print(">", " ".join(cmd)); sys.stdout.flush()
    subprocess.run(cmd, check=True)


def main():
    Path("artifacts").mkdir(exist_ok=True)
    # 1) حصاد (يمكن إبقاءه mock/حي حسب متغيرات البيئة لديك)
    try:
        run_p([sys.executable, "workers/knowledge_harvester.py"])
    except subprocess.CalledProcessError as e:
        print("[agl4] harvest step failed, continuing in best-effort mode:", e)
    # 2) استدلال
    try:
        run_p([sys.executable, "workers/reasoning_cycle.py"])
    except subprocess.CalledProcessError as e:
        print("[agl4] reasoning step failed, continuing:", e)
    # 3) نظرية
    try:
        run_p([sys.executable, "tools/run_theory.py"])
    except subprocess.CalledProcessError as e:
        print("[agl4] run_theory failed:", e)

    # 4) حفظ أفضل عناصر النظرية في الذاكرة
    # respect configured thresholds from artifacts/agl4_config.json, but allow env overrides
    cfgp = Path("artifacts/agl4_config.json")
    min_conf = None
    min_coh = None
    if cfgp.exists():
        try:
            import json
            cfg = json.loads(cfgp.read_text(encoding='utf-8'))
            min_conf = float(cfg.get('theory', {}).get('min_conf_for_memory', 0.6))
            min_coh = float(cfg.get('theory', {}).get('min_coherence_for_memory', 0.6))
        except Exception:
            min_conf = 0.6; min_coh = 0.6

    # environment overrides (temporary, do not modify config file)
    try:
        v = os.getenv('AGL_FORCE_SAVE_MIN_CONF')
        if v is not None and v != '':
            min_conf = float(v)
        v2 = os.getenv('AGL_FORCE_SAVE_MIN_COH')
        if v2 is not None and v2 != '':
            min_coh = float(v2)
    except Exception:
        pass

    # allow disabling auto-tuning step after save (for experiments)
    do_auto_tune = os.getenv('AGL_AUTO_TUNE', '1') == '1'

    # capture existing ids to determine new additions
    mem_path = Path('artifacts/memory/long_term.jsonl')
    existing = set()
    if mem_path.exists():
        try:
            for ln in mem_path.read_text(encoding='utf-8').splitlines():
                try:
                    obj = json.loads(ln) # type: ignore
                    if 'id' in obj:
                        existing.add(obj['id'])
                except Exception:
                    continue
        except Exception:
            existing = set()

    saved = save_theory_items("artifacts/theory_bundle.json", min_conf=min_conf or 0.6, min_coherence=min_coh or 0.6)
    print(f"[agl4] memory saved items: {saved}")

    # write newly added records to artifacts/memory_added.jsonl for easy per-run auditing
    try:
        run_id = time.strftime("run_%Y%m%d_%H%M%S", time.gmtime())
        added_path = Path('artifacts/memory_added.jsonl')
        if mem_path.exists():
            new_lines = []
            for ln in mem_path.read_text(encoding='utf-8').splitlines():
                try:
                    obj = json.loads(ln) # type: ignore
                    if obj.get('id') not in existing:
                        obj['_run_id'] = run_id
                        obj['_run_ts'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                        new_lines.append(json.dumps(obj, ensure_ascii=False)) # type: ignore
                except Exception:
                    continue
            if new_lines:
                added_path.parent.mkdir(parents=True, exist_ok=True)
                with added_path.open('a', encoding='utf-8') as af:
                    af.write('\n'.join(new_lines) + '\n')
    except Exception:
        pass
    # 5) ضبط تلقائي للمعاملات (قابل للتعطيل عبر AGL_AUTO_TUNE=0)
    if do_auto_tune:
        new_cfg = tune_after_cycle()
        print("[agl4] tuned config:", new_cfg)
    else:
        print("[agl4] auto-tune disabled for this run (AGL_AUTO_TUNE=0)")
    # 6) لقطـة تطور
    snapshot(run_tag="agl4_cycle")


if __name__ == "__main__":
    main()
