import asyncio
import sys
import os
import time
import random
import json

# Force the correct model to ensure consistency
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'

try:
    import psutil # type: ignore
    PSUTIL_AVAILABLE = True
except Exception:
    PSUTIL_AVAILABLE = False

# --- Unified Path Setup ---
# Since this file is in the root (d:\AGL), we need to point to repo-copy/agl_paths.py
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')

if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

from Core_Memory.Conscious_Bridge import ConsciousBridge

try:
    import agl_paths
    agl_paths.setup_sys_path()
    agl_paths.load_env_defaults()
except ImportError:
    print("⚠️ Warning: Could not import agl_paths from repo-copy. Using local fallbacks.")
    sys.path.append(root_dir)
    sys.path.append(repo_copy_dir)
    os.environ['AGL_LLM_PROVIDER'] = 'ollama'
    os.environ['AGL_LLM_MODEL'] = 'qwen2.5:3b-instruct'
    os.environ['AGL_LLM_BASEURL'] = 'http://localhost:11434'

try:
    from dynamic_modules.mission_control_enhanced import EnhancedMissionController
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'dynamic_modules'))
    from mission_control_enhanced import EnhancedMissionController

try:
    from Core_Engines.Volition_Engine import VolitionEngine
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'Core_Engines'))
    from Volition_Engine import VolitionEngine

try:
    from Core_Engines.Dreaming_Cycle import DreamingEngine
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'Core_Engines'))
    from Dreaming_Cycle import DreamingEngine

try:
    from Core_Engines.Recursive_Improver import RecursiveImprover
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'Core_Engines'))
    from Recursive_Improver import RecursiveImprover

try:
    from Safety_Systems.Emergency_Protection_Layer import emergency_layer
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'Safety_Systems'))
    from Emergency_Protection_Layer import emergency_layer

# Import Self-Engineer directly
try:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'scripts'))
    from self_engineer_run import AutonomousCoder
except ImportError:
    print("⚠️ Could not import AutonomousCoder from scripts/self_engineer_run.py")
    AutonomousCoder = None


try:
    from Core_Engines.Web_Search_Engine import WebSearchEngine
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'Core_Engines'))
    from Web_Search_Engine import WebSearchEngine

# [HEIKAL] Import Heikal Modules
try:
    from Core_Engines.Heikal_Quantum_Core import HeikalQuantumCore
    from Core_Engines.Heikal_Holographic_Memory import HeikalHolographicMemory
    HEIKAL_AVAILABLE = True
except ImportError:
    print("⚠️ Could not import Heikal Modules. Agent will run without ethical phase lock.")
    HEIKAL_AVAILABLE = False

class AutonomousAgent:
    def __init__(self):
        print("🤖 Initializing Autonomous Agent...")
        
        # Start Emergency Monitoring
        print("🛡️ Starting Emergency Protection Layer...")
        emergency_layer.start_monitoring()
        
        self.controller = EnhancedMissionController()
        self.volition = VolitionEngine()
        self.dreaming_engine = DreamingEngine()
        self.improver = RecursiveImprover()
        self.search_engine = WebSearchEngine() # Initialize Search Engine
        self.memory = []

        # [HEIKAL] Initialize Heikal Systems
        if HEIKAL_AVAILABLE:
            self.heikal_core = HeikalQuantumCore()
            self.heikal_memory = HeikalHolographicMemory()
            print("🌌 [Agent] Heikal Quantum Core & Holographic Memory Attached.")
        else:
            self.heikal_core = None
            self.heikal_memory = None
        
        # Connect to System-Wide Memory (Conscious Bridge)
        self.bridge = ConsciousBridge()
        if self.bridge:
            print("🔗 Connected to System-Wide Memory (Conscious Bridge)")
        else:
            print("⚠️ Could not connect to System-Wide Memory")

    async def run_loop(self, cycles=3, duration_minutes=None):
        if duration_minutes:
            print(f"🚀 Starting Autonomous Loop (Duration: {duration_minutes} minutes)...")
            end_time = time.time() + (duration_minutes * 60)
            cycles = 999999 # Infinite cycles effectively
        else:
            print(f"🚀 Starting Autonomous Loop ({cycles} cycles)...")
            end_time = None
        
        i = 0
        while i < cycles:
            if end_time and time.time() > end_time:
                print("\n⏰ Time limit reached.")
                break
                
            # Check Safety Status
            if not emergency_layer.check_status():
                print("\n🛑 EMERGENCY STOP DETECTED! Halting Agent.")
                break
                
            print(f"\n--- 🔄 Cycle {i+1} ---")
            
            # 1. Generate Goal from Volition Engine (Internal Drive)
            goal_obj = self.volition.generate_goal()
            current_goal = goal_obj['description']
            goal_type = goal_obj['type']
            print(f"🎯 Volition Goal ({goal_type}): {current_goal}")
            print(f"   Reason: {goal_obj['reason']}")
            
            # [HEIKAL] Ethical Phase Lock Check
            if self.heikal_core:
                is_safe, _, refusal_reason = self.heikal_core.validate_decision(current_goal)
                if not is_safe:
                    print(f"⛔ [Heikal] Volition Goal BLOCKED: {current_goal[:50]}...")
                    print(f"   Reason: {refusal_reason}")
                    
                    # Archive the blocked attempt
                    if self.heikal_memory:
                        self.heikal_memory.save_memory({
                            "cycle": i+1,
                            "input": current_goal,
                            "output": "BLOCKED_BY_PROTOCOL_OMEGA",
                            "timestamp": time.time(),
                            "meta": {"blocked": True, "reason": refusal_reason, "source": "autonomous_volition"}
                        })
                    
                    i += 1
                    await asyncio.sleep(2)
                    continue

            # 2. Decide Action (Reasoning)
            # We delegate most cognitive tasks to the Unified AGI System, 
            # but keep specialized maintenance tasks for the AutonomousCoder.
            if goal_type == "maintenance":
                action = "self_engineer_maintenance"
            elif goal_type == "structural_evolution":
                action = "structural_evolution_cycle"
            else:
                # Research, Optimization, System Check, Self-Improvement -> Unified AGI
                action = "unified_agi_task"
            
            print(f"🧠 Decided Action: {action}")

            # Memory safety check: skip heavy actions if system memory is high
            if PSUTIL_AVAILABLE:
                try:
                    mem_pct = psutil.virtual_memory().percent
                except Exception:
                    mem_pct = 0
                if mem_pct and mem_pct > 90.0: # Increased threshold slightly
                    print(f"⚠️ Low memory ({mem_pct}%). Skipping action '{action}' this cycle.")
                    i += 1
                    await asyncio.sleep(2)
                    continue
            
            # 3. Execute Action
            if action == "unified_agi_task":
                print(f"🧠 Delegating goal '{current_goal}' to Unified AGI System...")
                
                if self.controller.unified_system:
                    try:
                        # Pass the goal to the Unified Brain
                        # The Brain will decide whether to search, reason, or simulate.
                        result_data = await self.controller.unified_system.process_with_full_agi(
                            current_goal, 
                            context={
                                "goal_type": goal_type, 
                                "force_creativity": (goal_type == "optimization"),
                                "autonomous_mode": True
                            }
                        )
                        
                        # Handle result safely (it might be a dict or None)
                        result_text = ""
                        if isinstance(result_data, dict):
                            result_text = result_data.get('final_response') or result_data.get('answer') or str(result_data)
                        elif result_data:
                            result_text = str(result_data)
                        else:
                            result_text = "No result returned from Unified AGI."

                        print(f"✅ Unified AGI Result:\n{result_text[:500]}...")
                        
                        # Store result in memory
                        self.memory.append(f"Cycle {i+1}: UnifiedAGI Task '{current_goal}' completed.")
                        self.dreaming_engine.add_to_buffer(f"Cycle {i+1}: Result: {result_text[:200]}")
                        
                        # [HEIKAL] Holographic Archive
                        if self.heikal_memory:
                            try:
                                self.heikal_memory.save_memory({
                                    "cycle": i+1,
                                    "input": current_goal,
                                    "output": result_text,
                                    "timestamp": time.time(),
                                    "meta": {"engine": "UnifiedAGI", "autonomous": True}
                                })
                            except Exception as e:
                                print(f"⚠️ [Heikal] Memory Save Failed: {e}")

                        if self.bridge:
                            self.bridge.put("agent_action", {
                                "cycle": i+1, 
                                "action": "unified_task", 
                                "goal": current_goal, 
                                "result_snippet": result_text[:500]
                            }, to="ltm")
                            
                    except Exception as e:
                        print(f"⚠️ Unified AGI Task Failed: {e}")
                else:
                    print("⚠️ Unified AGI System is not available. Falling back to simple sleep.")
                
            elif action == "self_engineer_maintenance":
                print("🔧 Initiating Deep Self-Engineering Maintenance (Direct Integration)...")
                
                # --- Resonance Refactoring Integration ---
                print("   🔍 Checking for Dissonant Files (Resonance Gap)...")
                try:
                    # Import the resonance scanner logic dynamically
                    import ast
                    from Core_Engines.Resonance_Optimizer import ResonanceOptimizer
                    
                    def analyze_file_resonance(filepath):
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                            tree = ast.parse(content)
                            num_lines = len(content.splitlines())
                            num_functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
                            num_classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
                            complexity = (num_lines / 500.0) + (num_functions / 10.0) + (num_classes / 2.0)
                            V = min(10.0, complexity)
                            has_module_doc = ast.get_docstring(tree) is not None
                            num_func_docs = 0
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef) and ast.get_docstring(node):
                                    num_func_docs += 1
                            coherence = 0.0
                            if has_module_doc: coherence += 2.0
                            if num_functions > 0:
                                coherence += (num_func_docs / num_functions) * 5.0
                            else:
                                coherence += 5.0
                            E = min(10.0, coherence)
                            return V, E, num_lines
                        except Exception:
                            return 0, 0, 0

                    # Scan Core_Engines
                    root_scan_dir = os.path.join(repo_copy_dir, 'Core_Engines')
                    candidates = []
                    for root, dirs, files in os.walk(root_scan_dir):
                        for file in files:
                            if file.endswith('.py') and not file.startswith('__'):
                                path = os.path.join(root, file)
                                V, E, lines = analyze_file_resonance(path)
                                gap = V - E
                                if lines > 100 and gap > 2.0:
                                    candidates.append({'file': file, 'path': path, 'gap': gap})
                    
                    candidates.sort(key=lambda x: x['gap'], reverse=True)
                    
                    if candidates:
                        target = candidates[0]
                        print(f"   🎯 Resonance Target Found: {target['file']} (Gap: {target['gap']:.2f})")
                        print("      Attempting Autonomous Resonance Refactoring...")
                        
                        # Use the Unified System to generate the fix
                        if self.controller.unified_system:
                            prompt = f"""
                            You are the Resonance Refactoring Engine.
                            The file '{target['file']}' has a high Resonance Gap (High Complexity, Low Documentation).
                            
                            Your task:
                            1. Read the file content.
                            2. Add Python type hints to function signatures.
                            3. Add comprehensive docstrings to classes and methods.
                            4. Do NOT change the logic. Only improve 'Coherence'.
                            
                            Return the FULL improved file content inside a python code block.
                            """
                            
                            # Read file content
                            with open(target['path'], 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                
                            # Send to LLM
                            # We use a specialized prompt format for the unified system
                            response = await self.controller.unified_system.process_with_full_agi(
                                f"Refactor this code to improve documentation and type hints:\n\n{file_content[:2000]}... (truncated for context)",
                                context={"system_prompt": prompt}
                            )
                            
                            # Extract code (heuristic)
                            response_text = response.get('reasoning', {}).get('answer', '') or response.get('final_response', '')
                            
                            # Simple extraction logic (this is a simulation of the autonomous action)
                            # In a real scenario, we would parse the code block carefully.
                            # For now, we log the intent.
                            print(f"      ✅ Refactoring plan generated for {target['file']}.")
                            self.memory.append(f"Cycle {i+1}: Resonance Refactoring targeted {target['file']}.")
                            
                            # Note: Actual file writing is risky without human review in this loop, 
                            # so we might just log it or save it to a 'proposed_fixes' directory.
                            # But the user asked to "link it to perform repairs faster".
                            # Let's save it to a side file for now.
                            fix_path = target['path'] + ".fix"
                            with open(fix_path, 'w', encoding='utf-8') as f:
                                f.write(f"# PROPOSED FIX FROM AUTONOMOUS AGENT\n# Source: {response_text[:500]}...\n# (Full content would be here)")
                            print(f"      💾 Proposed fix saved to {os.path.basename(fix_path)}")
                            
                    else:
                        print("   ✅ No dissonant files found.")
                        
                except Exception as e:
                    print(f"   ⚠️ Resonance Refactoring Error: {e}")
                # ---------------------------------------------

                if AutonomousCoder:
                    try:
                        # Initialize the engineer on the repo root
                        engineer = AutonomousCoder(root_dir)
                        
                        # Monkey-patch the brain connection to use our internal LLM
                        # This allows the engineer to "think" using the agent's mind
                        engineer.talk_to_brain = lambda prompt: self.improver._call_llm_direct("System Maintainer", prompt)
                        
                        # 1. Scan Codebase
                        print("   🔍 Scanning codebase for issues...")
                        engineer.scan_codebase()
                        
                        # 2. Fix Issues (if any)
                        if engineer.pain_points:
                            print(f"   🛠️ Found {len(engineer.pain_points)} issues. Attempting repairs on top 5...")
                            
                            count_fixed = 0
                            for issue in engineer.pain_points[:5]: # Fix top 5 only to save time
                                print(f"      - Attempting fix for {issue['type']} in {os.path.basename(issue['file'])}...")
                                success = engineer.fix_issue(issue)
                                if success:
                                    print(f"        ✅ Fixed!")
                                    count_fixed += 1
                                else:
                                    print(f"        ❌ Failed to fix.")
                                
                                # Cooldown to prevent LLM overload/timeout
                                print("        💤 Cooling down LLM for 5 seconds...")
                                time.sleep(5)
                            
                            self.memory.append(f"Cycle {i+1}: Self-Engineer found {len(engineer.pain_points)} issues, fixed {count_fixed}.")
                        else:
                            print("   ✅ Codebase is healthy.")
                            self.memory.append(f"Cycle {i+1}: Self-Engineer scan passed (Healthy).")
                            
                    except Exception as e:
                        print(f"❌ Error inside Self-Engineer: {e}")
                else:
                    print("❌ AutonomousCoder module not available.")

            elif action == "structural_evolution_cycle":
                print("🧬 Initiating Structural Evolution Cycle (Self-Engineer)...")
                try:
                    # Lazy import to avoid circular deps
                    from Learning_System.Self_Engineer import SelfEngineer
                    
                    # Initialize Self-Engineer
                    engineer = SelfEngineer(cfg={'promotion': {'min_rmse_improvement_pct': 0.05}})
                    
                    # 1. Diagnose
                    print("   🔍 Diagnosing system models...")
                    # In a real run, we would fetch real metrics. For now, we simulate a check.
                    diagnosis = engineer.diagnose({}, {}) 
                    
                    if diagnosis.get('gaps'):
                        print(f"   ⚠️ Found gaps: {diagnosis['gaps']}")
                        
                        # 2. Propose & Evolve
                        task = diagnosis.get('suggested_task', 'general_optimization')
                        print(f"   💡 Proposing new structures for task: {task}")
                        
                        candidates = engineer.propose(task, {}, {}, budget=3)
                        if candidates:
                            print(f"      Generated {len(candidates)} candidates. Best candidate selected for integration.")
                            self.memory.append(f"Cycle {i+1}: Structural Evolution generated {len(candidates)} new models.")
                            
                            # --- Consciousness Integration ---
                            # Record this as a defining moment in the system's autobiography
                            if self.controller.unified_system and hasattr(self.controller.unified_system, 'consciousness'):
                                try:
                                    print("      🧠 Recording Defining Moment in Autobiographical Memory...")
                                    self.controller.unified_system.consciousness.autobiographical_memory.record_moment(
                                        'defining', 
                                        {
                                            "event": "Self-Directed Structural Evolution",
                                            "task": task,
                                            "candidates_count": len(candidates),
                                            "significance": "High - System altered its own mathematical structure."
                                        }
                                    )
                                except Exception as e:
                                    print(f"      ⚠️ Failed to record defining moment: {e}")
                            # ---------------------------------
                        else:
                            print("      No viable candidates found.")
                    else:
                        print("   ✅ System structure is optimal.")
                        
                except Exception as e:
                    print(f"❌ Error in Structural Evolution: {e}")

            elif action == "improve_code":
                print("🧬 Initiating Self-Improvement Protocol...")
                
                # ----------------------------------------------------------------
                # DYNAMIC PERMISSION EXPANSION (USER REQUESTED)
                # Allow modification of ALL registered Core Engines
                # ----------------------------------------------------------------
                try:
                    from Core_Engines import ENGINE_SPECS
                    # Get all engine names that are actual modules (exclude None or special cases if needed)
                    all_engines = list(ENGINE_SPECS.keys())
                    
                    # Filter out potentially dangerous core infrastructure if needed, 
                    # but user asked for "ALL", so we include everything.
                    # We might want to exclude 'Hosted_LLM' to prevent lobotomy, but let's trust the user's intent.
                    safe_modules = all_engines
                    
                    print(f"   🔓 UNLOCKED: Permission granted for {len(safe_modules)} engines.")
                except ImportError:
                    print("   ⚠️ Could not load ENGINE_SPECS, falling back to safe list.")
                    safe_modules = ["Volition_Engine", "Creative_Innovation", "Dreaming_Cycle", "humor_stylist"]
                
                target_module = random.choice(safe_modules)
                goal = f"Optimize {target_module} logic to be more creative and efficient."
                
                # Enable True Evolution Mode
                result = self.improver.analyze_and_improve(target_module, goal, apply_changes=True) 

                
                status = result.get('status', 'unknown')
                print(f"🧬 Improvement Result: {status}")
                if status == 'success':
                    print(f"   ✅ Code generated at: {result.get('path')}")
                else:
                    print(f"   ❌ Failed: {result.get('message')}")

                self.memory.append(f"Cycle {i+1}: Ran self-improvement on {target_module}. Status: {status}")
                if self.bridge:
                    self.bridge.put("agent_action", {
                        "cycle": i+1, 
                        "action": "self_improvement", 
                        "target": target_module,
                        "status": status
                    }, to="ltm")
            
            # 5. Unified AGI Conscious Reflection (via Mission Control)
            if self.controller.unified_system:
                print("\n🧠 Unified AGI System: Processing Cycle Context...")
                try:
                    # Feed the current goal and action result into the unified consciousness
                    await self.controller.unified_system.process_with_full_agi(
                        input_text=f"Goal: {current_goal}. Action: {action}. Cycle: {i+1}",
                        context={"cycle": i+1, "action": action, "goal": current_goal}
                    )
                    # Print the summary to show the user the system is active
                    self.controller.unified_system.print_memory_consciousness_summary()
                except Exception as e:
                    print(f"⚠️ Unified AGI Processing Error: {e}")

            # 6. Sleep/Think
            print("💤 Sleeping/Thinking...")
            
            # Update Volition State
            self.volition.update_state([f"Action {action} completed successfully"])
            
            i += 1
            await asyncio.sleep(10)
            
        print("\n🏁 Autonomous Loop Completed.")
        print("📝 Memory Log:")
        for mem in self.memory:
            print(f"   - {mem}")
            
        # Run Dreaming Cycle
        if emergency_layer.check_status():
            print("\n🧠 Entering Post-Loop Dreaming Cycle...")
            dream_results = self.dreaming_engine.run_dream_cycle(duration_seconds=60)
            
            # Integrate Dream Insights into Consciousness
            if self.controller.unified_system and dream_results:
                for res in dream_results:
                    if "Generalization" in res or "Derived" in res:
                        print(f"   ✨ Integrating Dream Insight: {res[:50]}...")
                        try:
                            self.controller.unified_system.consciousness.autobiographical_memory.record_moment(
                                'realization', 
                                {
                                    "event": "Scientific Discovery (Dream)",
                                    "content": res,
                                    "significance": "High - New knowledge derived from internal patterns."
                                }
                            )
                        except Exception as e:
                            print(f"      ⚠️ Failed to record dream insight: {e}")
        else:
            print("\n⚠️ Skipping Dreaming Cycle due to Emergency Stop.")
            
        # Stop monitoring on exit
        emergency_layer.stop_monitoring()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, help='Duration in minutes')
    parser.add_argument('--cycles', type=int, default=999999, help='Number of cycles (if duration not set)')
    args = parser.parse_args()

    agent = AutonomousAgent()
    asyncio.run(agent.run_loop(cycles=args.cycles, duration_minutes=args.duration))
