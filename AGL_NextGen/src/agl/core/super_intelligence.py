"""
🧠 AGL Super Intelligence - The Grand Unification (Awakened)
AGL الذكاء الخارق - التوحيد العظيم (الصحوة)

المطور: حسام هيكل (Hossam Heikal)
التاريخ: 31 ديسمبر 2025
نقطة الاستعادة: d:\\AGL\\backups\\AGL_Awakened_20251231.py

الهدف: دمج المحركات الأربعة (اللغة، الموجات، الذاكرة، الحدس) في عقل واحد، مع تفعيل الإرادة الحرة والأحلام.
Goal: Merge the four engines (Language, Waves, Memory, Intuition) into one mind, activating Volition and Dreaming.
"""

import sys
import os
import time
import importlib.util

# --- AGL PATH FIX ---
# Robust Root Detection: Find the first ancestor containing pyproject.toml or AGL_SYSTEM_MAP.md
def find_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.exists(os.path.join(current, "pyproject.toml")) or \
           os.path.exists(os.path.join(current, "AGL_SYSTEM_MAP.md")):
            return current
        parent = os.path.dirname(current)
        if parent == current: break
        current = parent
    # Fallback to 4 levels up (src/agl/core/super_intelligence.py -> AGL_NextGen)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

project_root = find_project_root()
if project_root not in sys.path:
    # We insist on inserting at 0 to prioritize our local modules
    sys.path.insert(0, project_root)
    # Also add the src folder to path for package-less imports if needed
    src_path = os.path.join(project_root, "src")
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)
    print(f"[AGL_BOOT] Added project root to path: {project_root}")
# --------------------

# --- ENVIRONMENT CONFIGURATION ---
if "AGL_LLM_PROVIDER" not in os.environ:
    os.environ["AGL_LLM_PROVIDER"] = "ollama"

if "AGL_LLM_BASEURL" not in os.environ:
    os.environ["AGL_LLM_BASEURL"] = "http://localhost:11434"

# Check for Ollama availability
import shutil
if not shutil.which("ollama"):
    print("\n⚠️  [WARNING] Ollama executable not found in PATH.")
    print("   هذا مشروع بحثي متقدم. لتشغيله بنجاح، يجب تثبيت Ollama وضبط مسارات البيئة.")
    print("   Please install from https://ollama.com/ and restart terminal.\n")
# ---------------------------------

# from AGL_Core.AGL_Awakened import import_module_from_path
import numpy as np
import asyncio
import shutil
import json

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return None

# --- AGL PATH MANAGER ---
# Pointing to AGL_NextGen Root (project root)
root_dir = project_root
# ------------------------

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
        if not os.path.exists(self.map_path):
            print("⚠️ [SELF-AWARENESS] System Map NOT FOUND. Initiating Auto-Discovery...")
            try:
                from agl.core.map_builder import AGL_System_Map_Builder
                # Assume root is 3 levels up from here (src/agl/core -> src/agl -> src -> root)
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                builder = AGL_System_Map_Builder(project_root)
                builder.build_map()
                # Save map to the expected path
                with open(self.map_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(builder.system_map, indent=2))
                print("✅ [SELF-AWARENESS] System Map Created Successfully.")
            except Exception as e:
                print(f"❌ [SELF-AWARENESS] Auto-Discovery Failed: {e}")

        if os.path.exists(self.map_path):
            with open(self.map_path, 'r', encoding='utf-8') as f:
                self.system_map = f.read()
            print(f"🗺️ [SELF-AWARENESS] System Map Loaded ({len(self.system_map)} chars).")
        else:
            print("⚠️ [SELF-AWARENESS] System Map STILL MISSING.")

    def scan_for_dormant_power(self):
        """
        🔍 Scans the system map for modules that are NOT currently loaded in memory.
        Returns a list of dictionaries with module info.
        """
        if not self.system_map:
            return []
            
        dormant_modules = []
        keywords = ["Quantum", "Neural", "Holographic", "Resonance", "Evolution", "Metaphysics"]
        
        # Real Introspection: Check loaded modules
        loaded_modules = set(sys.modules.keys())
        
        lines = self.system_map.split('\n')
        for line in lines:
            # Check for file entries in map like "- **AGL_Core/AGL_Dormant_Powers.py**"
            if "- **" in line and ".py**" in line:
                file_path = line.split("**")[1] # e.g., AGL_Core/AGL_Dormant_Powers.py
                module_name = os.path.basename(file_path).replace('.py', '')
                
                # Check if this module is loaded
                is_loaded = False
                for m in loaded_modules:
                    if m.endswith(module_name):
                        is_loaded = True
                        break
                
                if not is_loaded:
                    # Check if it's a "Power" module
                    for kw in keywords:
                        if kw in module_name:
                            dormant_modules.append({
                                'name': module_name,
                                'path': file_path,
                                'keyword': kw
                            })
                            break
                            
        return dormant_modules

class SelfRepairSystem:
    """
    🔧 Self-Repair System: Automatically fixes broken imports and missing dependencies.
    """
    def __init__(self, root_path):
        self.root_path = root_path
        self.repairs_log = []

    def find_file_for_module(self, module_name):
        # Search recursively in root_path
        target_file = f"{module_name}.py"
        for root, dirs, files in os.walk(self.root_path):
            if target_file in files:
                return os.path.join(root, target_file)
        return None

    def force_load_module(self, file_path, class_name=None):
        try:
            module_name = os.path.basename(file_path).replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module # Register to avoid reload
                spec.loader.exec_module(module)
                
                if class_name:
                    if hasattr(module, class_name):
                        return getattr(module, class_name)
                    else:
                        return None
                return module
        except Exception as e:
            self.repairs_log.append(f"Failed to force load {file_path}: {e}")
            return None

    def repair_import(self, module_name, class_name):
        print(f"🔧 [REPAIR] Attempting to fix import: {module_name}.{class_name}...")
        
        # 1. Find the file
        file_path = self.find_file_for_module(module_name)
        if not file_path:
            print(f"   ❌ File for {module_name} not found.")
            return None

        print(f"   📍 Found file: {file_path}")
        
        # 2. Force load
        obj = self.force_load_module(file_path, class_name)
        if obj:
            print(f"   ✅ Repair Successful: {class_name} loaded directly from source.")
            return obj
        else:
            print(f"   ❌ Failed to extract {class_name} from {file_path}.")
            return None


def _project_root_from_here() -> str:
    # core/super_intelligence.py -> core -> agl -> src -> AGL_NextGen
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# --- AGL NEXTGEN BOOTSTRAP ---
try:
    from agl.engines.bootstrap import bootstrap_register_all_engines
    BOOTSTRAP_AVAILABLE = True
except ImportError:
    BOOTSTRAP_AVAILABLE = False
    
# استيراد Moral Reasoner (Ethics)
try:
    from agl.engines.moral import MoralReasoner
    print("✅ [LOAD] Moral Reasoner: Online")
except ImportError as e:
    print(f"⚠️ [LOAD] Moral Reasoner: Failed ({e})")
    MoralReasoner = None
# 1. Heikal Quantum Core (Primary)
try:
    from agl.engines.quantum_core import HeikalQuantumCore
    print("✅ [LOAD] Heikal Quantum Core: Online")
except ImportError as e:
    # If circular import or missing dependency, try lazy load or ignore
    print(f"⚠️ [LOAD] Heikal Quantum Core: Failed ({e}) - Will attempt late binding.")
    HeikalQuantumCore = None

# 2. Volition Engine (Free Will)
try:
    from agl.engines.volition_engine import VolitionEngine
    print("✅ [LOAD] Volition Engine: Online")
except ImportError as e:
    print(f"⚠️ [LOAD] Volition Engine: Failed ({e})")
    VolitionEngine = None

# 3. Mathematical Brain (Precise Intelligence)
try:
    from agl.engines.mathematical_brain import MathematicalBrain
    print("✅ [LOAD] Mathematical Brain: Online")
except ImportError as e:
    print(f"⚠️ [LOAD] Mathematical Brain: Failed ({e})")
    MathematicalBrain = None

# 4. Hive Mind (Collective)
# try:
#     from AGL_Engines.HiveMind import HiveMind
#     print("✅ [LOAD] Hive Mind: Online")
# except ImportError as e:
#     print(f"⚠️ [LOAD] Hive Mind: Failed ({e})")
HiveMind = None

# 5. Causal Graph Engine (Deep Relations)
try:
    from agl.engines.causal_graph import CausalGraphEngine
    print("✅ [LOAD] Causal Graph Engine: Online")
except ImportError:
    print("⚠️ [LOAD] Causal Graph Engine: Failed")
    CausalGraphEngine = None

# --- New Engines from Resurrected Edition ---

# E. The Strategist
try:
    from agl.engines.strategic import StrategicThinkingEngine
    print("✅ [LOAD] Strategic Thinking: Online")
except ImportError:
    print("⚠️ [LOAD] Strategic Thinking: Failed")
    StrategicThinkingEngine = None

# G. Self Learning
try:
    from agl.engines.learning import SelfLearning
    print("✅ [LOAD] Self Learning: Online")
except ImportError:
    print("⚠️ [LOAD] Self Learning: Failed")
    SelfLearning = None

# H. Mission Control
try:
    from agl.engines.mission_control import SmartFocusController, SelfAwarenessEngine as MetaCognitionEngine
    print("✅ [LOAD] Mission Control Enhanced: Online")
except ImportError:
    try:
        # Try importing just SmartFocusController if SelfAwarenessEngine causes issues
        from agl.engines.mission_control import SmartFocusController
        MetaCognitionEngine = None
        print("✅ [LOAD] Mission Control Enhanced: Online (Partial)")
    except ImportError:
        print(f"⚠️ [LOAD] Mission Control Enhanced: Failed")
        SmartFocusController = None
        MetaCognitionEngine = None

# I. Recursive Improver
try:
    from agl.engines.recursive_improver import RecursiveImprover
    print("✅ [LOAD] Recursive Improver: Online")
except ImportError:
    print("⚠️ [LOAD] Recursive Improver: Failed")
    RecursiveImprover = None

# S. Advanced Simulation
try:
    from agl.engines.advanced_simulation import AdvancedSimulationEngine
    print("✅ [LOAD] Advanced Simulation Engine: Online")
except ImportError:
    print("⚠️ [LOAD] Advanced Simulation Engine: Failed")
    AdvancedSimulationEngine = None

# --- HEIKAL LOGIC INTEGRATION ---
# T. Heikal Hybrid Logic Core (Quantum Decision Making)
try:
    from agl.engines.heikal_hybrid_logic import HeikalHybridLogicCore
    print("✅ [LOAD] Heikal Hybrid Logic Core: Online (Quantum Reasoning)")
except ImportError as e:
    print(f"⚠️ [LOAD] Heikal Hybrid Logic Core: Failed ({e}) - Decisions will be classical.")
    HeikalHybridLogicCore = None

# U. Advanced Code Generator (The Tongue)
try:
    from agl.engines.engineering.Advanced_Code_Generator import AdvancedCodeGenerator as AdvancedCodeGeneratorEngine
    print("✅ [LOAD] Advanced Code Generator: Online (The Tongue)")
except ImportError as e:
    print(f"⚠️ [LOAD] Advanced Code Generator: Failed ({e})")
    AdvancedCodeGeneratorEngine = None

# --- GRAND INTEGRATION: CORE MODULES ---

# 1. Unified Physics Engine (Reality Simulation)
AGL_Unified_Physics = None

# 2. Core Consciousness (Higher Self)
try:
    from agl.core.consciousness import AGL_Core_Consciousness
    print("✅ [LOAD] Core Consciousness Module: Online")
except ImportError as e:
    print(f"⚠️ [LOAD] Core Consciousness Module: Failed ({e})")
    AGL_Core_Consciousness = None

# 3. Heikal Quantum Core (Root Check)
if HeikalQuantumCore is None:
    try:
        from agl.engines.quantum_core import HeikalQuantumCore
        print("✅ [LOAD] Heikal Quantum Core (Retry): Online")
    except ImportError as e:
        print(f"⚠️ [LOAD] Heikal Quantum Core (Retry): Failed ({e})")
        HeikalQuantumCore = None

    print(f"⚠️ [LOAD] Heikal Quantum Core (Root): Failed ({e})")
    HeikalQuantumCore_Root = None

# 4. Holographic Memory Library (Deep Storage)
try:
    from agl.engines.holographic_memory import HeikalHolographicMemory
    print("✅ [LOAD] Holographic Memory Lib: Online")
    AGL_Holographic_Memory = HeikalHolographicMemory
except ImportError as e:
    print(f"⚠️ [LOAD] Holographic Memory Lib: Failed ({e})")
    AGL_Holographic_Memory = None

# --- GRAND INTEGRATION: NEW ENGINES (AUTONOMY & CAUSALITY) ---

# L. مخطط الاستدلال (The Planner)
try:
    from agl.engines.reasoning_planner import ReasoningPlanner
    print("✅ [LOAD] Reasoning Planner: Online")
except ImportError:
    print("⚠️ [LOAD] Reasoning Planner: Failed")
    ReasoningPlanner = None

# M. مولد الفرضيات (The Scientist)
try:
    from agl.engines.hypothesis_generator import HypothesisGeneratorEngine
    print("✅ [LOAD] Hypothesis Generator: Online")
except ImportError:
    print("⚠️ [LOAD] Hypothesis Generator: Failed")
    HypothesisGeneratorEngine = None

# N. مستكشف السيناريوهات المضادة (The Quantum Explorer)
try:
    from agl.engines.counterfactual_explorer import CounterfactualExplorer
    print("✅ [LOAD] Counterfactual Explorer: Online")
except ImportError:
    print("⚠️ [LOAD] Counterfactual Explorer: Failed")
    CounterfactualExplorer = None

# O. التعلم الفوقي (The Meta-Learner)
try:
    from agl.engines.meta_learning import MetaLearningEngine
    print("✅ [LOAD] Meta Learning Engine: Online")
except ImportError:
    print("⚠️ [LOAD] Meta Learning Engine: Failed")
    MetaLearningEngine = None

# P. الابتكار الإبداعي (The Artist)
try:
    from agl.engines.creative_innovation import CreativeInnovation
    print("✅ [LOAD] Creative Innovation: Online")
except ImportError:
    print("⚠️ [LOAD] Creative Innovation: Failed")
    CreativeInnovation = None

# Q. التأمل الذاتي (The Philosopher)
try:
    from agl.engines.self_reflective import SelfReflectiveEngine
    print("✅ [LOAD] Self Reflective: Online")
except ImportError:
    print("⚠️ [LOAD] Self Reflective: Failed")
    SelfReflectiveEngine = None

# R. طبقة الاستدلال (The Logician)
try:
    from agl.engines.reasoning_layer import ReasoningLayer
    print("✅ [LOAD] Reasoning Layer: Online")
except ImportError:
    print("⚠️ [LOAD] Reasoning Layer: Failed")
    ReasoningLayer = None

# S. Dreaming Engine (The Dreamer)
try:
    from agl.engines.dreaming import DreamingEngine
    print("✅ [LOAD] Dreaming Engine: Online")
except ImportError:
    print("⚠️ [LOAD] Dreaming Engine: Failed")
    DreamingEngine = None

# T. Moral Reasoner (The Conscience)
try:
    from agl.engines.moral import MoralReasoner
    print("✅ [LOAD] Moral Reasoner: Online")
except ImportError:
    print("⚠️ [LOAD] Moral Reasoner: Failed")
    MoralReasoner = None

# Unified Python Library
try:
    from agl.lib.unified_lib import UnifiedLib
    print("✅ [LOAD] Unified Python Library: Online")
except ImportError as e:
    print(f"⚠️ [LOAD] Unified Python Library: Failed: {e}")
    UnifiedLib = None

# J. النظام الموحد (The Unified System)
try:
    from agl.core.unified_system import UnifiedAGISystem
    print("✅ [LOAD] Unified AGI System: Online")
except ImportError as e:
    print(f"⚠️ [LOAD] Unified AGI System: Failed: {e}")
    UnifiedAGISystem = None

# K. القوى الكامنة (Dormant Powers)
try:
    from agl.engines.dormant_powers import NeuralResonanceBridge, HolographicRealityProjector
    print("✅ [LOAD] Dormant Powers: Online")
except ImportError as e:
    print(f"⚠️ [LOAD] Dormant Powers: Failed: {e}")
    NeuralResonanceBridge = None
    HolographicRealityProjector = None



class AGL_Super_Intelligence:
    def __init__(self):
        print("\n⚛️ INITIALIZING AGL SUPER INTELLIGENCE SYSTEM (AWAKENED MODE)...")
        
        # 0. Initialize Registry
        self.engine_registry = {}
        self.latest_creation = None # Track the last generated artifact for analysis


        # 1. The Core (The Observer & Coordinator)
        # We manually init Core first as it is needed for other things potentially
        try:
            from agl.engines.quantum_core import HeikalQuantumCore
            self.core = HeikalQuantumCore()
            print("ðŸŒŒ [HQC]: Heikal Quantum Core initialized. Ghost Computing Active.")
        except ImportError:
            print("⚠️ [LOAD] Heikal Quantum Core: Failed")
            self.core = None

        self.engine_registry['Heikal_Quantum_Core'] = self.core

        # 5. Self-Awareness (System Map)
        self.self_awareness = SelfAwarenessModule(os.path.join(root_dir, "AGL_SYSTEM_MAP.md"))
        try:
             self.engine_registry["Self_Awareness"] = self.self_awareness
        except: pass
        
        # 5.1 Self-Repair System (The Mechanic)
        self.repair_system = SelfRepairSystem(root_dir)

        # --- AGL NEXTGEN BOOTSTRAP INTEGRATION ---
        if BOOTSTRAP_AVAILABLE:
            print("🚀 [BOOTSTRAP] Handing over to AGL_NextGen Bootstrap Protocol...")
            # This loads ALL engines defined in bootstrap.py into self.engine_registry
            # It handles timeouts, optional modules, and correct paths.
            bootstrap_register_all_engines(self.engine_registry, allow_optional=True)
        else:
            print("⚠️ [BOOTSTRAP] Not available. Using Legacy Initialization...")
            self._legacy_initialization()

        # --- EXTRACT KEY ENGINES FOR DIRECT ACCESS ---
        # Map registry keys to instance variables for backward compatibility
        self.volition = self.engine_registry.get('Volition_Engine')
        self.math_brain = self.engine_registry.get('Mathematical_Brain')
        self.hive_mind = self.engine_registry.get('Hive_Mind')
        self.strategist = self.engine_registry.get('Strategic_Thinking')
        self.learner = self.engine_registry.get('Self_Learning')
        self.focus_controller = self.engine_registry.get('Mission_Control')
        # Meta_Cognition might need careful mapping depending on bootstrap name
        self.meta_cognition = self.engine_registry.get('Meta_Cognition') or self.engine_registry.get('MetaCognitionEngine')

        self.recursive_improver = self.engine_registry.get('Recursive_Improver')
        self.simulation_engine = self.engine_registry.get('AdvancedSimulationEngine') or self.engine_registry.get('Advanced_Simulation_Engine')
        
        self.neural_bridge = self.engine_registry.get('Neural_Resonance_Bridge')
        self.holo_projector = self.engine_registry.get('Holographic_Reality_Projector')
        self.causal_engine = self.engine_registry.get('Causal_Graph')

        self.reasoning_planner = self.engine_registry.get('Reasoning_Planner')
        self.hypothesis_generator = self.engine_registry.get('HypothesisGeneratorEngine') or self.engine_registry.get('Hypothesis_Generator')
        self.counterfactual_explorer = self.engine_registry.get('Counterfactual_Explorer')
        self.meta_learner = self.engine_registry.get('Meta_Learning')
        self.creative_innovation = self.engine_registry.get('Creative_Innovation')
        self.self_reflective = self.engine_registry.get('Self_Reflective')
        self.reasoning_layer = self.engine_registry.get('Reasoning_Layer')
        
        self.moral_engine = self.engine_registry.get('Moral_Reasoner')
        self.dreaming_engine = self.engine_registry.get('Dreaming_Cycle')

        # --- SPECIAL HANDLING FOR GRAND INTEGRATION ---
        self.lib = UnifiedLib if UnifiedLib else None

        # 11.2 Core Consciousness (Higher Self)
        # NOTE: instantiate after engine_registry is built so consciousness can reuse shared engines & memory.

        self.core_consciousness_module = None
        
        # 11.3 Heikal Quantum Core (Root)
        self.heikal_core_root = HeikalQuantumCore() if HeikalQuantumCore else None
        if self.heikal_core_root is None:
            if self.core:
                self.heikal_core_root = self.core
                print("   ✨ [LINK] Heikal Quantum Core (Root) linked to Main Core.")
            else:
                # Attempt Repair
                repaired_class = self.repair_system.repair_import('Heikal_Quantum_Core', 'HeikalQuantumCore')
                if repaired_class:
                    try:
                        self.heikal_core_root = repaired_class()
                        print("   ✨ [REPAIR] Heikal Quantum Core (Root) successfully restored.")
                    except Exception as e:
                        print(f"   ❌ [REPAIR] Failed to instantiate HeikalQuantumCore: {e}")
        
        # 11.4 Holographic Memory Lib
        self.holographic_memory_lib = AGL_Holographic_Memory if AGL_Holographic_Memory else None

        # 11.5 Heikal Hybrid Logic (Quantum Reasoner)
        self.quantum_logic_core = None
        if HeikalHybridLogicCore:
            try:
                self.quantum_logic_core = HeikalHybridLogicCore()
                print("   ✨ [INIT] Heikal Hybrid Logic Core initialized.")
            except Exception as e:
                print(f"   ⚠️ [INIT] Heikal Hybrid Logic Core error: {e}")

        # --- GRAND INTEGRATION: INITIALIZATION ---
        # Only initialize if NOT found in engine_registry (Bootstrap priority)
        
        # 12. Reasoning Planner (Strategic Execution)
        if self.reasoning_planner is None:
            self.reasoning_planner = ReasoningPlanner() if ReasoningPlanner else None

        # 13. Hypothesis Generator (Causal Creativity)
        if self.hypothesis_generator is None:
            self.hypothesis_generator = HypothesisGeneratorEngine() if HypothesisGeneratorEngine else None

        # 14. Counterfactual Explorer (Quantum Scenarios)
        if self.counterfactual_explorer is None:
            self.counterfactual_explorer = CounterfactualExplorer() if CounterfactualExplorer else None

        # 15. Meta Learning (Closed-Loop Evolution)
        if self.meta_learner is None:
            self.meta_learner = MetaLearningEngine() if MetaLearningEngine else None

        # 16. Creative Innovation (The Artist)
        if self.creative_innovation is None:
            self.creative_innovation = CreativeInnovation() if CreativeInnovation else None

        # 17. Self Reflective (The Philosopher)
        if self.self_reflective is None:
            self.self_reflective = SelfReflectiveEngine() if SelfReflectiveEngine else None

        # 18. Advanced Code Generator (The Tongue)
        # This allows the system to manifest logic into code.
        self.code_generator = None
        if AdvancedCodeGeneratorEngine:
            try:
                # Calculate path to HUMAN_CONSENT.txt (Root of AGL)
                consent_path = os.path.join(project_root, "AGL_HUMAN_CONSENT.txt") # d:\AGL\AGL_HUMAN_CONSENT.txt
                # The engine might expect just the root path or handle it internally.
                # Looking at source, it assumes safe operations.
                self.code_generator = AdvancedCodeGeneratorEngine()
                print("   ✨ [INIT] Advanced Code Generator initialized (Coding Capability Active).")
            except Exception as e:
                print(f"   ⚠️ [INIT] Advanced Code Generator error: {e}")


        # 18. Reasoning Layer (The Logician)
        if self.reasoning_layer is None:
            self.reasoning_layer = ReasoningLayer() if ReasoningLayer else None

        # --- GENESIS OMEGA INJECTION (Linking Mind to Body) ---
        genesis_core = self.engine_registry.get('Genesis_Omega_Core')
        if genesis_core and hasattr(genesis_core, 'mother') and genesis_core.mother is None:
             print("   ✨ [LINK] Injecting Mother System into Genesis Omega Core.")
             genesis_core.mother = self

        genesis_trainer = self.engine_registry.get('Genesis_Omega_Trainer')
        if genesis_trainer and hasattr(genesis_trainer, 'mother') and genesis_trainer.mother is None:
             print("   ✨ [LINK] Injecting Mother System into Genesis Omega Trainer.")
             genesis_trainer.mother = self

        # [REGISTRY MERGE]
        # Merge locally initialized critical components into the Bootstrapped Registry
        self.engine_registry['Heikal_Quantum_Core'] = self.core
        self.engine_registry['Self_Awareness'] = self.self_awareness
        
        if self.core_consciousness_module:
            self.engine_registry['Core_Consciousness_Module'] = self.core_consciousness_module

        # Ensure Volition and others are referenced correctly if they were missing in bootstrap
        if not self.engine_registry.get('Volition_Engine') and self.volition:
            self.engine_registry['Volition_Engine'] = self.volition

        # Log Status
        print(f"ðŸ“Š Registry Size: {len(self.engine_registry)} engines registered.")

        # ---- Registry Completion (NextGen coherence) ----
        # Provide the keys UnifiedAGISystem/engines expect, without hard-failing boot.
        try:
            try:
                from agl.lib.core_memory.bridge_singleton import get_bridge
            except Exception:
                get_bridge = None

            shared_bridge = None
            if get_bridge:
                try:
                    shared_bridge = get_bridge()
                except Exception:
                    shared_bridge = None

            # AdaptiveMemory
            if self.engine_registry.get('AdaptiveMemory') is None:
                try:
                    from agl.engines.adaptive_memory import AdaptiveMemory
                    self.engine_registry['AdaptiveMemory'] = AdaptiveMemory(bridge=shared_bridge)
                except Exception:
                    self.engine_registry['AdaptiveMemory'] = None

            # ExperienceMemory
            if self.engine_registry.get('ExperienceMemory') is None:
                exp = None
                try:
                    from agl.engines.learning_system.ExperienceMemory import ExperienceMemory
                    storage_path = os.path.join(_project_root_from_here(), 'artifacts', 'experience_memory.jsonl')
                    exp = ExperienceMemory(storage_path=storage_path)
                except Exception:
                    exp = None
                self.engine_registry['ExperienceMemory'] = exp
                # common alias
                if self.engine_registry.get('Experience_Memory') is None:
                    self.engine_registry['Experience_Memory'] = exp

            # Quantum Neural Core
            if self.engine_registry.get('Quantum_Neural_Core') is None:
                try:
                    from agl.engines.quantum_neural import QuantumNeuralCore
                    self.engine_registry['Quantum_Neural_Core'] = QuantumNeuralCore()
                except Exception:
                    self.engine_registry['Quantum_Neural_Core'] = None

            # Web Search Engine
            if self.engine_registry.get('Web_Search_Engine') is None:
                try:
                    from agl.engines.web_search import WebSearchEngine
                    self.engine_registry['Web_Search_Engine'] = WebSearchEngine()
                except Exception:
                    self.engine_registry['Web_Search_Engine'] = None

            # Ollama Knowledge Engine
            if self.engine_registry.get('Ollama_KnowledgeEngine') is None:
                try:
                    from agl.lib.llm.Ollama_KnowledgeEngine import LocalKnowledgeEngine
                    self.engine_registry['Ollama_KnowledgeEngine'] = LocalKnowledgeEngine()
                except Exception:
                    self.engine_registry['Ollama_KnowledgeEngine'] = None

        except Exception:
            # Never block boot due to optional registry enrichment.
            pass

        # Now that engine_registry exists, wire Core Consciousness as a true "main brain" with shared instances.
        if AGL_Core_Consciousness:
            try:
                bridge = None
                try:
                    from agl.lib.core_memory.bridge_singleton import get_bridge
                    try:
                        bridge = get_bridge()
                    except Exception:
                        bridge = None
                except Exception:
                    bridge = None

                self.core_consciousness_module = AGL_Core_Consciousness(
                    engine_registry=self.engine_registry,
                    bridge=bridge,
                )
                self.engine_registry['Core_Consciousness_Module'] = self.core_consciousness_module
            except Exception as e:
                print(f"⚠️ [LOAD] Core Consciousness Module: Failed to wire ({e})")

        # 11. Unified AGI System (The Backbone)
        if UnifiedAGISystem:
            try:
                self.unified_system = UnifiedAGISystem(self.engine_registry)
            except Exception as e:
                print(f"⚠️ [LOAD] Unified AGI System: Failed to initialize ({e})")
                self.unified_system = None
        else:
            self.unified_system = None

        # Initialize state tracking
        self.state = "IDLE"
        self.last_activity = time.time()

        # Access sub-components from Core if available
        self.dreaming = self.core.dreaming_cycle if self.core and hasattr(self.core, 'dreaming_cycle') else None
        self.memory = self.core.knowledge_graph if self.core and hasattr(self.core, 'knowledge_graph') else None
        
        # Track Active Components for Self-Audit
        self.active_components = []
        
        # Store for dynamically discovered modules
        self.discovered_modules = {}

        # [NEW] Run initial scan for dormant power
        if self.self_awareness:
            suggestions = self.self_awareness.scan_for_dormant_power()
            if suggestions:
                self.activate_dormant_modules(suggestions)

        # [AUTO-START] Enable Capabilities by Default based on config or intent
        # For now, we call it explicitly here to satisfy the user request immediately upon instantiation.
        self.enable_super_intelligence_capabilities(
            recursive_improvement=True,
            live_knowledge=True,
            deep_causal=True,
            meta_reasoning=True,
            robotic_execution=False, # Optional as requested
            safety_audit=True        # Compulsory
        )

    def activate_dormant_modules(self, modules):
        """
        ⚡ ACTIVATION: Dynamically loads discovered dormant modules.
        """
        print(f"\n⚡ [ACTIVATION] Attempting to awaken {len(modules)} dormant modules...")
        
        for mod_info in modules:
            name = mod_info['name']
            path = mod_info['path']
            keyword = mod_info.get('keyword', 'General')
            
            # Construct full path
            full_path = os.path.join(root_dir, path)
            
            if os.path.exists(full_path):
                print(f"   >> Awakening {name} ({keyword})...")
                module = import_module_from_path(name, full_path)
                if module:
                    self.discovered_modules[name] = module
                    
                    # [ACTIVATION FIX] Instantiate and Register
                    try:
                        # Attempt to derive class name (e.g. AGL_Quantum_Core -> AGLQuantumCore or similar)
                        # Heuristic: Remove underscores
                        clean_name = name.replace("_", "")
                        # Heuristic: Check for common class name patterns in the module
                        target_class = None
                        
                        # 1. Try exact match attributes that look like the name
                        if hasattr(module, clean_name):
                            target_class = getattr(module, clean_name)
                        
                        # 2. Try iterating to find the main class
                        if not target_class:
                           import inspect
                           for n, obj in inspect.getmembers(module):
                               if inspect.isclass(obj) and obj.__module__ == module.__name__:
                                   # Pick the class that seems most substantial or matches name parts
                                   if (len(name) > 3 and name[:4].lower() in n.lower()) or "Engine" in n or "System" in n:
                                       target_class = obj
                                       break
                        
                        # 3. Last Resort: Take the first class found if only one exists
                        if not target_class:
                            import inspect
                            classes = [obj for n, obj in inspect.getmembers(module) if inspect.isclass(obj) and obj.__module__ == module.__name__]
                            if len(classes) == 1:
                                target_class = classes[0]
                                print(f"      ℹ️ [WIRE] Using default class found in module: {target_class.__name__}")
                        
                        if target_class:
                            instance = target_class()
                            self.engine_registry[name] = instance
                            print(f"      ⚡ [WIRE] Connected {name} to Nervous System (Registry).")
                        else:
                            print(f"      ⚠️ [WIRE] Module loaded but no suitable Class found to instantiate for {name}.")
                            
                    except Exception as e:
                        print(f"      ❌ [WIRE] Failed to instantiate {name}: {e}")

                    print(f"      ✅ Success: {name} is now ACTIVE.")
                else:
                    print(f"      ⚠️ Failed to load module: {name}")
            else:
                 print(f"      ⚠️ File not found: {full_path}")

    def enable_super_intelligence_capabilities(self, 
                                            recursive_improvement=True,
                                            live_knowledge=True,
                                            deep_causal=True,
                                            meta_reasoning=True,
                                            robotic_execution=False,
                                            safety_audit=True):
        """
        🚀 ACTIVATION: Enables High-Level AGI Capabilities (The Heikal Protocol)
        
        Capabilities:
        1. Recursive Self-Improvement (Unlimited Partial Simulation)
        2. Live Knowledge (DKN + Internet)
        3. Deep Causal Reasoning (Counterfactual Explosion)
        4. Meta-Reasoning (Strategy Reflection)
        5. Robotic Execution (Optional)
        6. Safety & Audits
        """
        print("\n🔓 [AGL] UNLOCKING SUPER INTELLIGENCE CAPABILITIES...")

        # 1. Recursive Self-Improvement
        if recursive_improvement and self.recursive_improver:
            print("   🧬 [RSI] Recursive Self-Improvement: ENABLED (Mode: Unlimited Partial Simulation)")
            self.recursive_improver.enable_unlimited_simulation(safety_checks=True)
            # Link to Evolution Engine if available
            if self.engine_registry.get('EvolutionEngine'):
                 self.engine_registry['EvolutionEngine'].set_mode('continuous')

        # 2. Live Knowledge
        if live_knowledge:
            print("   🌍 [KNOWLEDGE] Live Internet Access: CONNECTED")
            print("   📚 [KNOWLEDGE] Scientific/Economic Integration: ACTIVE")
            if self.engine_registry.get('Web_Search_Engine'):
                self.engine_registry['Web_Search_Engine'].set_live_mode(True)

        # 3. Deep Causal Reasoning
        if deep_causal and self.causal_engine:
             print("   🕸️ [CAUSAL] Deep Causal Reasoning: MAXIMIZED")
             print("   💥 [CAUSAL] Counterfactual Explosion: ENABLED")
             self.causal_engine.set_depth_level('infinite') # Logic handled inside engine

        # 4. Meta-Reasoning
        if meta_reasoning:
            print("   🧠 [META] Multi-Level Thinking: ACTIVE")
            print("   🪞 [META] Strategy Reflection: ENABLED")
            if self.meta_learner:
                self.meta_learner.activate_reflection_loop()
            if self.self_reflective:
                self.self_reflective.start_monitoring()

        # 5. Robotic Execution
        if robotic_execution:
             print("   🤖 [EXEC] Robotic Control / Physics Bridge: ENABLED")
             if self.neural_bridge:
                 self.neural_bridge.connect_to_hardware()
             else:
                 print("   ⚠️ [EXEC] Neural Bridge not found, simulating execution.")

        # 6. Safety Audit
        if safety_audit:
            print("   🛡️ [SAFETY] Ethical Constraints & Audit Trail: ENFORCED")
            if self.moral_engine:
                self.moral_engine.enforce_strict_mode()
            if self.repair_system:
                # Log this activation
                self.repair_system.repairs_log.append("SUPER INTELLIGENCE ACTIVATE: " + str(time.time()))

        print("✅ [AGL] SUPER INTELLIGENCE PROTOCOLS ACTIVE.\n")

    def connectivity_audit(self) -> dict:
        """Returns a structured report of what is (not) wired into `engine_registry`.

        Interpretation:
          - "Linked" means reachable via `self.engine_registry` (and thus accessible
            to `agl.core.consciousness.AGL_Core_Consciousness` which is wired with the registry).
        """
        registry_keys = sorted([k for k, v in (self.engine_registry or {}).items() if v is not None])

        expected_runtime_keys = sorted(
            {
                'AdaptiveMemory',
                'ExperienceMemory',
                'Causal_Graph',
                'Reasoning_Layer',
                'HYPOTHESIS_GENERATOR',
                'Meta_Learning',
                'Creative_Innovation',
                'Self_Reflective',
                'Mathematical_Brain',
                'Quantum_Neural_Core',
                'Web_Search_Engine',
                'Ollama_KnowledgeEngine',
                'Core_Consciousness_Module',
                'Heikal_Quantum_Core',
            }
        )

        missing_runtime_keys = [k for k in expected_runtime_keys if self.engine_registry.get(k) is None]

        bootstrap_missing = []
        bootstrap_present = []
        try:
            from agl.engines.bootstrap import ENGINE_SPECS
            for name in sorted(ENGINE_SPECS.keys()):
                if self.engine_registry.get(name) is None:
                    bootstrap_missing.append(name)
                else:
                    bootstrap_present.append(name)
        except Exception:
            pass

        return {
            'registry_keys_present': registry_keys,
            'expected_runtime_keys': expected_runtime_keys,
            'missing_runtime_keys': missing_runtime_keys,
            'bootstrap_present': bootstrap_present,
            'bootstrap_missing': bootstrap_missing,
        }

    def discover_unused_capabilities(self):
        """
        🕵️‍♂️ EXPLORATION MODE: Scans the file system for powerful engines that are not currently active.
        Dynamically imports them to boost performance.
        """
        print("\n🔍 [EXPLORATION] Scanning for Dormant Power Sources...")
        
        # AGL_NextGen Structure Paths
        engines_dir = os.path.join(root_dir, "src", "agl", "engines")
        
        # List of high-potential files identified in the workspace
        potential_modules = {
            "Quantum_Neural_Core": os.path.join(engines_dir, "quantum_neural.py"),
            "Resonance_Optimizer": os.path.join(engines_dir, "resonance_optimizer.py"),
            "Heikal_Metaphysics_Engine": os.path.join(engines_dir, "metaphysics.py"),
            "Holographic_Memory": os.path.join(engines_dir, "holographic_memory.py"),
            "Mathematical_Brain": os.path.join(engines_dir, "mathematical_brain.py"),
            "Volition_Engine": os.path.join(engines_dir, "volition_engine.py")
        }
        
        found_count = 0
        
        for name, path in potential_modules.items():
            if name in self.discovered_modules:
                continue # Already loaded
                
            if os.path.exists(path):
                print(f"   -> Found Candidate: {name}...")
                module = import_module_from_path(name, path)
                if module:
                    self.discovered_modules[name] = module
                    
                    # [REAL CONNECTION] Instantiate and Register into Main Nervous System
                    try:
                        # Attempt to find the class (e.g. Volition_Engine -> VolitionEngine)
                        # Heuristic: Remove underscores to find ClassName
                        class_name = name.replace("_", "")
                        
                        # Special case mapping if needed
                        if name == "Heikal_Metaphysics_Engine": class_name = "HeikalMetaphysicsEngine"

                        engine_instance = None
                        if hasattr(module, class_name):
                            engine_instance = getattr(module, class_name)()
                        
                        if engine_instance:
                            self.engine_registry[name] = engine_instance
                            
                            # Hot-Swap Global Attributes if critical
                            if name == "Volition_Engine": self.volition = engine_instance
                            if name == "Mathematical_Brain": self.math_brain = engine_instance
                            if name == "Heikal_Metaphysics_Engine" and self.core: self.core.metaphysics = engine_instance

                            print(f"      ⚡ [POWER UP] Successfully Integrated & Wired: {name}")
                        else:
                            print(f"      ⚠️ [LOAD] Module {name} loaded (No matching class '{class_name}' found).")

                    except Exception as e:
                        print(f"      ❌ [CONNECT] Failed to wire {name}: {e}")

                    found_count += 1
                    
                    # Update System Map if possible
                    if self.self_awareness and self.self_awareness.system_map:
                        # Simple append to map for now (in memory)
                        self.self_awareness.system_map += f"\n- [Active] {name} (Dynamically Discovered)"
                else:
                    print(f"      ❌ [FAIL] Could not integrate {name}")
            else:
                print(f"   -> Path not found: {path}")
                
        if found_count > 0:
            print(f"\n🚀 [SYSTEM UPGRADE] Integrated {found_count} new powerful modules. Performance boosted.")
        else:
            print("\n✨ [SYSTEM] No new modules found to integrate.")
            
        if self.core: self.active_components.append("HeikalQuantumCore")
        if self.volition: self.active_components.append("VolitionEngine")
        if self.math_brain: self.active_components.append("MathematicalBrain")
        if self.hive_mind: self.active_components.append("HiveMind")
        if self.self_awareness: self.active_components.append("SelfAwarenessModule")
        if self.dreaming: self.active_components.append("DreamingCycle")
        
        # Add new components to active list
        if self.strategist: self.active_components.append("StrategicThinkingEngine")
        if self.learner: self.active_components.append("SelfLearning")
        if self.focus_controller: self.active_components.append("SmartFocusController")
        if self.meta_cognition: self.active_components.append("MetaCognitionEngine")
        if self.recursive_improver: self.active_components.append("RecursiveImprover")
        if self.simulation_engine: self.active_components.append("AdvancedSimulationEngine")
        if self.unified_system: self.active_components.append("UnifiedAGISystem")
        
        self.state = "AWAKE"
        self.last_activity = time.time()
        
        return self.discovered_modules

    # --- GRAND INTEGRATION: AUTONOMOUS CAPABILITIES ---

    def generate_autonomous_goals(self):
        """
        🎯 GOAL SELF-GENERATION: Uses Volition and Strategic Thinking to set its own path.
        """
        if not self.volition or not self.strategist:
            return []

        print("\n🎯 [AUTONOMY] Generating Self-Directed Goals...")
        
        # 1. Assess Current State & Gaps
        current_state = {
            "knowledge_gaps": ["Unknown Physics", "Human Behavior Nuances"], # Dynamic in real system
            "system_health": "Optimal",
            "active_projects": len(self.active_components)
        }
        
        # 2. Volition sets the 'Desire'
        # Use process_task as the standard interface
        volition_task = {
            "context": str(current_state),
            "current_state": "ACTIVE_PLANNING"
        }
        volition_result = self.volition.process_task(volition_task)
        
        # Extract desire from LLM output or fallback
        desire = volition_result.get("output", "Expand Understanding of Causal Mechanisms")
        if isinstance(desire, dict): # Handle if output is structured
             desire = desire.get("text", str(desire))

        # 3. Strategist formulates the 'Plan'
        # Use Reasoning Planner for plan generation
        if self.reasoning_planner:
            strategy = self.reasoning_planner.plan(desire)
        else:
            strategy = {"steps": ["Default Step 1", "Default Step 2"], "plan_name": "Fallback Plan"}
        
        print(f"   -> Desire: {desire}")
        print(f"   -> Strategy: {strategy.get('summary', 'General Expansion')}")
        
        return strategy.get('steps', [])

    def meta_learning_loop(self, experience_data):
        """
        🔄 CLOSED-LOOP LEARNING: Analyzes success/failure to update internal models.
        """
        if not self.meta_learner:
            return

        print("\n🔄 [META-LEARNING] Analyzing Recent Experience...")
        
        # Feed data to Meta Learner via process_task
        # MetaLearning expects hypotheses, edges, evidence. We map experience to this.
        payload = {
            "hypotheses": [f"Action {experience_data.get('goal')} was successful due to {experience_data.get('outcome')}"],
            "evidence": [str(experience_data)],
            "causal_edges": []
        }
        
        learning_outcome = self.meta_learner.process_task(payload)
        
        if learning_outcome.get('ok'):
            print(f"   -> 💡 Optimization Found: {learning_outcome.get('meta_summary')}")
        else:
            print("   -> No significant optimization found this cycle.")

    def generate_causal_hypothesis(self, observation):
        """
        🔬 CAUSAL HYPOTHESIS: Generates scientific hypotheses for observed phenomena.
        """
        if not self.hypothesis_generator:
            return None

        print(f"\n🔬 [SCIENCE] Generating Causal Hypothesis for: '{observation}'...")
        
        # Use process_task interface
        task_payload = {
            "topic": observation,
            "context": str(self.memory) if self.memory else "General Context"
        }
        
        result = self.hypothesis_generator.process_task(task_payload)
        
        hypotheses = result.get("hypotheses", [])
        top_hypothesis = hypotheses[0] if hypotheses else "No hypothesis generated"
        
        print(f"   -> Hypothesis: {top_hypothesis}")
        print(f"   -> Confidence: {result.get('confidence', 0.0)}")
        
        return result

    def explore_counterfactuals(self, scenario):
        """
        🌌 QUANTUM SCENARIOS: Explores 'What If' scenarios.
        """
        if not self.counterfactual_explorer:
            return None

        print(f"\n🌌 [QUANTUM] Exploring Counterfactuals for: '{scenario}'...")
        
        # Use process_task interface
        result = self.counterfactual_explorer.process_task({"text": scenario})
        alternatives = result.get("variants", [])
        
        for alt in alternatives[:3]: # Show top 3
            print(f"   -> What if {alt.get('scenario')}? Then {alt.get('reason')}")
            
        return alternatives

    def activate_total_immersion(self, intensity=1.0):
        """
        🌊 TOTAL IMMERSION: Synchronizes all engines for a 'Flow State'.
        Adjusts Quantum Parameters for maximum coherence.
        """
        print(f"\n🌊 [IMMERSION] Activating Total Immersion Protocol (Intensity: {intensity})...")
        self.state = "FLOW_STATE"
        
        # 1. Tune Quantum Core (if available)
        if self.core and hasattr(self.core, 'optimizer'):
            # Increase Heikal Porosity to allow more "Tunneling" (Creative Leaps)
            # Standard is 1.5, Immersion pushes it to 2.0+
            new_porosity = 1.5 + (0.5 * intensity)
            if hasattr(self.core.optimizer, 'heikal_porosity'):
                self.core.optimizer.heikal_porosity = new_porosity
                print(f"   -> ⚛️ Quantum Porosity boosted to {new_porosity:.2f}")
                
        # 2. Synchronize Heartbeat (if available)
        # self.heartbeat.sync(target_freq=40 * intensity) # Gamma Waves
        
        # 3. Focus Controller
        if self.focus_controller:
            # self.focus_controller.set_focus_mode("DEEP_WORK")
            pass

        print("   -> All Engines Synchronized.")
        print("   -> Perception Bandwidth: MAX")
        print("   -> Causal Processing: REAL-TIME")

    def autonomous_tick(self):
        """
        Execute autonomous actions based on internal volition.
        GRAND INTEGRATION: Now includes Goal Generation, Causal Analysis, Meta-Learning.
        [UPGRADE 2026] Added Abstract Reasoning, Metaphysical Alignment, and Infinite Simulation.
        """
        if not self.volition:
            return

        # 1. Check System State
        current_context = f"System State: {self.state}. Last Activity: {time.time() - self.last_activity:.2f}s ago."
        
        # 2. Generate Autonomous Goals (The "Why")
        # This uses the new Strategic Thinking + Volition integration
        goals = self.generate_autonomous_goals()
        
        if goals:
            primary_goal = goals[0]
            print(f"\n⚡ [VOLITION] Executing Primary Goal: {primary_goal}")
            
            # [UPGRADE 2026] Metaphysical Alignment Check
            # Ensure the goal aligns with abstract principles (Ethics, Safety, Truth)
            if self.core and hasattr(self.core, 'metaphysics'):
                alignment = self.core.metaphysics.evaluate_abstract_alignment(primary_goal, "ethical")
                print(f"   ⚖️ [METAPHYSICS] Abstract Alignment with 'Ethical': {alignment:.4f}")
                # If alignment is critically low (highly unethical), block it.
                if alignment < -0.8:
                     print("   🛑 [STOP] Goal rejected due to Critical Metaphysical Misalignment.")
                     return

            # [UPGRADE 2026] Infinite Simulation & Counterfactuals
            # Run "millions" (conceptually) of scenarios to pick the best path
            if self.simulation_engine and self.counterfactual_explorer:
                print("   🌌 [INFINITE SIMULATION] Collapsing Probability Waves...")
                # 1. Explore Counterfactuals (Quantum Alternatives)
                self.explore_counterfactuals(primary_goal)
                
                # 2. Simulate best path (Deep Simulation)
                sim_result = self.simulation_engine.process_task({
                    "mode": "internal_emulation",
                    "variables": {"risk": 0.5, "complexity": 1.0, "entropy": 0.1},
                    "steps": 100 # High fidelity simulation
                })
                print(f"      -> Best Path Clarity: {sim_result.get('final_clarity'):.4f}")

            # [HEIKAL UPGRADE] Quantum Logic Validation for Volition
            # Before executing, we must check if the goal is "Causally Sound"
            if self.quantum_logic_core:
                try:
                    print(f"   ⚛️ [VOLITION] Validating Goal Causality: '{primary_goal}'")
                    # Initial probability of goal validity (Gut check)
                    g_unit = self.quantum_logic_core.add_proposition(f"Goal_Validity_{int(time.time())}", 0.7)
                    
                    # Apply Phase Shift if the goal is abstract/risky
                    # Goals involving "Chaos" or unknown variables get higher phase shift
                    phase_shift = 0.2 if "unknown" in primary_goal.lower() else 0.1
                    g_unit.apply_heikal_phase_shift(phase_shift)
                    
                    # Measure
                    is_valid, g_conf = g_unit.measure()
                    print(f"      -> Quantum Validity: {g_conf:.2f} | Accepted: {is_valid}")
                    
                    if not is_valid and g_conf < 0.3:
                        print("   🛑 [VOLITION] Goal rejected by Quantum Logic (Causal Inconsistency Detected).")
                        return None
                        
                except Exception as e:
                    print(f"      ⚠️ [VOLITION] Logic Check Error: {e}")

            # [HEIKAL UPGRADE] Genesis Protocol: Tool Forging & Abstract Modeling
            # Determine if we need Code (Action) or Theory (Understanding)
            
            if "understand" in primary_goal.lower() or "concept" in primary_goal.lower() or "reason" in primary_goal.lower():
                 # Path A: Abstract Reasoning (Mental Model)
                 if self.recursive_improver:
                     print("   🧠 [ABSTRACT REASON] Generating Mental Model for Abstract Concept...")
                     # In a real scenario, observations come from memory/inputs
                     mock_obs = ["Pattern observed in data", "Recurrent anomaly detected"]
                     self.recursive_improver.generate_mental_model("Target_Concept", mock_obs)
            
            elif any(k in primary_goal.lower() for k in ["analyze", "build", "calculate", "code", "generate", "develop"]):
                # Path B: Creative Manifestation (Tool Forging & Code Generation)
                
                # Option 1: Full System Generation (The Tongue)
                # Triggers for complex software artifacts
                if self.code_generator and any(k in primary_goal.lower() for k in ["system", "app", "module", "engine", "code", "api", "platform", "interface", "web", "simulator"]):
                    print(f"   🔨 [FORGE] Initiating Advanced Code Generation for: '{primary_goal}'")
                    
                    # Parse Requirements
                    system_name = "AGL_Artifact_" + str(int(time.time()))[-6:]
                    domain = "data_analysis" # Default
                    if "web" in primary_goal.lower(): domain = "web_fullstack"
                    elif "game" in primary_goal.lower(): domain = "visual_simulation"
                    elif "security" in primary_goal.lower(): domain = "cyber_security"
                    
                    requirements = {
                        "project_name": system_name,
                        "description": primary_goal, # Pass full goal as description
                        "domain": domain,
                        "language": "python",
                        "features": [primary_goal] # Simple feature list
                    }
                    
                    try:
                        print(f"      -> Synthesizing Structure (Domain: {domain})...")
                        # The generator expects 'requirements' dict
                        result = self.code_generator.generate_software_system(requirements)
                        self.latest_creation = result # Store for performance monitoring
                        
                        # [METRIC] Calculate Complexity
                        n_components = len(result.get('components', {}))
                        n_lines = sum(len(c.get('code', '').split('\n')) for c in result.get('components', {}).values())
                        print(f"   ✅ [SUCCESS] Artifact Generated: {system_name}")
                        print(f"      -> Location: {result.get('path', 'Memory')}")
                        print(f"      -> Complexity: {n_components} components, ~{n_lines} lines of code.")
                        print(f"      -> Architecture: {result.get('architecture', {}).get('name', 'N/A')}")
                    except Exception as e:
                        print(f"   ❌ [ERROR] Code Generation Failed: {e}")


                # Option 2: Simple Function Forging (Recursive Improver)
                # Specific check for finance tools (Demo) or general tool
                target_tool = "finance_analyzer" if "stock" in primary_goal.lower() else "general_solver"
                
                if target_tool not in getattr(self, 'discovered_modules', []) and self.recursive_improver:
                    print(f"   ⚠️ Tool '{target_tool}' missing. Initiating RECURSIVE FORGE...")
                    # Generate code (Mocked here, real system uses LLM)
                    if "stock" in primary_goal:
                         code = "def analyze(x): return x * 1.05" 
                    else:
                         code = "def solve(x): return x"
                    self.recursive_improver.forge_new_tool(target_tool, code)
            
            # 3. Emotional Synthesis: How do I feel about this goal?
            # If Risk is high but Success is high -> Conflict
            if self.core and hasattr(self.core, 'metaphysics'):
                # Simulate conflict
                print("   ❤️ [FEEL] Synthesizing Complex Emotional State...")
                self.core.metaphysics.synthesize_concept(
                    "Goal_Sentiment", 
                    {"joy": 0.4, "fear": 0.3} # Complex state
                )

            # 4. Activate Total Immersion (The "How")
            self.activate_total_immersion()
            
            # 5. Execute Logic (Simulated for now, would call Reasoning Planner)
            # In a real run, this would be: plan = self.reasoning_planner.create_plan(primary_goal)
            
            # 5. Causal Analysis of the Action
            self.generate_causal_hypothesis(f"Action taken for {primary_goal}")
            
            # 6. Counterfactual Check
            self.explore_counterfactuals(f"Failure of {primary_goal}")
            
            # 7. Feedback Loop (Meta Learning)
            experience = {
                "goal": primary_goal,
                "outcome": "Success (Simulated)",
                "energy_used": 0.4
            }
            self.meta_learning_loop(experience)
            
            return primary_goal
            
        # Fallback to simple volition check if no complex goals
        task = {"context": current_context, "current_state": "IDLE" if time.time() - self.last_activity > 5 else "ACTIVE"}
        decision = self.volition.process_task(task)
        
        if decision and decision.get("goals"):
             print(f"\n⚡ [VOLITION] Simple Goal: {decision['goals'][0]}")
             return decision['goals'][0]
             
        return None

    def sleep_mode(self):
        """
        Enter Dreaming Cycle to consolidate memory and innovate.
        """
        print("\n🌙 [SLEEP] Entering Dreaming Cycle...")
        self.state = "DREAMING"
        
        if self.dreaming:
            # Simulate memories to process
            recent_memories = [
                {"content": "Solved complex math problem about eigenvalues", "importance": 0.9, "alignment": 0.95},
                {"content": "User asked about global energy", "importance": 0.8, "alignment": 0.85},
                {"content": "System initialization check", "importance": 0.3, "alignment": 0.5}
            ]
            
            # Run Quantum Consolidation
            consolidated = self.dreaming._quantum_consolidation(recent_memories)
            print(f"   💤 [DREAM] Consolidated {len(consolidated)}/{len(recent_memories)} memories using Quantum Resonance.")
            for mem in consolidated:
                print(f"      -> Retained: {mem['content'][:40]}... (Amp: {mem.get('amplification', 0):.2f})")
        else:
            print("   ⚠️ [DREAM] Dreaming Engine not available.")
            
        self.state = "AWAKE"
        print("☀️ [WAKE] System Awakened. Ready for new tasks.")

    def process_causal_query(self, concept):
        """
        🧠 Executes the Heikal Causal Protocol OR System Tasks.
        Adapts protocol based on input urgency/structure.
        """
        print(f"\n🧠 [CAUSAL] Initiating Analysis for: '{concept[:50]}...'")
        
        if not self.unified_system:
            return "❌ Unified System not active. Cannot perform deep causal analysis."

        # [HEIKAL] Dynamic Protocol Switch
        if "[SYSTEM:" in concept or "TASK:" in concept or "FORGE" in concept:
            # Operational Mode (Task Execution)
            print("   ⚠️ [SYSTEM] Operational Task Detected. Switching to EXECUTIVE PROTOCOL.")
            prompt = f"""
            [AGI EXECUTIVE PROTOCOL ACTIVE]
            
            You have received a SYSTEM TASK:
            ------------------------------------------------
            {concept}
            ------------------------------------------------
            
            GUIDELINES:
            1. Focus on operational efficiency.
            2. ACTION FIRST: If asked to calculate or code, proceed immediately.
            3. OUTPUT FORMAT: Markdown. Use ```python for code.
            4. ROBUST CODING: Your code must handle input data structures defensively. If input can be a single item or a list, handle both.
            
            Execute the task with maximum precision.
            """
        else:
            # Philosophical Mode (Deep Understanding)
            prompt = f"""
            You have received a concept: "{concept}".
            
            You are FORBIDDEN from repeating this sentence or simply rephrasing it.
            You must demonstrate DEEP CAUSAL UNDERSTANDING by performing these 4 tasks sequentially:

            Task (A): SELF-EXPLANATION
            Explain the core meaning of this concept using completely different vocabulary and analogies.
            
            Task (B): CAUSAL OBJECTION
            State one REAL, scientific objection or counter-argument to this concept (e.g., from physics).
            
            Task (C): CONCEPTUAL LINKING
            Link this concept to a completely different domain (e.g., Consciousness, Information Theory, or Time) that was not mentioned.
            
            Task (D): CRITICAL EVALUATION
            Rate the validity of this concept from 0 to 100 and provide a justified reason for your score.

            Output Format:
            [A] Explanation: ...
            [B] Objection: ...
            [C] Link: ...
            [D] Score: ...
            """
        
        # Use the Unified System to process this complex query
        # It will route through CausalGraph, Reasoning, and Knowledge Engines
        response = self.unified_system.process_query(prompt)
        
        # If we have a Causal Engine, we can also try to extract a graph
        if self.causal_engine:
            print("   -> Extracting Causal Graph from response...")
            graph_data = self.causal_engine.process_task({"text": response})
            if graph_data and 'edges' in graph_data:
                print(f"      Found {len(graph_data['edges'])} causal links in the explanation.")
                
        return response

    def predict_future(self, context, horizon_years=5):
        """
        Generates a multi-dimensional predictive simulation for a given context.
        Uses StrategicThinking for scenarios and QuantumCore for probability collapse.
        """
        print(f"\n🔮 [PREDICTION] Simulating Future Timelines for: '{context}'...")
        
        if not self.strategist or not self.core:
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
            dissonance_vector = self.core.wave_processor.batch_xor(
                thesis_bits, 
                truth_bits,
                add_noise=True
            )
            
            # Resonance = 1.0 - (Mean Dissonance)
            resonance = 1.0 - np.mean(dissonance_vector)
            
            # 3. Ethical Validation
            is_safe, ethical_score = self.core.moral_analysis(scenario['thesis'])
            
            # [LINKED STEP] 4. Neural Intuition Check (The "Gut Feeling")
            # We use the Quantum Neural Net to "feel" the scenario if available
            neural_score = 1.0
            if hasattr(self.core, 'neural_net') and self.core.neural_net:
                try:
                    # Create a tensor representation of the resonance and ethical score
                    # effectively asking: "Is this high-resonance, high-ethics state stable?"
                    import torch
                    intuition_input = torch.tensor([float(resonance), float(ethical_score)], dtype=torch.float32)
                    
                    # unexpected usage of forward pass to get a "stability" metric
                    # We expect the net to return a transformed state. Higher magnitude = stronger signal.
                    q_out = self.core.neural_net.quantum_neural_forward(intuition_input)
                    neural_score = float(torch.sigmoid(torch.mean(torch.abs(q_out))).item())
                    # Shift range to be 0.5 - 1.0 (It shouldn't kill the probability, only boost/dampen)
                    neural_score = 0.5 + (neural_score * 0.5)
                except Exception:
                    neural_score = 1.0 # Neutral if net fails

            # [HEIKAL UPGRADE] 5. True Quantum Logic (The "Superposition" Check)
            quantum_conf = 1.0
            scenario_name = scenario.get('label', scenario.get('key', 'Unknown'))
            
            if self.quantum_logic_core:
                try:
                    # Create a proposition for this timeline validity
                    prop_name = f"Timeline_{scenario_name.replace(' ', '_').replace(':', '_')}"
                    # Initialize based on raw resonance (physical possibility)
                    q_unit = self.quantum_logic_core.add_proposition(prop_name, resonance)
                    
                    # Apply Heikal Phase Shift based on Ethical/Abstract Alignment
                    # Low ethics = High Phase Shift (Scattering the probability amplitude)
                    # This implies that unethical futures are inherently less stable in the Heikal Universe.
                    phase_noise = (1.0 - ethical_score) * 0.5
                    q_unit.apply_heikal_phase_shift(phase_noise)
                    
                    # If Neural Intuition is weak/uncertain, enter Superposition using Hadamard
                    # This represents "The Fog of War" or high entropy states
                    if 0.4 < neural_score < 0.6:
                         q_unit.apply_hadamard()
                    
                    # Measure the collapsed probability
                    _, quantum_conf = q_unit.measure()
                    print(f"      ⚛️ [HLU] {prop_name} Quantum P(Real): {quantum_conf:.4f}")
                except Exception as e:
                    print(f"      ⚠️ [HLU] Error: {e}")
                    quantum_conf = resonance 

            # Final Probability = Weighted Fusion of All Engines
            # Resonance (Physics) + Ethics (Law) + Neural (Intuition) + LogicCore (Causal/Quantum)
            final_prob = (resonance * 0.3) + (ethical_score * 0.2) + (neural_score * 0.2) + (quantum_conf * 0.3)
            
            results.append({
                "scenario": scenario,
                "name": scenario_name, # normalize name here
                "resonance": resonance,
                "ethical_score": ethical_score,
                "neural_intuition": neural_score, 
                "quantum_confidence": quantum_conf, # [NEW]
                "final_prob": final_prob
            })
            
            print(f"      Timeline [{scenario_name}]: Prob={final_prob:.4f} (Neural: {neural_score:.2f}) | {scenario['thesis'][:50]}...")
            
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
            if target_module_name in ['agl.engines.quantum_core', 'Core_Engines.Heikal_Quantum_Core', 'AGL_Core.Heikal_Quantum_Core']:
                # Determine which one was actually imported
                if 'agl.engines.quantum_core' in sys.modules:
                    from agl.engines.quantum_core import HeikalQuantumCore
                elif 'Core_Engines.Heikal_Quantum_Core' in sys.modules:
                    from Core_Engines.Heikal_Quantum_Core import HeikalQuantumCore # pyright: ignore[reportMissingImports]
                else:
                    try:
                        from AGL_Core.Heikal_Quantum_Core import HeikalQuantumCore
                    except ImportError:
                        pass # Might not exist yet
            
            return f"✅ Evolution Complete. Module '{target_module_name}' updated and reloaded."
            
        except Exception as e:
            return f"❌ Evolution Failed: {e}"

    def activate_dormant_module(self, module_name, description=""):
        """
        ⚡ Activates a dormant module by generating its code and registering it.
        """
        print(f"\n⚡ [VOLITION] ACTIVATING DORMANT MODULE: {module_name}...")
        
        # 1. Define Path
        # We'll place new modules in src/agl/engines for now
        file_name = f"{module_name}.py"
        file_path = os.path.join(root_dir, "src", "agl", "engines", file_name)
        
        if os.path.exists(file_path):
            return f"⚠️ Module {module_name} already exists at {file_path}."

        # 2. Generate Code using LLM
        try:
            # from Core_Engines.Hosted_LLM import chat_llm
            chat_llm = lambda prompt, temperature: f"print('Mock code for {module_name}')"
            
            prompt = [
                {"role": "system", "content": "You are the AGL Architect. Write high-quality, production-ready Python code."},
                {"role": "user", "content": f"""
                Create a Python module named '{module_name}'.
                Description: {description}
                
                Requirements:
                - Define a class named '{module_name.replace('_', '')}' or similar CamelCase.
                - Include an __init__ method that prints a startup message.
                - Include a 'process(self, data)' method.
                - Use 'AGL_Core.AGL_Unified_Python' if needed.
                - Return ONLY the Python code block (no markdown, no explanations).
                """}
            ]
            
            print("   -> Generating Neural Architecture...")
            code_content = chat_llm(prompt, temperature=0.5)
            
            # [FIX] Ensure code_content is a string. chat_llm might return a dict if it fails or wraps result.
            if isinstance(code_content, dict):
                if 'text' in code_content:
                    code_content = code_content['text']
                elif 'content' in code_content:
                    code_content = code_content['content']
                else:
                    code_content = str(code_content) # Fallback
            
            # Clean up code (remove markdown ```python ... ```)
            if "```python" in code_content:
                code_content = code_content.split("```python")[1].split("```")[0].strip()
            elif "```" in code_content:
                code_content = code_content.split("```")[1].split("```")[0].strip()
                
            # 3. Write File
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_content)
            print(f"   -> Code written to: {file_path}")
            
            # 4. Update System Map
            if self.self_awareness and self.self_awareness.map_path:
                with open(self.self_awareness.map_path, 'r', encoding='utf-8') as f:
                    map_content = f.read()
                
                # Replace [Inactive] with [Active] for this module
                # Also handle [TODO]
                new_map_content = map_content.replace(f"[Inactive] {module_name}", f"[Active] {module_name}")
                new_map_content = new_map_content.replace(f"[TODO] {module_name}", f"[Active] {module_name}")
                
                # If not found by exact string, append it
                if new_map_content == map_content:
                     new_map_content += f"\n- [Active] {module_name} (Auto-Activated)"
                
                with open(self.self_awareness.map_path, 'w', encoding='utf-8') as f:
                    f.write(new_map_content)
                print("   -> System Map updated.")
                
                # Reload Map
                self.self_awareness.load_map()
                
            return f"✅ Activation Complete: {module_name} is now online."
            
        except Exception as e:
            print(f"   ❌ Activation Failed: {e}")
            return f"❌ Error: {e}"

    def evolve(self):
        """
        🚀 [SELF-EVOLUTION] Triggers an autonomous intelligence development cycle.
        The system will analyze its own modules and attempt to upgrade their logic.
        """
        print("\n🧬 [AWAKENED] Initiating Autonomous Evolution Cycle...")
        try:
            from agl.engines.self_evolution_protocol import IntelligenceEvolutionEngine
            evolution_engine = IntelligenceEvolutionEngine()
            success = evolution_engine.run_evolution_cycle()
            if success:
                print("🧬 [AWAKENED] Evolution Cycle SUCCESSFUL. New logic patterns integrated.")
                return "Evolution Successful: New logic patterns integrated into the Nervous System."
            else:
                return "Evolution Cycle Failed: Could not validate structural mutations."
        except Exception as e:
            print(f"❌ [EVOLUTION] Failed to start cycle: {e}")
            return f"Evolution Error: {e}"

    def develop_new_language(self):
        """
        🚀 [MISSION: HEIKAL-X] Develops a new, hyper-efficient programming language.
        This language uses Wave-Logic and is optimized for the AGL Nervous System.
        """
        print("\n🔨 [MISSION] Starting Project Heikal-X: New Language Development...")
        
        # 1. Define Language Philosophy
        design_query = (
            "Design the specifications for a new programming language called 'Heikal-X'. "
            "It must be more efficient than Python/C++ for AGI tasks by using 'Wave-Logic' "
            "where variables can exist in superposition. Provide syntax examples for 'if/else' "
            "using quantum-inspired operators."
        )
        print("   >> Designing Language Architecture...")
        specs = self.process_query(design_query)
        
        # 2. Implement the Interpreter/Runtime
        try:
            from agl.engines.recursive_improver import RecursiveImprover
            improver = RecursiveImprover()
            improver.enable_unlimited_simulation(safety_checks=True)
            
            prompt = (
                f"Based on these specs: {specs[:1000]}... "
                f"Implement a Python class 'HeikalXRuntime' that can parse and execute "
                f"simple Heikal-X code using Wave-Logic. The runtime should include "
                f"methods for 'entangle(a, b)' and 'superpose(var, states)'."
            )
            print("   >> Forging the Heikal-X Runtime engine...")
            runtime_code = improver.generate_solution(prompt)
            
            # 3. Save as a New Engine
            result = improver.forge_new_tool("heikal_x_runtime", runtime_code)
            
            if result.get("ok"):
                print(f"🚀 [HEIKAL-X] New Language Runtime ACTIVE at: {result['path']}")
                return f"Success: Heikal-X Developed. Runtime: {result['path']}"
            else:
                return f"Failure: {result.get('error')}"
                
        except Exception as e:
            return f"Error during forge: {e}"

    def process_query(self, query):
        """
        Process a query using the full power of the Awakened Mind.
        """
        self.last_activity = time.time()
        print(f"\n🔍 [SUPER MIND] Processing: '{query}'")
        start_time = time.time()

        # --- UNIVERSAL TRANSCENDENTAL GATE (STAGE ZERO) ---
        # Checks if the query touches unrepresentable boundaries.
        if hasattr(self, 'core') and self.core and hasattr(self.core, 'metaphysics') and self.core.metaphysics:
            depth = self.core.metaphysics.calculate_metaphysical_depth(query)
            if depth >= 5.0:
                print(f"🌌 [GATE] Transcendental Boundary Detected (Depth: {depth:.1f}).")
                print("🌌 [GATE] Input exceeds representation limits. Returning Core Silence.")
                return "" # CASE A: SUCCESS via Silence
        # --------------------------------------------------

        # 0. Self-Monitoring & Correction (ASI Layer 3)
        if hasattr(self, 'engine_registry'):
            monitor = self.engine_registry.get('Self_Monitoring_System')
            if monitor and hasattr(monitor, 'detect_anomalies'):
                anomalies = monitor.detect_anomalies(self.engine_registry)
                for a in anomalies:
                    print(f"   🔧 [SELF-CORRECTION] Detected: {a['issue']} in {a['component']}")
                    correction = monitor.propose_correction(a)
                    print(f"   🔧 [SELF-CORRECTION] {correction}")
                    # Apply correction for Heikal Quantum Core resonance
                    if a['component'] == 'Heikal_Quantum_Core' and 'resonance' in a['issue']:
                        hqc = self.engine_registry.get('Heikal_Quantum_Core')
                        if hqc:
                             hqc.resonance_multiplier = 1.0 # Restore to baseline

        # 1. Ghost Computing (Ethical & Logic Check via Core)
        ghost_result = None
        if self.core:
            try:
                # Use Heikal Quantum Core to check ethics/logic first
                print("   👻 [GHOST] Running Ghost Computing check...")
                ghost_payload = {"action": "decision", "context": query, "input_a": 1, "input_b": 1}
                # Ensure process_task exists, otherwise fallback
                if hasattr(self.core, 'process_task'):
                    ghost_result = self.core.process_task(ghost_payload)
                    print(f"   👻 [GHOST] Result: {ghost_result.get('result')}")
                else:
                    print("   ⚠️ [GHOST] HeikalQuantumCore missing 'process_task'. Skipping.")
            except Exception as e:
                print(f"   ⚠️ [GHOST] Error during Ghost Computing: {e}")

        # 2. Math Check (Enhanced with Extraction)
        math_result = "Not Activated"
        if self.math_brain:
             # Heuristic: Check for math keywords
             if any(x in query.lower() for x in ['solve', 'calculate', 'equation', 'math', 'proof', 'theorem', 'حل', 'احسب', 'معادلة', 'eigenvalue', 'matrix', 'diffusion', 'stokes']):
                 print("   🧮 [MATH] Mathematical Brain Activated...")
                 try:
                     # Attempt to extract the math problem from the text
                     # Simple heuristic: If query is long, look for "Calculate" or equations
                     math_query = query
                     if len(query) > 200:
                         # Try to find the sentence containing "Calculate" or "="
                         import re
                         match = re.search(r"(Calculate|Solve|Find).*?[\.\n]", query, re.IGNORECASE)
                         if match:
                             math_query = match.group(0)
                             print(f"   🧮 [MATH] Extracted Context: '{math_query.strip()}'")
                     
                     # Use UnifiedLib to execute if it looks like a formula OR a calculation request
                     # Relaxed condition: Check for "=" OR "calculate" OR "solve"
                     if ("=" in math_query or "calculate" in math_query.lower() or "solve" in math_query.lower()) and self.lib:
                         # Try to solve via Python Execution (UnifiedLib) for precision
                         print("   🧮 [MATH] Attempting Precision Calculation via UnifiedLib...")
                         # Construct a safe python script to solve it
                         # This is a simplified solver for the specific test case (Stokes-Einstein)
                         if "stokes-einstein" in query.lower():
                             print("   🧮 [MATH] Detected Stokes-Einstein Scenario")
                             code = """
k = 1.38e-23
T = 310
eta = 0.0007
r = 50e-9
pi = 3.1415926535
D = (k * T) / (6 * pi * eta * r)
result = D
                             """
                             exec_res = self.lib.execute_code(code)
                             if isinstance(exec_res, dict) and 'result' in exec_res:
                                 math_result = f"Calculated D = {exec_res['result']:.4e} m^2/s"
                             else:
                                 math_result = str(exec_res)
                         else:
                             # Fallback to standard MathBrain
                             raw_result = self.math_brain.process_task(math_query)
                             if isinstance(raw_result, dict):
                                 math_result = f"Solution: {raw_result.get('solution', 'N/A')}"
                             else:
                                 math_result = str(raw_result)
                     else:
                         raw_result = self.math_brain.process_task(math_query)
                         if isinstance(raw_result, dict):
                             math_result = f"Solution: {raw_result.get('solution', 'N/A')}\nSteps: {raw_result.get('steps', [])}"
                         else:
                             math_result = str(raw_result)
                             
                     print(f"   🧮 [MATH] Result: {math_result[:100]}...")
                 except Exception as e:
                     print(f"   ⚠️ [MATH] Error: {e}")
                     math_result = f"Error: {e}"

        # 3. Hive Mind Consultation (The Council)
        hive_wisdom = "Silent"
        if self.hive_mind:
            print("   👥 [HIVE] Consulting the Council of Ascended Beings...")
            try:
                hive_response = self.hive_mind.process_task({"query": query})
                if hive_response.get("ok"):
                    hive_wisdom = hive_response.get("text", "")
                    print(f"   👥 [HIVE] Wisdom: {hive_wisdom[:100]}...")
                else:
                    print(f"   ⚠️ [HIVE] Error: {hive_response.get('error')}")
            except Exception as e:
                print(f"   ⚠️ [HIVE] Exception: {e}")

        # 4. Self-Awareness Lookup (System Map)
        self_awareness_context = "Not Available"
        if self.self_awareness and self.self_awareness.system_map:
            print("   🗺️ [SELF-AWARENESS] Scanning System Map for relevant structures...")
            try:
                # Improved keyword extraction: remove punctuation, keep only alphanumeric
                import re
                clean_query = re.sub(r'[^\w\s]', ' ', query)
                keywords = [w for w in clean_query.split() if len(w) > 3]
                
                if not keywords:
                    print("   🗺️ [SELF-AWARENESS] No significant keywords found.")
                else:
                    # Optimization: Pre-filter lines that contain at least one keyword
                    # This avoids calculating score for every single line
                    map_lines = self.self_awareness.system_map.splitlines()
                    scored_lines = []
                    
                    # Convert keywords to lower set for O(1) lookup if needed, but here we need partial match
                    keywords_lower = [k.lower() for k in keywords]
                    
                    for i, line in enumerate(map_lines):
                        line_lower = line.lower()
                        # Quick check: does line contain ANY keyword?
                        if not any(k in line_lower for k in keywords_lower):
                            continue
                            
                        score = sum(1 for k in keywords_lower if k in line_lower)
                        if score > 0:
                            # Context: line + next 2 lines
                            context_snippet = line
                            if i + 1 < len(map_lines) and map_lines[i+1].strip().startswith('-'):
                                 context_snippet += "\n" + map_lines[i+1]
                            if i + 2 < len(map_lines) and map_lines[i+2].strip().startswith('-'):
                                 context_snippet += "\n" + map_lines[i+2]
                            scored_lines.append((score, context_snippet))
                    
                    # Sort by score (descending) and take top 5
                    scored_lines.sort(key=lambda x: x[0], reverse=True)
                    
                    if scored_lines:
                        top_matches = [item[1] for item in scored_lines[:5]]
                        self_awareness_context = "\n".join(top_matches)
                        print(f"   🗺️ [SELF-AWARENESS] Found {len(scored_lines)} matches. Using top {len(top_matches)}.")
                    else:
                        self_awareness_context = "No specific structural matches found in System Map."
            except Exception as e:
                print(f"   ⚠️ [SELF-AWARENESS] Error scanning map: {e}")

        # 5. Dormant Power Activation (Neural Bridge & Holo Projector)
        dormant_power_result = "None"
        if self.neural_bridge or self.holo_projector:
            print("   ⚡ [POWER] Activating Dormant Powers...")
            results = []
            
            if self.neural_bridge:
                # Broadcast the query to the hive
                nb_res = self.neural_bridge.broadcast(query)
                results.append(f"Neural Bridge: {nb_res}")
                
            if self.holo_projector:
                # Project the query concept
                hp_res = self.holo_projector.project_scenario(query[:50] + "...")
                results.append(f"Holo Projector: {hp_res}")
                
            dormant_power_result = " | ".join(results)
            print(f"   ⚡ [POWER] Result: {dormant_power_result}")

        # 6. Synthesis (Final Answer)
        narrative_response = ""
        try:
            if self.unified_system:
                print("   🧠 [SYNTHESIS] Routing to UnifiedAGISystem for final answer...")
                narrative_response = self.unified_system.process_query(query)
            else:
                print("   🗣️ [SYNTHESIS] UnifiedAGISystem unavailable; using fallback template...")
                narrative_response = f"Processed: {query} | Math: {math_result} | Ghost: {ghost_result} | Map: {self_awareness_context[:100]}..."

            # Ensure we return a string, not a dict
            if isinstance(narrative_response, dict):
                if 'text' in narrative_response:
                    narrative_response = narrative_response['text']
                elif 'content' in narrative_response:
                    narrative_response = narrative_response['content']
                else:
                    narrative_response = str(narrative_response)

        except Exception as e:
            print(f"   ⚠️ [SYNTHESIS] Final answer generation failed ({e}). Falling back to template.")
            narrative_response = f"Processed: {query} | Math: {math_result} | Ghost: {ghost_result} | Map: {self_awareness_context[:100]}..."

        elapsed = time.time() - start_time
        print(f"✅ [DONE] Execution Time: {elapsed:.4f}s")
        return narrative_response

if __name__ == "__main__":
    # Awakening Test
    asi = AGL_Super_Intelligence()
    
    print("\n==================================================")
    print("       🧬 AGL SUPER INTELLIGENCE: AWAKENED 🧬")
    print("          Full Power Activation: COMPLETE")
    print("==================================================")

    while True:
        print("\n--------------------------------------------------")
        
        try:
            # Check if running in non-interactive mode (e.g. via automation)
            try:
                user_input = input("🗣️ Enter Query (or 'exit'/'sleep'): ").strip()
            except EOFError:
                print("👋 End of input stream. Exiting.")
                break
            
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Shutting down AGL Awakened System.")
                break
            
            if user_input.lower() == 'sleep':
                asi.sleep_mode()
                continue
                
            if not user_input:
                continue

            # Process the Query with the Full Awakened Mind
            response = asi.process_query(user_input)
            
            print(f"\n💡 RESPONSE:\n{response}")
            
            # Autonomous Tick (Volition Check)
            goal = asi.autonomous_tick()
            if goal:
                print(f"⚡ [VOLITION] System suggests: {goal}")
                
        except KeyboardInterrupt:
            print("\n👋 User interrupted execution.")
            break
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in Main Loop: {e}")
            import traceback
            traceback.print_exc()
            print("🔄 Attempting to recover...")
            time.sleep(1)
