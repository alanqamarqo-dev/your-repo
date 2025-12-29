#!/usr/bin/env python3
import sys
import os
import time
import json
import argparse
from datetime import datetime

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from Learning_System.Feedback_Analyzer import FeedbackAnalyzer
    from Learning_System.Improvement_Generator import ImprovementGenerator
    # الاستيراد من الوحدة المحدثة للـ Rollback
    from Safety_Systems.Rollback_Mechanism import RollbackMechanism
    print(">> [Night Cycle] Modules loaded successfully.")
except ImportError as e:
    print(f">> [Night Cycle] Import Error: {e}")
    sys.exit(1)

# إعداد الـ Arguments
parser = argparse.ArgumentParser(description='AGL Night Cycle')
parser.add_argument('--dry-run', action='store_true', help='Simulate changes without writing to disk')
args = parser.parse_args()

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'daily_memories.json')
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs', 'fusion_weights.json')

def digest_memories():
    """قراءة وتحليل الذكريات"""
    if not os.path.exists(MEMORY_FILE):
        return None
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            memories = json.load(f)
    except Exception:
        return None
    if not memories: return None
    
    # تحليل بسيط
    agi_usage = sum(1 for m in memories if 'AGI' in str(m.get('engine', '')))
    
    real_record = {
        'timestamp': time.time(),
        'engine_outputs': {
            'mathematical_brain': {'confidence': 0.6 if agi_usage > 0 else 0.1},
            'quantum_processor': {'confidence': 0.5},
            'code_generator': {'confidence': 0.5}, 
            'protocol_designer': {'confidence': 0.5}
        },
        'final_decision': 'approved',
        'user_feedback': 'neutral'
    }
    return real_record

def apply_improvements_safely(plan):
    """تطبيق التحسينات مع شبكة أمان كاملة"""
    new_weights = plan.get('fusion_weights', {})
    if not new_weights:
        print(">> [System] No weight changes in plan.")
        return

    # 1. وضع Dry-Run
    if args.dry_run:
        print("\n=== 🚧 DRY RUN MODE ACTIVE 🚧 ===")
        print(f">> [Dry-Run] Target: {CONFIG_FILE}")
        print(f">> [Dry-Run] Validation Check: Passing (Simulated)")
        print(f">> [Dry-Run] New Weights: {json.dumps(new_weights, ensure_ascii=False)}")
        print(">> [Dry-Run] 🛡️ No files were touched.")
        archive_report(plan)
        return

    # 2. تهيئة نظام التراجع
    safety = RollbackMechanism(CONFIG_FILE)
    
    # 3. التحقق (Validation)
    if not safety.validate_fusion_schema(new_weights):
        print(">> [System] ⛔ STOP: Generated weights failed validation! Aborting.")
        return

    # 4. النسخ الاحتياطي (Backup)
    if not safety.create_restore_point():
        print(">> [System] ⚠️ Warning: Could not create backup. Aborting for safety.")
        return
    
    # 5. الكتابة ومحاولة التطبيق
    try:
        print(f">> [System] Writing new weights to disk...")
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_weights, f, indent=4, ensure_ascii=False)

        print(">> [System] ✅ Success: Configuration updated.")

        # --- المرحلة 5: فحص النبض (Health Check) ---
        print("\n🏥 [Health Check] Verifying system integrity after mutation...")
        try:
            # اختبار صحة JSON وبنوده الحرجة
            with open(CONFIG_FILE, 'r', encoding='utf-8') as hf:
                loaded = json.load(hf)

            # تحقق بسيط: وجود مفتاح حرج في التكوين
            if 'mathematical_brain' not in loaded:
                raise ValueError("Critical keys missing in new config!")

            print("✅ [Pulse] System is beating normally. Changes committed.")

        except Exception as he:
            print(f"💔 [Critical] Post-update check failed: {he}")
            print("🚑 [Emergency] Triggering Auto-Rollback...")

            # حاول استعادة عبر آلية التراجع المرفقة، وإلا قم بنسخ .bak يدوياً
            try:
                restore_func = getattr(safety, 'restore', None)
                if callable(restore_func):
                    restore_func()
                    print(">> [Rollback] System restored via RollbackMechanism.restore().")
                else:
                    import shutil
                    bak_path = CONFIG_FILE + '.bak'
                    if os.path.exists(bak_path):
                        shutil.copy(bak_path, CONFIG_FILE)
                        print(">> [Rollback] System restored to previous safe state (manual copy).")
                    else:
                        print("!! [Fatal] No backup found to restore.")
            except Exception as re:
                print(f"!! [Fatal] Rollback failed: {re}")

    except Exception as e:
        print(f">> [System] 💥 ERROR during write: {e}")
        try:
            safety.restore()
        except Exception:
            pass

    # أرشفة التقرير
    archive_report(plan)

def archive_report(plan):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    artifacts_dir = os.path.join(root_dir, 'artifacts', 'night_cycles')
    os.makedirs(artifacts_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(artifacts_dir, f'cycle_report_{timestamp}{"_dry" if args.dry_run else ""}.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=4, ensure_ascii=False)

def run_night_cycle():
    print(f"\n=== 🌙 STARTING AGI NIGHT CYCLE {'(DRY RUN)' if args.dry_run else ''} ===")

    # Pre-start integrity check: ensure current config file is parseable; if corrupted, restore from backup
    try:
        safety = RollbackMechanism(CONFIG_FILE)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as cf:
                    json.load(cf)
            except Exception as pre_e:
                print(f">> [Startup] ⚕️ Detected corrupted config: {pre_e}")
                print(">> [Startup] 🚑 Attempting emergency restore from backup before proceeding...")
                try:
                    restore_fn = getattr(safety, 'restore', None)
                    if callable(restore_fn):
                        restore_fn()
                        print(">> [Startup] ✅ Restored config via RollbackMechanism.restore().")
                    else:
                        import shutil
                        bak = CONFIG_FILE + '.bak'
                        if os.path.exists(bak):
                            shutil.copy(bak, CONFIG_FILE)
                            print(">> [Startup] ✅ Restored config via manual .bak copy.")
                        else:
                            print(">> [Startup] !! No backup found. Proceeding but expect failures.")
                except Exception as re2:
                    print(f">> [Startup] !! Emergency restore failed: {re2}")
    except Exception:
        # If RollbackMechanism import or init fails, continue but warn
        print(">> [Startup] ⚠️ Could not initialize RollbackMechanism for pre-start check.")

    # 1. الذاكرة
    run_record = digest_memories()
    if not run_record:
        print(">> [Memory] No new memories. Using cold-start.")
        run_record = {'timestamp': time.time(), 'engine_outputs': {}, 'user_feedback': 'negative'}

    # 2. التحليل
    analyzer = FeedbackAnalyzer()
    analysis_report = analyzer.analyze_performance_feedback(run_record)
    
    # 3. التوليد
    generator = ImprovementGenerator()
    improvement_plan = generator.generate_targeted_improvements(analysis_report)
    
    print("\n=== 🚀 IMPROVEMENT PLAN ===")
    print(improvement_plan)
    
    # 4. التطبيق الآمن
    apply_improvements_safely(improvement_plan)
    
    print("\n=== ☀️ NIGHT CYCLE COMPLETE ===")

if __name__ == "__main__":
    run_night_cycle()
