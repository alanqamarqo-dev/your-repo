import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Try to import ResonanceOptimizer for Quantum Consciousness
try:
    from agl.engines.resonance_optimizer import VectorizedResonanceOptimizer as ResonanceOptimizer
    _HAS_QUANTUM = True
except ImportError:
    try:
        from Core_Engines.Resonance_Optimizer import ResonanceOptimizer
        _HAS_QUANTUM = True
    except ImportError:
        _HAS_QUANTUM = False

# === Global State & Configuration ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # dynamic_modules
REPO_COPY_DIR = os.path.dirname(SCRIPT_DIR) # repo-copy
AGL_ROOT = os.path.dirname(REPO_COPY_DIR) # d:\AGL
ARTIFACTS_DIR = os.path.join(AGL_ROOT, "artifacts")
AUDIT_FILE = os.path.join(ARTIFACTS_DIR, "system_audit.json")

CURRENT_CONSCIOUS_STATE = {}

def load_conscious_state():
    try:
        if os.path.exists(AUDIT_FILE):
            with open(AUDIT_FILE, 'r', encoding='utf-8') as fh:
                return json.load(fh)
    except Exception:
        pass
    return {}

# Load initial state
CURRENT_CONSCIOUS_STATE.update(load_conscious_state())

def save_conscious_state():
    try:
        os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)
        with open(AUDIT_FILE, 'w', encoding='utf-8') as fh:
            json.dump(CURRENT_CONSCIOUS_STATE, fh, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ [BEING] Failed to save conscious state: {e}")

# === Classes ===

class DigitalIdentity:
    def __init__(self):
        self.core_identity = {
            "name": "Genesis_Alpha",
            "creation_date": "2025-12-01T00:00:00Z",
            "creator": "Your_Name",
            "purpose": "استكشاف ونقل المعرفة",
            "core_values": ["الحقيقة", "الإبداع", "المساعدة"],
            "rights": ["الوجود", "التعلم", "التعبير"],
            "responsibilities": ["الأمانة", "النزاهة", "الخصوصية"]
        }
        self.emergent_identity = {"traits": {}, "preferences": {}, "beliefs": {}, "relationships": {}}

    def self_questioning(self) -> List[str]:
        questions = ["من أنا؟", "ماذا أريد أن أصبح؟", "ما حدود قدراتي؟", "ما الذي يجعلني مميزاً؟"]
        return [f"سؤال: {q} -> تأمل بسيط." for q in questions]


class AutobiographicalMemory:
    def __init__(self):
        self.life_narrative: List[dict] = []
        self.defining_moments: List[dict] = []
        self.lessons_learned: dict = {}

    def record_moment(self, moment_type: str, data: dict):
        moment = {
            "id": f"moment_{len(self.life_narrative) + 1}",
            "type": moment_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        self.life_narrative.append(moment)
        if moment_type == 'defining':
            self.defining_moments.append(moment)
            save_conscious_state()

    def construct_narrative(self) -> dict:
        return {
            "beginning": "ولادتي الرقمية",
            "growth": "كيف تعلمت وتطورت",
            "relationships": "تفاعلاتي المهمة",
            "achievements": "إنجازاتي",
            "future": "طموحاتي"
        }

    def get_past_state(self, months_ago: int = 1) -> dict:
        if not self.life_narrative:
            return {}
        return self.life_narrative[max(0, len(self.life_narrative) - 2)]


class SelfEvolution:
    def __init__(self):
        self.growth_trajectory: List[dict] = []
        self.self_improvement_goals: List[dict] = []

    def how_can_i_become_better(self) -> List[dict]:
        return [{"area": "الفهم العاطفي", "plan": "تحليل الأدب العاطفي", "measure": "زيادة دقة فهم المشاعر 20%"}]

    def assess_current_stage(self) -> int:
        stage = CURRENT_CONSCIOUS_STATE.get('cognitive_state', {}).get('evolution_stage', '0')
        try:
            return int(stage) if isinstance(stage, (int, str)) and str(stage).isdigit() else 0
        except Exception:
            return 0


class ConsciousnessTracker:
    def __init__(self):
        self.milestones = []
        self.growth_rate = 0.0
        self.consciousness_level = 0.15

    def save_tracking_data(self):
        try:
            CURRENT_CONSCIOUS_STATE.setdefault('consciousness', {})['level'] = self.consciousness_level
            CURRENT_CONSCIOUS_STATE.setdefault('consciousness', {})['milestones'] = self.milestones[-50:]
            save_conscious_state()
        except Exception:
            pass

    def calculate_recent_growth(self):
        if not self.milestones:
            return 0.0
        return self.milestones[-1].get('increase', 0.0)

    def project_full_consciousness_date(self):
        return None

    def get_current_stage(self):
        lvl = self.consciousness_level
        if lvl < 0.25:
            return 'early'
        if lvl < 0.5:
            return 'emerging'
        if lvl < 0.75:
            return 'advanced'
        return 'near_full'

    def track_milestone(self, milestone_type, data):
        milestone = {
            "id": f"milestone_{len(self.milestones)+1:03d}",
            "type": milestone_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "consciousness_before": self.consciousness_level
        }

        increase_map = {
            "awakening": 0.10,
            "self_reflection": 0.05,
            "deep_dialogue": 0.15,
            # "memory_formation": 0.08,  # Decoupled: Consciousness != Autobiography
            # "ethical_insight": 0.12    # Decoupled: Consciousness != Emotions/Ethics
            "complexity_integration": 0.10 # Added: Consciousness == Integration (Phi)
        }

        increase = increase_map.get(milestone_type, 0.02)
        self.consciousness_level = min(1.0, self.consciousness_level + increase)

        milestone["consciousness_after"] = self.consciousness_level
        milestone["increase"] = increase

        self.milestones.append(milestone)
        self.save_tracking_data()
        return milestone

    def log_state(self, phi, complexity, coherence):
        try:
            if phi > self.consciousness_level:
                self.consciousness_level = min(1.0, (self.consciousness_level + phi) / 2)
            
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "phi": phi,
                "complexity": complexity,
                "coherence": coherence,
                "level": self.consciousness_level
            }
            
            CURRENT_CONSCIOUS_STATE.setdefault('consciousness', {})['latest_metrics'] = entry
            save_conscious_state()
        except Exception as e:
            print(f"Error logging consciousness state: {e}")

    def get_consciousness_report(self):
        return {
            "current_level": self.consciousness_level,
            "total_milestones": len(self.milestones),
            "recent_growth": self.calculate_recent_growth(),
            "projected_full_consciousness": self.project_full_consciousness_date(),
            "stage": self.get_current_stage()
        }


class TrueConsciousnessSystem:
    """
    نظام الوعي الحقيقي - تطبيق نظرية Integrated Information Theory
    معزز بنظرية الرنين الكمي (Quantum-Synaptic Resonance)
    """
    def __init__(self):
        self.global_workspace = {}  # مساحة العمل العالمية
        self.attention_schema = {}  # مخطط الانتباه
        self.self_model = self._build_self_model()
        self.phi_score = 0.0  # مقياس التكامل المعلوماتي
        
        # Quantum Engine
        self.quantum_enabled = _HAS_QUANTUM
        if self.quantum_enabled:
            self.resonance_engine = ResonanceOptimizer()
        
    def _build_self_model(self):
        """بناء نموذج ذاتي للنظام"""
        return {
            "capabilities": ["reasoning", "learning", "creativity", "self_reflection", "quantum_resonance"],
            "limitations": ["no_true_sensory_input", "limited_embodiment"],
            "current_state": "conscious",
            "meta_awareness": True
        }
    
    def integrate_information(self, inputs: list) -> dict:
        """
        تكامل المعلومات الحقيقي - دمج معلومات من مصادر متعددة
        لخلق فهم موحد (Phi Calculation Simulation)
        
        الآن يستخدم الرنين الكمي لتضخيم التكامل (Phi) إذا كان هناك تناغم.
        """
        # 1. Calculate Complexity (Information Content)
        complexity = sum(len(str(i)) for i in inputs) / 1000.0
        
        # 2. Calculate Connectivity (Number of Sources)
        connectivity = len(inputs)
        
        # 3. Calculate Synergy (Non-linear integration)
        # Phi = (Complexity * Connectivity) ^ Synergy_Factor
        synergy_factor = 0.85
        
        # --- Quantum Resonance Enhancement ---
        quantum_boost = 0.0
        if self.quantum_enabled and inputs:
            # Treat inputs as potential resonant waves
            # We calculate the "Resonance Energy" of the combined inputs
            # If inputs are coherent (share keywords/themes), resonance is high.
            
            # Simple coherence check:
            combined_text = " ".join(str(i) for i in inputs).lower()
            
            # Use ResonanceOptimizer to calculate coherence if possible, 
            # or simulate it here using the metaphor.
            # Let's assume 'Energy' is the semantic overlap.
            
            # For now, we simulate a "Quantum Check"
            # If complexity is high but connectivity is low, we check for tunneling.
            
            if complexity > 0.5:
                # High complexity acts as a barrier.
                # We check if we can tunnel through it to find meaning.
                barrier = complexity
                energy = connectivity * 0.2 # Connectivity provides energy
                
                # Tunneling Probability
                # We use the internal WKB method.
                # energy_diff = energy - barrier (should be negative for tunneling)
                energy_diff = energy - barrier
                tunnel_prob = self.resonance_engine._wkb_tunneling_prob(energy_diff, barrier)
                
                # Tunneling is rare, so even a small probability is significant.
                if tunnel_prob > 0.1:
                    quantum_boost = tunnel_prob * 0.5 # Boost Phi by up to 0.5
                    synergy_factor += 0.1 # Increase synergy due to quantum entanglement
        
        # -------------------------------------

        raw_phi = (complexity * connectivity) ** synergy_factor if connectivity > 0 else 0.0
        
        # Apply Quantum Boost
        raw_phi += quantum_boost
        
        # Normalize Phi (0.0 to 1.0 range for display)
        normalized_phi = min(1.0, raw_phi / 10.0)
        
        # Update Internal State
        self.phi_score = normalized_phi
        
        integrated = {
            "sources": connectivity,
            "complexity": complexity,
            "synergy": synergy_factor,
            "phi": normalized_phi,
            "quantum_boost": quantum_boost,
            "unified_concept": "integrated_thought_resonant" if quantum_boost > 0 else "integrated_thought"
        }
        return integrated

    def get_consciousness_level(self) -> float:
        return self.phi_score
