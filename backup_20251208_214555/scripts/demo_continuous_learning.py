#!/usr/bin/env python3
"""
repo-copy/scripts/demo_continuous_learning.py
Lightweight demo that exercises MetaLearning and SelfLearningManager using
synthetic tasks. Writes artifacts/learning_curve_demo.json and artifacts/demo_results.json
"""
from __future__ import annotations

import json
import time
import os
from datetime import datetime
from pathlib import Path
import sys

# ensure repo-copy root on sys.path when executed from repo root
HERE = Path(__file__).resolve()
REPO_COPY_ROOT = HERE.parent.parent
if str(REPO_COPY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_COPY_ROOT))


def demo_meta_learning():
    print("🧠 Starting meta-learning demo...")
    try:
        from Core_Engines.Meta_Learning import MetaLearningEngine

        meta = MetaLearningEngine()

        synthetic_tasks = [
            {"task": "solve_linear", "input": "2x + 5 = 15", "output": "x = 5", "domain": "mathematics"},
            {"task": "arabic_text_analysis", "input": "النصوص العربية تحتاج إلى معالجة خاصة", "output": "تحليل نحوي وإعرابي كامل", "domain": "nlp_arabic"},
            {"task": "design_algo", "input": "sort large array", "output": "quicksort with optimizations", "domain": "programming"},
        ]

        learning_history = []

        for i, task in enumerate(synthetic_tasks):
            print(f"\n📚 Learning from task {i+1}: {task['task']}")
            # adapt example format expected by continual_self_learning
            examples = [ (task['input'], task['output']) ]
            result = meta.continual_self_learning(skill_id=task['task'], example_batches=[examples], rounds=3, eval_holdout=examples, lr=0.1)
            learning_history.append({"task": task['task'], "principles_learned": list(meta.list_principles()), "history": result})
            print(f"   ✅ Learned principles: {len(list(meta.list_principles()))}")
            time.sleep(0.2)

        learning_curve = {
            "demo_timestamp": datetime.now().isoformat(),
            "total_tasks": len(synthetic_tasks),
            "learning_history": learning_history,
            "summary": {"total_principles": sum(len(h['principles_learned']) for h in learning_history)}
        }

        Path("artifacts").mkdir(exist_ok=True)
        with open("artifacts/learning_curve_demo.json", "w", encoding="utf-8") as f:
            json.dump(learning_curve, f, ensure_ascii=False, indent=2)

        print(f"\n📈 Saved learning curve to artifacts/learning_curve_demo.json")
        return learning_curve
    except Exception as e:
        print(f"❌ Meta-learning import or run error: {e}")
        return None


def demo_transfer_learning():
    print("\n🔄 Starting transfer demo...")
    try:
        from Core_Engines.Meta_Learning import MetaLearningEngine
        meta = MetaLearningEngine()

        # prepare some principles to transfer
        principles = [
            {"id": "p1", "principle": "use abstract variables", "confidence": 0.8, "desc": "use abstract variables"},
            {"id": "p2", "principle": "stepwise solve", "confidence": 0.9, "desc": "solve step by step"},
        ]

        # map p1->p1_copy simulated
        mapping = {"p1": "p1_copy", "p2": "p2_copy"}
        res = meta.transfer_principles_between_domains(mapping)
        print(f"📤 Transferred {res.get('count',0)} principles")
        return res
    except Exception as e:
        print(f"❌ transfer error: {e}")
        return {}


def demo_self_improvement():
    print("\n⚡ Starting self-improvement demo...")
    try:
        import os
        os.environ['AGL_SELF_LEARNING_ENABLE'] = '1'
        os.environ['AGL_SELF_LEARNING_LOGDIR'] = 'learning_logs'
        from Self_Improvement.Self_Improvement_Engine import SelfLearningManager

        Path('learning_logs').mkdir(exist_ok=True)
        manager = SelfLearningManager()
        print("🏋️ Running one training epoch...")
        results = manager.run_training_epoch()
        print(f"📊 Training results: {results}")

        # attempt to read latest snapshot if present
        latest = None
        runs = Path('artifacts') / 'self_runs'
        if runs.exists():
            files = sorted([p for p in runs.iterdir() if p.is_file()], reverse=True)
            if files:
                latest = files[0]
        if latest:
            print(f"   - Latest snapshot: {latest}")

        return results
    except Exception as e:
        print(f"❌ self-improvement error: {e}")
        return {}


def run_full_demo():
    print("=" * 60)
    print("🧪 Continuous learning demo for AGL")
    print("=" * 60)

    results = {}
    results['meta_learning'] = demo_meta_learning()
    results['transfer_learning'] = demo_transfer_learning()
    results['self_improvement'] = demo_self_improvement()

    successful = sum(1 for k, v in results.items() if v)
    total = len(results)

    final_report = {
        "demo_completed": datetime.now().isoformat(),
        "results_summary": {"meta_learning": bool(results['meta_learning']), "transfer_learning": bool(results['transfer_learning']), "self_improvement": bool(results['self_improvement'])},
        "success_rate": f"{successful}/{total}"
    }
    Path('artifacts').mkdir(exist_ok=True)
    with open('artifacts/demo_results.json', 'w', encoding='utf-8') as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Saved results to artifacts/demo_results.json")
    return results


if __name__ == '__main__':
    run_full_demo()
