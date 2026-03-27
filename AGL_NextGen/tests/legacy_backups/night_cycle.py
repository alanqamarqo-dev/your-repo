
import asyncio
import sys
import os
import time
import json
from datetime import datetime

# إضافة المسار الحالي للمكتبات
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# محاولة استيراد النظام الموحد
try:
    from repo_copy.dynamic_modules.unified_agi_system import create_unified_agi_system # pyright: ignore[reportMissingImports]
    from repo_copy.Core_Engines import bootstrap_register_all_engines # type: ignore
except ImportError:
    # Fallback paths
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'repo-copy'))
    from dynamic_modules.unified_agi_system import create_unified_agi_system
    from Core_Engines import bootstrap_register_all_engines

try:
    from repo_copy.Core_Engines.Dreaming_Cycle import DreamingEngine # type: ignore
except ImportError:
    from Core_Engines.Dreaming_Cycle import DreamingEngine

async def run_night_cycle(duration_minutes=5):
    print(f"🌙 Starting AGL Night Cycle (Dreaming Mode)...")
    print(f"⏱️  Duration: {duration_minutes} minutes")
    
    # Initialize Dreaming Engine
    dreaming_engine = DreamingEngine()
    
    # 1. تهيئة النظام
    registry = {}
    print("   - Bootstrapping engines...")
    bootstrap_register_all_engines(registry, allow_optional=True, verbose=False)
    
    print("   - Initializing Unified AGI System...")
    agi_system = create_unified_agi_system(registry)
    
    # 2. بدء دورة الاستقلال الذاتي (Autonomous Cycle)
    print("   - Entering autonomous state...")
    start_time = time.time()
    
    # تشغيل الدورة المستقلة
    cycle_count = 0
    thoughts_log = []
    
    try:
        while (time.time() - start_time) < (duration_minutes * 60):
            cycle_count += 1
            remaining = (duration_minutes * 60) - (time.time() - start_time)
            print(f"\n💤 Cycle #{cycle_count} (Time remaining: {int(remaining)}s)")
            
            try:
                # تشغيل دورة قصيرة
                result = await agi_system.autonomous_cycle(duration_seconds=60)
                
                # تسجيل النتائج
                if result.get('log'):
                    for entry in result['log']:
                        goal_text = entry.get('goal', {}).get('goal', 'Exploring...')
                        res_text = str(entry.get('result', ''))
                        print(f"      💭 Thought: {goal_text}")
                        print(f"         Result: {res_text[:100]}...")
                        thoughts_log.append(entry)
                        
                        # Add to Dreaming Engine Buffer
                        dreaming_engine.add_to_buffer(f"Goal: {goal_text}, Result: {res_text}")
                        
                        # === Active Learning Injection ===
                        # محاولة تغذية النتائج للذاكرة الدلالية إذا كانت مفيدة
                        if len(res_text) > 20 and "error" not in res_text.lower():
                            print("      🧠 Consolidating memory...")
                            # إضافة للذاكرة (محاكاة التعلم)
                            if hasattr(agi_system, 'memory') and hasattr(agi_system.memory, 'add_memory'):
                                agi_system.memory.add_memory(
                                    content=f"Learned from night cycle: {goal_text} -> {res_text[:200]}",
                                    memory_type="semantic",
                                    importance=0.8
                                )
                            
                            # تحديث الوعي
                            if hasattr(agi_system, 'consciousness_tracker'):
                                agi_system.consciousness_tracker.update_consciousness(
                                    complexity=0.01, 
                                    integration=0.01
                                )
                                
            except Exception as e:
                print(f"      ❌ Error in cycle: {e}")
            
            # فترة راحة قصيرة
            await asyncio.sleep(2)
            
    except KeyboardInterrupt:
        print("\n⚠️ Night cycle interrupted by user.")
    
    # 3. Deep Sleep Consolidation
    print("\n🧠 Starting Deep Sleep Consolidation...")
    dream_results = dreaming_engine.run_dream_cycle(duration_seconds=120)
    
    # 4. حفظ تقرير الحلم
    print("\n🌅 Waking up...")
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration_minutes": duration_minutes,
        "cycles_completed": cycle_count,
        "consciousness_level_start": 0.15, 
        "consciousness_level_end": agi_system.consciousness_level,
        "thoughts": thoughts_log,
        "dream_consolidation": dream_results
    }
    
    filename = f"night_cycle_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Night cycle complete. Report saved to: {filename}")
    print(f"📈 Consciousness Level: {agi_system.consciousness_level:.4f}")

if __name__ == "__main__":
    duration = 1 
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except:
            pass
            
    asyncio.run(run_night_cycle(duration))
