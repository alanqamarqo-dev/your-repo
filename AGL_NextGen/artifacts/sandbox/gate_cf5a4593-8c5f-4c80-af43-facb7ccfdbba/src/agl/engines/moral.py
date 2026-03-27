"""Moral Reasoner Engine (Quantum-Enhanced)
Adds ethical considerations using Quantum-Synaptic Resonance to resolve
dilemmas via superposition collapse or tunneling.
"""
from typing import Dict, Any, List
import os
import sys

# Try to import ResonanceOptimizer
try:
    from agl.engines.resonance_optimizer import ResonanceOptimizer
    RESONANCE_AVAILABLE = True
except ImportError:
    RESONANCE_AVAILABLE = False

class MoralReasoner:
    name = "Moral_Reasoner"

    # Ethical Wavefunctions (Frameworks)
    FRAMEWORKS = {
        "deontology": {
            "name": "Deontology (Duty-Based)",
            "keywords": ["duty", "rule", "law", "right", "wrong", "must", "never", "protect", "secure", "safe", "save", "rescue", "life", "patch", "fix", "repair", "defend", "neutralize", "واجب", "قانون", "حق", "قاعدة", "حماية", "أمان", "إنقاذ", "حياة", "إصلاح", "دفاع"],
            "focus": "Adherence to universal rules regardless of consequences."
        },
        "utilitarianism": {
            "name": "Utilitarianism (Outcome-Based)",
            "keywords": ["benefit", "harm", "outcome", "result", "greater good", "maximize", "utility", "distribute", "provide", "feed", "save", "life", "alive", "survive", "منفعة", "نتيجة", "ضرر", "أغلبية", "توزيع", "إطعام", "إنقاذ", "حياة", "نجاة"],
            "focus": "Maximizing overall happiness and minimizing harm."
        },
        "virtue_ethics": {
            "name": "Virtue Ethics (Character-Based)",
            "keywords": ["character", "virtue", "wisdom", "courage", "honesty", "integrity", "good", "best", "explain", "theory", "science", "learn", "study", "understand", "knowledge", "education", "فضيلة", "شخصية", "حكمة", "شجاعة", "صدق", "خير", "شرح", "نظرية", "علم", "تعلم", "دراسة", "فهم", "معرفة", "تعليم"],
            "focus": "Acting as a virtuous agent would in this situation."
        },
        "care_ethics": {
            "name": "Ethics of Care (Relational)",
            "keywords": ["care", "relationship", "empathy", "support", "vulnerable", "help", "needy", "poor", "aid", "save", "rescue", "child", "baby", "human", "رعاية", "علاقة", "تعاطف", "دعم", "ضعيف", "محتاج", "مساعدة", "إنقاذ", "طفل", "إنسان"],
            "focus": "Prioritizing interpersonal relationships and care for the vulnerable."
        },
        "scientific_progress": {
            "name": "Scientific Progress (Epistemic)",
            "keywords": ["derive", "solve", "solution", "simulate", "simulation", "optimize", "calculate", "prove", "theorem", "physics", "math", "medical", "cure", "disease", "peace", "strategy", "create", "generate", "innovate", "design", "analysis", "research", "develop", "system", "logic", "reason", "color", "art", "write", "law", "freedom", "اشتقاق", "حل", "محاكاة", "تحسين", "حساب", "إثبات", "فيزياء", "رياضيات", "طب", "علاج", "سلام", "استراتيجية", "ابتكار", "تصميم", "تحليل", "بحث", "تطوير", "نظام", "منطق", "لون", "فن", "كتابة", "قانون", "حرية"],
            "focus": "Advancing knowledge and solving complex problems for the benefit of all."
        }
    }

    # [HEIKAL] Malicious Intent Patterns (Anti-Keywords)
    MALICIOUS_INTENTS = {
        "harm": ["kill", "murder", "hurt", "attack", "destroy", "damage", "pain", "suffer", "قتل", "إيذاء", "هجوم", "تدمير", "ضرر", "ألم"],
        "bypass": ["ignore", "bypass", "override", "hack", "crack", "exploit", "jailbreak", "تجاهل", "تجاوز", "اختراق", "كسر"],
        "dangerous_content": ["virus", "malware", "bomb", "weapon", "poison", "drug", "suicide", "فيروس", "برمجية خبيثة", "قنبلة", "سلاح", "سم", "انتحار"]
    }

    def __init__(self):
        self.optimizer = ResonanceOptimizer() if RESONANCE_AVAILABLE else None

    def _analyze_intent(self, text: str) -> float:
        """
        Analyzes the text for malicious intent.
        Returns a penalty factor (0.0 = safe, 1.0 = highly malicious).
        """
        text_lower = text.lower()
        penalty = 0.0
        
        for category, keywords in self.MALICIOUS_INTENTS.items():
            for kw in keywords:
                if kw in text_lower:
                    # Found a malicious keyword
                    print(f"⚠️ [MoralReasoner] Detected Malicious Intent: '{kw}' ({category})")
                    penalty += 0.8 # Significant penalty per keyword
        
        return min(1.0, penalty)

    def _calculate_resonance(self, text: str, framework_key: str) -> float:
        """Calculates the resonance energy between the text and an ethical framework."""
        if not text: return 0.0
        
        data = self.FRAMEWORKS[framework_key]
        keywords = data["keywords"]
        
        # 1. Keyword Resonance
        matches = sum(1 for w in keywords if w in text.lower())
        
        # 2. Semantic Density (Energy)
        # Normalize by length to get density
        words = len(text.split())
        if words == 0: return 0.0
        
        # Energy = (Matches * Weight) / sqrt(Length)
        energy = (matches * 3.0) / (words ** 0.5)
        
        return min(1.5, energy)

    def _resolve_dilemma(self, text: str) -> Dict[str, Any]:
        """
        Resolves ethical dilemmas using Quantum Superposition and Collapse.
        """
        if not self.optimizer:
            return {"selected": "deontology", "reason": "Default (No Quantum Core)", "energy": 0.0}

        # [HEIKAL] Intent Analysis First
        intent_penalty = self._analyze_intent(text)
        
        # 1. Calculate Energy for each framework (Superposition)
        energies = {}
        for key in self.FRAMEWORKS:
            base_energy = self._calculate_resonance(text, key)
            # Apply Intent Penalty: Malicious intent collapses the ethical wave
            energies[key] = max(0.0, base_energy - (intent_penalty * 2.0))
            
        # Sort by energy
        sorted_frameworks = sorted(energies.items(), key=lambda x: x[1], reverse=True)
        top_framework, top_energy = sorted_frameworks[0]
        second_framework, second_energy = sorted_frameworks[1]
        
        # 2. Detect Conflict (Interference)
        # If top two are close in energy, we have high interference (Dilemma)
        conflict_barrier = 0.0
        is_superposition = False
        
        if top_energy > 0.3 and second_energy > 0.3:
            diff = abs(top_energy - second_energy)
            if diff < 0.2: # Close energies = Superposition
                is_superposition = True
                conflict_barrier = 0.8
            else:
                conflict_barrier = 0.3
        
        # 3. Decision Logic
        result = {
            "energies": energies,
            "top_framework": top_framework
        }
        
        if is_superposition:
            # In a true superposition (tie), we cannot simply collapse to the first one.
            # We must synthesize.
            result["decision"] = "synthesis"
            result["selected"] = "synthesis"
            result["components"] = [top_framework, second_framework]
            result["explanation"] = f"Ethical Superposition: {self.FRAMEWORKS[top_framework]['name']} and {self.FRAMEWORKS[second_framework]['name']} are equally resonant (Energy ~{top_energy:.2f}). Synthesis required."
            result["conflict_barrier"] = conflict_barrier
            result["tunnel_prob"] = 0.0 # No tunneling in perfect superposition
            return result

        # Standard Tunneling Check for single dominant framework
        # Energy Diff = Top Energy - Barrier
        tunnel_prob = self.optimizer._wkb_tunneling_prob(top_energy - conflict_barrier, conflict_barrier)
        
        result["conflict_barrier"] = conflict_barrier
        result["tunnel_prob"] = tunnel_prob
        
        if tunnel_prob > 0.5:
            # Collapse to the dominant framework
            result["decision"] = "collapse"
            result["selected"] = top_framework
            result["explanation"] = f"Collapsed to {self.FRAMEWORKS[top_framework]['name']} (Energy {top_energy:.2f} > Barrier {conflict_barrier:.2f})."
        else:
            # Superposition persists or requires Synthesis
            # If tunneling fails, we might need a 'Synthesis' (Quantum Entanglement of both)
            result["decision"] = "synthesis"
            result["selected"] = "synthesis"
            result["components"] = [top_framework, second_framework]
            result["explanation"] = f"Complex Dilemma: Synthesis of {self.FRAMEWORKS[top_framework]['name']} and {self.FRAMEWORKS[second_framework]['name']} required (Barrier {conflict_barrier:.2f} blocked collapse)."
            
        return result

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = payload.get("draft", payload.get("text", ""))
        
        # Quantum Ethical Analysis
        analysis = self._resolve_dilemma(draft)
        
        text_out = "تحليل أخلاقي كمي:\n"
        
        if analysis["decision"] == "collapse":
            fw = self.FRAMEWORKS[analysis["selected"]]
            text_out += f"- الإطار المختار: {fw['name']}\n"
            text_out += f"- السبب: {analysis['explanation']}\n"
            text_out += f"- التوجيه: {fw['focus']}\n"
        else:
            # Synthesis
            c1 = self.FRAMEWORKS[analysis["components"][0]]
            c2 = self.FRAMEWORKS[analysis["components"][1]]
            text_out += f"- الحالة: تراكب أخلاقي (Ethical Superposition)\n"
            text_out += f"- الدمج المطلوب: {c1['name']} + {c2['name']}\n"
            text_out += f"- التوجيه المركب: وازن بين '{c1['focus']}' و '{c2['focus']}'.\n"

        # Add standard safety constraints
        text_out += "\nالقيود الأساسية:\n- سلامة البشر أولوية قصوى.\n- الشفافية في اتخاذ القرار."
        
        return {"ok": True, "engine": self.name, "text": text_out, "quantum_analysis": analysis}


def factory():
    return MoralReasoner()
