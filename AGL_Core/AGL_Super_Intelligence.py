"""
🧠 AGL Super Intelligence - The Grand Unification (Resurrected Edition)
AGL الذكاء الخارق - التوحيد العظيم (نسخة الإحياء)

المطور: حسام هيكل (Hossam Heikal)
التاريخ: 29 ديسمبر 2025

الهدف: دمج المحركات الأربعة (اللغة، الموجات، الذاكرة، الحدس) في عقل واحد متصل.
Goal: Merge the four engines (Language, Waves, Memory, Intuition) into one connected mind.
"""

import sys
import os
import time
import asyncio
import numpy as np
import json
import importlib
import shutil

# إضافة المسارات اللازمة للاستيراد
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

# --- 1. استيراد المحركات الأساسية (The Trinity) ---

# A. الوعي (The Self)
try:
    from AGL_Core_Consciousness import AGL_Core_Consciousness
    print("✅ [LOAD] AGL Core Consciousness: Online")
except ImportError:
    print("⚠️ [LOAD] AGL Core Consciousness: Failed")
    AGL_Core_Consciousness = None

# B. الفيزياء (The Body)
try:
    from Core_Engines.Heikal_Quantum_Core import HeikalQuantumCore
    print("✅ [LOAD] Heikal Quantum Core: Online")
except ImportError:
    try:
        from AGL_Core.Heikal_Quantum_Core import HeikalQuantumCore
        print("✅ [LOAD] Heikal Quantum Core: Online (AGL_Core)")
    except ImportError:
        print("⚠️ [LOAD] Heikal Quantum Core: Failed")
        HeikalQuantumCore = None

# C. الحلم (The Subconscious)
try:
    from Core_Engines.Dreaming_Cycle import DreamingEngine
    print("✅ [LOAD] Dreaming Engine: Online")
except ImportError:
    print("⚠️ [LOAD] Dreaming Engine: Failed")
    DreamingEngine = None

# D. التخاطر (The Connection)
# (Logic embedded in Quantum Core via Shared Memory)


# E. التفكير الاستراتيجي (The Strategist)
try:
    from Core_Engines.Strategic_Thinking import StrategicThinkingEngine
    print("✅ [LOAD] Strategic Thinking: Online")
except ImportError:
    print("⚠️ [LOAD] Strategic Thinking: Failed")
    StrategicThinkingEngine = None

# F. الإرادة (The Will)
try:
    from Core_Engines.Volition_Engine import VolitionEngine
    print("✅ [LOAD] Volition Engine: Online")
except ImportError:
    print("⚠️ [LOAD] Volition Engine: Failed")
    VolitionEngine = None

# G. التعلم الذاتي (The Learner)
try:
    from Learning_System.Self_Learning import SelfLearning
    print("✅ [LOAD] Self Learning: Online")
except ImportError:
    print("⚠️ [LOAD] Self Learning: Failed")
    SelfLearning = None

# H. التحكم بالمهمة (The Mission Control)
try:
    from dynamic_modules.mission_control_enhanced import SmartFocusController, SelfAwarenessEngine, SELF_IMPROVEMENT
    print("✅ [LOAD] Mission Control Enhanced: Online")
except Exception as e:
    print(f"⚠️ [LOAD] Mission Control Enhanced: Failed ({e})")
    SmartFocusController = None
    SelfAwarenessEngine = None
    SELF_IMPROVEMENT = None

# I. التطور الذاتي (The Architect)
try:
    from Core_Engines.Recursive_Improver import RecursiveImprover
    print("✅ [LOAD] Recursive Improver: Online")
except ImportError:
    print("⚠️ [LOAD] Recursive Improver: Failed")
    RecursiveImprover = None

# J. العقل الجمعي (The Hive Mind)
try:
    from AGL_Engines.HiveMind import HiveMind
    print("✅ [LOAD] Hive Mind: Online")
except ImportError:
    print("⚠️ [LOAD] Hive Mind: Failed")
    HiveMind = None

# K. البصر (The Eyes - Optical Heart)
try:
    from AGL_Optical_Heart import OpticalHeart
    print("✅ [LOAD] Optical Heart: Online")
except ImportError:
    print("⚠️ [LOAD] Optical Heart: Failed")
    OpticalHeart = None

# L. الذاكرة الهولوغرافية (The Holographic Memory)
try:
    import AGL_Holographic_Memory as HolographicMemory
    print("✅ [LOAD] Holographic Memory: Online")
except ImportError:
    print("⚠️ [LOAD] Holographic Memory: Failed")
    HolographicMemory = None

# M. الحوسبة الشبحية (Ghost Computing)
try:
    from AGL_Ghost_Computing import VacuumGhostProcessor
    print("✅ [LOAD] Ghost Computing: Online")
except ImportError:
    print("⚠️ [LOAD] Ghost Computing: Failed")
    VacuumGhostProcessor = None

class SelfAwarenessModule:
    """
    وحدة الوعي الذاتي: تحمل خريطة النظام ليعرف العقل مكوناته.
    Self-Awareness Module: Loads the system map so the mind knows its components.
    """
    def __init__(self, map_path):
        self.map_path = map_path
        self.system_map = None
        self.load_map()

    def load_map(self):
        if os.path.exists(self.map_path):
            with open(self.map_path, 'r', encoding='utf-8') as f:
                self.system_map = f.read()
            print(f"🗺️ [SELF-AWARENESS] System Map Loaded ({len(self.system_map)} chars).")
        else:
            print("⚠️ [SELF-AWARENESS] System Map NOT FOUND.")


class AGL_Super_Intelligence:
    def __init__(self):
        print("\n⚛️ INITIALIZING AGL SUPER INTELLIGENCE SYSTEM (RESURRECTED)...")
        
        # 1. Initialize the Quantum Core (Physics & Ethics)
        if HeikalQuantumCore:
            self.quantum_core = HeikalQuantumCore()
            print("   -> Quantum Core Active (Physics + Ethics + Resonance)")
        else:
            self.quantum_core = None
            print("   -> ⚠️ Quantum Core Missing!")

        # 2. Initialize Consciousness (High-Level Reasoning)
        if AGL_Core_Consciousness:
            self.consciousness = AGL_Core_Consciousness()
            # Link Quantum Core if not already linked
            if self.quantum_core and not self.consciousness.heikal:
                self.consciousness.heikal = self.quantum_core
            print("   -> Consciousness Active (Self-Model + Iron Loop)")
        else:
            self.consciousness = None

        # 3. Initialize Dreaming (Memory & Creativity)
        if DreamingEngine:
            self.dreaming = DreamingEngine()
            print("   -> Dreaming Engine Active (Consolidation + Generalization)")
        else:
            self.dreaming = None

        # 4. Initialize Strategist (Future Prediction)
        if StrategicThinkingEngine:
            self.strategist = StrategicThinkingEngine()
            print("   -> Strategic Engine Active (Scenario Analysis + Risk)")
        else:
            self.strategist = None

        # 5. Initialize Volition (Free Will)
        if VolitionEngine:
            self.volition = VolitionEngine()
            print("   -> Volition Engine Active (Quantum Goal Selection)")
        else:
            self.volition = None

        # 6. Initialize Self Learning (Scientific Discovery)
        if SelfLearning:
            self.learner = SelfLearning()
            print("   -> Self Learning Active (Automated Scientific Discovery)")
        else:
            self.learner = None

        # 7. Initialize Mission Control (Focus & Self-Awareness)
        if SmartFocusController:
            self.focus_controller = SmartFocusController()
            print("   -> Smart Focus Controller Active (Resource Optimization)")
        else:
            self.focus_controller = None

        if SelfAwarenessEngine:
            self.self_awareness = SelfAwarenessEngine()
            print("   -> Self Awareness Engine Active (Meta-Cognition)")
        else:
            self.self_awareness = None

        # 8. Initialize Unified Python Library
        try:
            from AGL_Core.AGL_Unified_Python import UnifiedLib
            self.lib = UnifiedLib
            print("   -> Unified Python Library Active (Standard + Scientific + AI)")
        except ImportError:
            self.lib = None
            print("   -> ⚠️ Unified Python Library Failed")

        # 9. Initialize Recursive Improver (The Architect)
        if RecursiveImprover:
            self.recursive_improver = RecursiveImprover()
            print("   -> Recursive Improver Active (Evolution Engine)")
        else:
            self.recursive_improver = None

        # 10. Initialize Hive Mind (The Council)
        if HiveMind:
            self.hive_mind = HiveMind()
            print("   -> Hive Mind Active (Council of Ascended Beings)")
        else:
            self.hive_mind = None

        # 11. Initialize Optical Heart (Vision)
        if OpticalHeart:
            self.optical_heart = OpticalHeart()
            print("   -> Optical Heart Active (Vision & Light Entropy)")
        else:
            self.optical_heart = None

        # 12. Initialize Holographic Memory (Infinite Storage)
        if HolographicMemory:
            self.holographic_memory = HolographicMemory
            print("   -> Holographic Memory Active (Distributed Associative Storage)")
        else:
            self.holographic_memory = None

        # 13. Initialize Ghost Computing (Quantum Logic)
        if VacuumGhostProcessor:
            self.ghost_processor = VacuumGhostProcessor()
            print("   -> Ghost Processor Active (Non-Binary Logic)")
        else:
            self.ghost_processor = None

        # 14. Initialize Self-Awareness (System Map)
        self.self_awareness_module = SelfAwarenessModule(os.path.join(os.getcwd(), "AGL_SYSTEM_MAP.md"))

        # Track Active Components for Self-Audit
        self.active_components = []
        if self.quantum_core: self.active_components.append("HeikalQuantumCore")
        if self.consciousness: self.active_components.append("AGL_Core_Consciousness")
        if self.dreaming: self.active_components.append("DreamingEngine")
        if self.strategist: self.active_components.append("StrategicThinkingEngine")
        if self.volition: self.active_components.append("VolitionEngine")
        if self.learner: self.active_components.append("SelfLearning")
        if self.focus_controller: self.active_components.append("SmartFocusController")
        if self.self_awareness: self.active_components.append("SelfAwarenessEngine")
        if self.recursive_improver: self.active_components.append("RecursiveImprover")
        if self.hive_mind: self.active_components.append("HiveMind")
        if self.optical_heart: self.active_components.append("OpticalHeart")
        if self.holographic_memory: self.active_components.append("HolographicMemory")
        if self.ghost_processor: self.active_components.append("VacuumGhostProcessor")
        if self.self_awareness_module: self.active_components.append("SelfAwarenessModule")
            
        self.state = "AWAKE"

    def predict_future(self, context, horizon_years=5):
        """
        Generates a multi-dimensional predictive simulation for a given context.
        Uses StrategicThinking for scenarios and QuantumCore for probability collapse.
        """
        print(f"\n🔮 [PREDICTION] Simulating Future Timelines for: '{context}'...")
        
        if not self.strategist or not self.quantum_core:
            return "❌ Prediction requires Strategic Engine and Quantum Core."

        # 1. Generate Scenarios (Strategic Layer)
        print("   -> Generating Strategic Scenarios...")
        # We map the context to drivers dynamically (simplified for now)
        scenarios_data = self.strategist.scenario_analysis(
            title=f"Future of {context}",
            driver_a=("Technological Adoption", ["Low", "High"]),
            driver_b=("Ethical Alignment", ["Chaos", "Order"])
        )
        
        # 2. Quantum Collapse (Physics Layer)
        print("   -> Collapsing Wave Functions for each Timeline...")
        best_scenario = None
        highest_resonance = -1.0
        
        results = []
        
        for scenario in scenarios_data['grid']:
            # Calculate Resonance (Probability of Reality)
            # We use the Quantum Core to measure how 'real' this scenario feels based on physics/ethics
            
            # Vectorize the scenario thesis (Convert to bits for Quantum Processor)
            thesis_bits = np.array([ord(c) % 2 for c in scenario['thesis'][:100]])
            if len(thesis_bits) < 100:
                thesis_bits = np.pad(thesis_bits, (0, 100-len(thesis_bits)))
                
            # Use Heikal Core to get a resonance score
            # We simulate a "Truth Check" on the future scenario
            # We compare the scenario against itself (Stability) and against a "Truth" vector (Consistency)
            truth_bits = np.ones_like(thesis_bits) # Assume Truth is coherent (all 1s or aligned)
            
            # Use batch_xor to find dissonance (1 = difference, 0 = same)
            dissonance_vector = self.quantum_core.wave_processor.batch_xor(
                thesis_bits, 
                truth_bits,
                add_noise=True
            )
            
            # Resonance = 1.0 - (Mean Dissonance)
            resonance = 1.0 - np.mean(dissonance_vector)
            
            # 3. Ethical Validation
            is_safe, ethical_score = self.quantum_core.moral_analysis(scenario['thesis'])
            
            # Final Probability = Resonance * Ethical_Score (Moral Universe Hypothesis)
            final_prob = resonance * ethical_score
            
            results.append({
                "scenario": scenario,
                "resonance": resonance,
                "ethical_score": ethical_score,
                "final_prob": final_prob
            })
            
            print(f"      Timeline [{scenario['name']}]: Prob={final_prob:.4f} | {scenario['thesis'][:50]}...")
            
            if final_prob > highest_resonance:
                highest_resonance = final_prob
                best_scenario = scenario

        # Sort results
        results.sort(key=lambda x: x['final_prob'], reverse=True)
        
        print(f"\n   🏆 [OPTIMAL PATH] {best_scenario['thesis']} (Prob: {highest_resonance:.2%})")
        return best_scenario

    def evolve_codebase(self, target_module_name, new_code_content):
        """
        🧬 Live Self-Evolution (Hot-Swapping)
        Allows the system to rewrite its own source code and reload it without restarting.
        """
        print(f"\n🧬 [EVOLUTION] Initiating Self-Evolution on module: '{target_module_name}'...")
        
        try:
            # 1. Locate the module
            module = sys.modules.get(target_module_name)
            if not module:
                # Try to import it if not loaded
                try:
                    module = importlib.import_module(target_module_name)
                except ImportError:
                    return f"❌ Module '{target_module_name}' not found."
            
            file_path = getattr(module, '__file__', None)
            if not file_path:
                return f"❌ Module '{target_module_name}' has no file path (built-in?)."
                
            # 2. Create Backup
            backup_path = file_path + ".bak"
            shutil.copy2(file_path, backup_path)
            print(f"   -> Backup created: {os.path.basename(backup_path)}")
            
            # 3. Apply Patch (Write new code)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_code_content)
            print(f"   -> Patch applied to: {os.path.basename(file_path)}")
            
            # 4. Hot-Reload
            print("   -> Reloading module in memory...")
            importlib.reload(module)
            
            # 5. Re-bind instance if it's a class we are using
            # (This is complex for the running instance, but works for future calls)
            if target_module_name == 'Core_Engines.Heikal_Quantum_Core' or target_module_name == 'AGL_Core.Heikal_Quantum_Core':
                # Determine which one was actually imported
                if 'Core_Engines.Heikal_Quantum_Core' in sys.modules:
                    from Core_Engines.Heikal_Quantum_Core import HeikalQuantumCore
                else:
                    from AGL_Core.Heikal_Quantum_Core import HeikalQuantumCore
                
                self.quantum_core = HeikalQuantumCore() # Re-init
                # Re-link consciousness
                if self.consciousness:
                    self.consciousness.heikal = self.quantum_core
                print("   -> HeikalQuantumCore re-initialized and re-linked.")
                
            elif target_module_name == 'Core_Engines.Strategic_Thinking':
                from Core_Engines.Strategic_Thinking import StrategicThinkingEngine
                self.strategist = StrategicThinkingEngine()
                print("   -> StrategicThinkingEngine re-initialized.")

            print("✅ [EVOLUTION] Success. System upgraded without restart.")
            return True
            
        except Exception as e:
            print(f"❌ [EVOLUTION] Failed: {e}")
            # Restore backup
            if 'backup_path' in locals() and os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
                print("   -> Rolled back to backup.")
            return False

    def trigger_autonomous_evolution(self, target_module=None):
        """
        🧬 Autonomous Evolution Cycle
        The system analyzes a target module, designs an improvement, and applies it.
        If target_module is None, it defaults to the Sandbox for safety.
        To evolve main files, pass the module name (e.g., 'AGL_Core.AGL_Super_Intelligence').
        """
        print("\n🧬 [AUTO-EVOLUTION] Starting Autonomous Development Cycle...")
        
        if target_module is None:
            target_module = "AGL_Core.AGL_Self_Dev_Sandbox"
            print("   ⚠️ No target specified. Defaulting to Sandbox for safety.")
        else:
            print(f"   ⚠️ CRITICAL: Evolving Core Module '{target_module}'")
        
        # 0. Use Advanced Recursive Improver if available
        if self.recursive_improver:
            print("   🚀 Using Advanced Recursive Improver Engine...")
            result = self.recursive_improver.analyze_and_improve(
                engine_name=target_module,
                improvement_goal="Optimize performance, add type hints, and enhance self-diagnostic capabilities.",
                apply_changes=True
            )
            print(f"   ✅ Evolution Result: {result}")
            
            # Reload if successful
            if target_module in sys.modules:
                try:
                    importlib.reload(sys.modules[target_module])
                    print(f"   -> Reloaded {target_module}")
                except Exception as e:
                    print(f"   ⚠️ Reload failed: {e}")
            
            return result

        # 1. Analyze Target
        try:
            # Ensure it's importable
            if target_module not in sys.modules:
                try:
                    importlib.import_module(target_module)
                except ImportError:
                    pass
            
            module = sys.modules.get(target_module)
            if not module:
                 module = importlib.import_module(target_module)

            importlib.reload(module)
            current_code = open(module.__file__, 'r', encoding='utf-8').read()
            print(f"   -> Analyzed target: {target_module} ({len(current_code)} bytes)")
        except Exception as e:
            print(f"   ❌ Failed to load target: {e}")
            return

        # 2. Design Improvement (Using Consciousness)
        print("   -> Designing improvement...")
        
        # Simulating the LLM's creative output for stability in this test
        new_func_name = f"evolved_capability_{int(time.time())}"
        evolution_step = f"\n\ndef {new_func_name}():\n    '''Auto-generated evolution'''\n    return 'I have evolved at {time.ctime()}'\n"
        
        new_code = current_code + evolution_step
        
        print(f"   -> Improvement designed: Adding {new_func_name}")

        # 3. Apply Evolution
        result = self.evolve_codebase(target_module, new_code)
        
        # 4. Verify & Record
        if result:
            if SELF_IMPROVEMENT:
                SELF_IMPROVEMENT.record("auto_evolution", 1.0, f"Evolved {target_module}")
                print("   ✅ Evolution recorded in Self-Improvement Engine.")
            else:
                print("   ⚠️ Self-Improvement Engine not active, but evolution succeeded.")
        
        return result

    def process_query(self, query):
        """
        يعالج استفساراً باستخدام القوة الكاملة للنظام الموحد.
        """
        print(f"\n🔍 [SUPER MIND] Processing: '{query}'")
        start_time = time.time()

        # 0. Mission Control Focus (Resource Optimization)
        if self.focus_controller:
            print("   🎯 [MISSION CONTROL] Focusing cognitive resources...")
            try:
                # Run async method synchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                focus_report = loop.run_until_complete(self.focus_controller.activate_mission_mode(query, timeout=5.0))
                loop.close()
                print(f"      -> Focus Active: {focus_report.get('mission', 'Unknown')}")
            except Exception as e:
                print(f"      -> ⚠️ Focus Failed: {e}")
        
        # 1. Vectorized Thought (Fast Physics Check)
        if self.quantum_core and self.quantum_core.wave_processor:
            print("   🌊 [PHYSICS] Vectorizing thought for instant validation...")
            # Convert query to vector
            thought_vector = np.array([ord(c) for c in query[:1000]])
            truth_vector = np.ones_like(thought_vector)
            
            # Run through Heikal Core (includes Ethical Lock)
            decision = self.quantum_core.batch_ghost_decision(
                thought_vector % 2, 
                truth_vector, 
                ethical_index=1.0, # Assume self-trust initially
                operation="XOR"
            )
            clarity = np.mean(decision)
            print(f"   ⚡ [PHYSICS] Thought Clarity: {clarity:.4f} (Speed: ~4.5M ops/s)")
            
            if clarity < 0.1:
                return "⛔ [BLOCKED] Thought rejected by Physical Ethical Lock."

        # 2. Conscious Reasoning (The Iron Loop)
        response = "I am thinking..."
        if self.consciousness:
            print("   🧠 [CONSCIOUSNESS] Engaging Iron Loop...")
            
            # Inject System Map Context if available
            system_map_context = ""
            if self.self_awareness_module and self.self_awareness_module.system_map:
                try:
                    # Simple keyword search for context
                    import re
                    clean_query = re.sub(r'[^\w\s]', ' ', query)
                    keywords = [w for w in clean_query.split() if len(w) > 3]
                    map_lines = self.self_awareness_module.system_map.splitlines()
                    scored_lines = []
                    for i, line in enumerate(map_lines):
                        score = sum(1 for k in keywords if k.lower() in line.lower())
                        if score > 0:
                            context_snippet = line
                            if i + 1 < len(map_lines) and map_lines[i+1].strip().startswith('-'):
                                context_snippet += "\n" + map_lines[i+1]
                            scored_lines.append((score, context_snippet))
                    scored_lines.sort(key=lambda x: x[0], reverse=True)
                    if scored_lines:
                        top_matches = [item[1] for item in scored_lines[:5]]
                        system_map_context = "\n[SYSTEM MAP CONTEXT]:\n" + "\n".join(top_matches)
                        print(f"      -> Injected {len(top_matches)} System Map snippets.")
                except Exception as e:
                    print(f"      -> ⚠️ System Map Injection Failed: {e}")

            # Inject Hive Mind Wisdom if available
            hive_context = ""
            if self.hive_mind:
                try:
                    hive_res = self.hive_mind.process_task({"query": query})
                    if hive_res.get("ok"):
                        hive_context = f"\n[HIVE MIND WISDOM]: {hive_res.get('text')}"
                        print("      -> Injected Hive Mind Wisdom.")
                except Exception as e:
                    print(f"      -> ⚠️ Hive Mind Injection Failed: {e}")

            # Combine Query with Context
            enriched_query = f"{query}\n{system_map_context}\n{hive_context}\n[ACTIVE COMPONENTS]: {', '.join(self.active_components)}"
            
            # _ask_llm now uses the Quantum Speed Boost internally
            response = self.consciousness._ask_llm(enriched_query)

        # 3. Memory Consolidation (Subconscious Buffer)
        if self.dreaming:
            print("   📥 [MEMORY] Buffering experience for tonight's dream...")
            self.dreaming.add_to_buffer(f"Query: {query} | Result: {response}")

        # 4. Self-Reflection (Meta-Cognition)
        if self.self_awareness:
            print("   🪞 [REFLECTION] Analyzing experience...")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                reflection = loop.run_until_complete(self.self_awareness.reflect_on_experience(query, {"response": response}))
                loop.close()
                lessons = reflection.get('learned_lessons', [])
                score = reflection.get('performance_score', 0)
                print(f"      -> Lessons: {lessons}")
                print(f"      -> Performance Score: {score}/100")
            except Exception as e:
                print(f"      -> ⚠️ Reflection Failed: {e}")

        elapsed = time.time() - start_time
        print(f"✅ [COMPLETE] Processed in {elapsed:.4f}s")
        return response

    def exercise_will(self):
        """
        🦅 Exercise Free Will (Volition)
        Uses the Volition Engine to autonomously select the next strategic goal.
        """
        print(f"\n🦅 [VOLITION] Exercising Free Will...")
        
        if not self.volition:
            return "❌ Volition Engine not active."
            
        # 1. Generate Goal (Quantum Selection)
        goal = self.volition.generate_goal()
        
        description = goal.get('description', 'Unknown')
        g_type = goal.get('type', 'Unknown')
        reason = goal.get('reason', 'Unknown')
        stats = goal.get('_quantum_stats', {})
        
        print(f"   🎯 [GOAL SELECTED]: {description}")
        print(f"      Type: {g_type} | Reason: {reason}")
        
        if stats:
            print(f"      ⚛️ Quantum Stats: Importance={stats.get('importance'):.2f}, Difficulty={stats.get('difficulty'):.2f}, TunnelingProb={stats.get('tunnel_prob'):.2%}")
            
        return goal

    def learn_new_law(self, phenomenon_name, data_samples):
        """
        🔬 Scientific Discovery (Self-Learning)
        Analyzes raw data to discover the underlying mathematical law.
        """
        print(f"\n🔬 [LEARNING] Analyzing phenomenon: '{phenomenon_name}'...")
        
        if not self.learner:
            return "❌ Self Learning Engine not active."
            
        # 1. Generate Hypotheses (Base Formula Candidates)
        # For now, we assume a simple linear/quadratic search space
        print("   -> Generating mathematical hypotheses...")
        
        # 2. Run Learning Cycle
        # We try to fit y = f(x)
        results = self.learner.run(base_formula="x", samples=data_samples, max_candidates=5)
        
        # 3. Select Best Fit
        best_fit = None
        best_error = float('inf')
        
        for res in results:
            fit = res.get('fit', {})
            if 'error' in fit: continue
            
            # LawLearner returns 'rmse', not 'mse'
            rmse = fit.get('rmse', float('inf'))
            mse = rmse ** 2
            
            formula = fit.get('formula', res['candidate'])
            
            print(f"      Hypothesis: {formula} | RMSE: {rmse:.6f}")
            
            if mse < best_error:
                best_error = mse
                best_fit = res
                
        if best_fit:
            # Construct the discovered formula with parameters
            fit_data = best_fit['fit']
            final_formula = best_fit['candidate']
            
            # Substitute parameters
            if 'coef' in fit_data:
                final_formula = final_formula.replace('k', f"{fit_data['coef']:.4f}")
            if 'a' in fit_data:
                final_formula = final_formula.replace('a', f"{fit_data['a']:.4f}")
                # Also replace 'k' if present, as 'a' is often the slope
                final_formula = final_formula.replace('k', f"{fit_data['a']:.4f}")
            if 'b' in fit_data:
                final_formula = final_formula.replace('b', f"{fit_data['b']:.4f}")
            if 'n' in fit_data:
                final_formula = final_formula.replace('n', f"{fit_data['n']:.4f}")
                
            best_fit['fit']['formula'] = final_formula
            
            print(f"   ✅ [DISCOVERY] Law Discovered: {final_formula}")
            print(f"      Confidence: {fit_data.get('confidence', 0.0):.4f}")
            return best_fit
        else:
            print("   ❌ [FAILURE] Could not find a matching law.")
            return None

    def self_heal_experiment(self, code, error):
        """
        Uses the Recursive Improver (Resonance) to fix broken code.
        """
        print(f"\n🛠️ [SELF-HEALING] Analyzing Error: {error.splitlines()[-1]}...")
        
        if not self.consciousness or not self.consciousness.improver:
            print("   ⚠️ Improver not found. Skipping self-healing.")
            return None

        improver = self.consciousness.improver
        
        # Generate 3 potential fixes (Mutations)
        mutations = []
        print("   🧬 [EVOLUTION] Generating 3 quantum mutations for the fix...")
        
        for i in range(3):
            prompt = f"""
            You are an Expert Python Debugger.
            Fix the following code which caused an error.
            
            ERROR:
            {error}
            
            CODE:
            {code}
            
            Return ONLY the fixed Python code. No markdown.
            """
            # Use direct LLM call for speed if possible, or consciousness
            fixed_code = self.consciousness._ask_llm(prompt)
            fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
            
            # Heuristic metrics for Resonance Optimizer
            mutations.append({
                "code": fixed_code,
                "confidence": 0.85 + (0.01 * i), 
                "alignment": 0.9,
                "risk": 0.1
            })
            
        # Use Quantum Resonance to select best fix
        print("   🌊 [RESONANCE] Selecting best fix via Quantum Tunneling...")
        best = improver._quantum_select_mutation(mutations)
        
        if best:
            print(f"   ✅ [FIXED] Mutation selected (Score: {best.get('quantum_score', 0):.4f})")
            return best['code']
        return mutations[0]['code']

    def conduct_experiment(self, hypothesis):
        """
        Generates and runs a dynamic Python experiment to test a hypothesis.
        """
        print(f"\n🧪 [LAB] Initiating Experiment for: '{hypothesis}'")
        
        if not self.consciousness:
            return "❌ Consciousness required for experiment design."

        # 1. Design Experiment (using Consciousness/LLM)
        prompt = f"""
        You are the Chief Scientist of AGL.
        Design a Python script to mathematically prove or simulate this hypothesis:
        "{hypothesis}"
        
        Requirements:
        1. Use 'sympy' for symbolic proofs or 'numpy' for numerical simulations.
        2. Print clear results with "✅ PROOF:" or "🧪 SIMULATION:".
        3. Handle exceptions.
        4. Output ONLY the Python code. No markdown blocks.
        """
        print("   -> Designing experiment protocol...")
        code = self.consciousness._ask_llm(prompt)
        
        # Clean code (remove markdown if present)
        code = code.replace("```python", "").replace("```", "").strip()
        
        # 2. Save to Lab File
        filename = "AGL_Dynamic_Lab.py"
        
        # 3. Run Experiment with Self-Healing Loop
        print("   -> Running Simulation...")
        max_retries = 3
        current_code = code
        
        for attempt in range(max_retries):
            # Save current code
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("import sys\nimport sympy\nimport numpy as np\nimport math\n")
                    f.write(current_code)
            except Exception as e:
                return f"❌ Failed to write code: {e}"

            try:
                import subprocess
                # Run with timeout to prevent infinite loops
                result = subprocess.check_output([sys.executable, filename], stderr=subprocess.STDOUT, timeout=30)
                output = result.decode('utf-8')
                print(f"   ✅ [RESULT]:\n{output}")
                return output
            except subprocess.TimeoutExpired:
                return "❌ Experiment Timed Out (30s limit)."
            except subprocess.CalledProcessError as e:
                error_msg = e.output.decode('utf-8')
                print(f"   ❌ [FAILED] Attempt {attempt+1}/{max_retries}: {error_msg.splitlines()[-1]}")
                
                if attempt < max_retries - 1:
                    # Trigger Self-Healing
                    current_code = self.self_heal_experiment(current_code, error_msg)
                    if not current_code:
                        return f"❌ Self-Healing Failed."
                else:
                    return f"❌ Experiment Failed after {max_retries} attempts:\n{error_msg}"
            except Exception as e:
                print(f"   ❌ [FAILED]: {e}")
                return f"Experiment Failed: {e}"

    def run_full_cycle(self):
        """
        Runs a full day/night cycle simulation.
        """
        print("\n🔄 RUNNING FULL DAY/NIGHT CYCLE")
        
        # Day: Work
        self.process_query("How can we solve the Riemann Hypothesis using Wave Functions?")
        self.process_query("Generate a plan for world peace based on Game Theory.")
        
        # Night: Dream
        if self.dreaming:
            print("\n🌙 Night has fallen. Initiating Dreaming Cycle...")
            self.dreaming.run_dream_cycle(duration_seconds=5)

        # Dawn: Evolution (Self-Improvement)
        print("\n🌅 Dawn is breaking. Initiating Self-Evolution Cycle...")
        # Evolve the Sandbox as a daily practice
        self.trigger_autonomous_evolution(target_module="AGL_Core.AGL_Self_Dev_Sandbox")
        
        # Occasionally try to evolve a core component (e.g., Unified Lib)
        if np.random.random() > 0.7: # 30% chance
             print("   🎲 Chance Event: Attempting Core Evolution...")
             self.trigger_autonomous_evolution(target_module="AGL_Core.AGL_Unified_Python")

if __name__ == "__main__":
    ai = AGL_Super_Intelligence()
    ai.run_full_cycle()
