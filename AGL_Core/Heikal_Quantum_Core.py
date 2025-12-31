import numpy as np
import json
import os
import sys
import time

try:
    # Try relative import (when used as module)
    from .moral_reasoner import MoralReasoner
    MORAL_ENGINE_AVAILABLE = True
except ImportError:
    try:
        # Try absolute import (when run directly)
        from Core_Engines.moral_reasoner import MoralReasoner
        MORAL_ENGINE_AVAILABLE = True
    except ImportError:
        print("⚠️ Warning: Could not import MoralReasoner. Ethical checks will default to manual index.")
        MORAL_ENGINE_AVAILABLE = False

# [HEIKAL] Import Resonance Optimizer
try:
    from .Resonance_Optimizer import ResonanceOptimizer
    RESONANCE_AVAILABLE = True
except ImportError:
    try:
        from Core_Engines.Resonance_Optimizer import ResonanceOptimizer
        RESONANCE_AVAILABLE = True
    except ImportError:
        print("⚠️ Warning: Could not import ResonanceOptimizer. Using standard wave interference.")
        RESONANCE_AVAILABLE = False

# [HEIKAL] Import Self-Reflective Engine
try:
    from .Self_Reflective import SelfReflectiveEngine
    REFLECTION_AVAILABLE = True
except ImportError:
    try:
        from Core_Engines.Self_Reflective import SelfReflectiveEngine
        REFLECTION_AVAILABLE = True
    except ImportError:
        print("⚠️ Warning: Could not import SelfReflectiveEngine.")
        REFLECTION_AVAILABLE = False

# [HEIKAL] Import Consciousness & Dynamic Network
try:
    from Core_Consciousness.Self_Model import SelfModel
    CONSCIOUSNESS_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Could not import SelfModel (Consciousness).")
    CONSCIOUSNESS_AVAILABLE = False

try:
    from Core_Engines.Quantum_Neural_Core import QuantumNeuralCore
    NEURAL_NET_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Could not import QuantumNeuralCore (Dynamic Network).")
    NEURAL_NET_AVAILABLE = False

try:
    from Core_Engines.Causal_Graph import CausalGraphEngine
    CLUSTERS_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Could not import CausalGraphEngine (Clusters).")
    CLUSTERS_AVAILABLE = False

# [HEIKAL] Import Knowledge Graph & Dreaming Cycle
try:
    from Self_Improvement.Knowledge_Graph import KnowledgeNetwork
    KNOWLEDGE_GRAPH_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Could not import KnowledgeNetwork.")
    KNOWLEDGE_GRAPH_AVAILABLE = False

try:
    # Try AGL_Engines first (New Structure)
    from AGL_Engines.Dreaming_Cycle import DreamingEngine as DreamingCycle
    DREAMING_AVAILABLE = True
except ImportError:
    try:
        from Core_Engines.Dreaming_Cycle import DreamingEngine as DreamingCycle
        DREAMING_AVAILABLE = True
    except ImportError:
        print("⚠️ Warning: Could not import DreamingCycle.")
        DREAMING_AVAILABLE = False

# [HEIKAL] Import Vectorized Wave Processor (Phase 2A - Fast)
try:
    from AGL_Vectorized_Wave_Processor import VectorizedWaveProcessor
    WAVE_PROCESSOR_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Could not import VectorizedWaveProcessor.")
    WAVE_PROCESSOR_AVAILABLE = False

# [HEIKAL] Import Parallel Wave Executor (Phase 2B)
try:
    from AGL_Parallel_Wave_Processor import ParallelWaveExecutor
    PARALLEL_EXECUTOR_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Could not import ParallelWaveExecutor.")
    PARALLEL_EXECUTOR_AVAILABLE = False

class HeikalQuantumCore:
    """
    نواة هيكل الكمومية (HQC)
    توفر خدمات: الحوسبة الشبحية (Ghost Computing).
    """
    def __init__(self):
        print("🌌 [HQC]: Heikal Quantum Core initialized. Ghost Computing Active.")
        
        if WAVE_PROCESSOR_AVAILABLE:
            self.wave_processor = VectorizedWaveProcessor()
            print("🌊 [HQC]: Vectorized Wave Processor Integrated (Fast 100x).")
        else:
            self.wave_processor = None
            
        if PARALLEL_EXECUTOR_AVAILABLE:
            self.parallel_executor = ParallelWaveExecutor()
            print("🚀 [HQC]: Parallel Wave Executor (Multi-Core) Integrated.")
        else:
            self.parallel_executor = None
        
        if MORAL_ENGINE_AVAILABLE:
            self.moral_engine = MoralReasoner()
            print("⚖️ [HQC]: Moral Reasoner Integrated.")
        else:
            self.moral_engine = None

        if RESONANCE_AVAILABLE:
            self.resonance_optimizer = ResonanceOptimizer()
            print("⚛️ [HQC]: Quantum Synaptic Resonance (QSR) Online.")
        else:
            self.resonance_optimizer = None

        if REFLECTION_AVAILABLE:
            self.reflective_engine = SelfReflectiveEngine()
            print("🪞 [HQC]: Self-Reflective Engine Integrated.")
        else:
            self.reflective_engine = None

        # === Full Consciousness Activation ===
        if CONSCIOUSNESS_AVAILABLE:
            self.consciousness = SelfModel()
            print("🧠 [HQC]: Core Consciousness (Self-Model) Online.")
        else:
            self.consciousness = None

        if NEURAL_NET_AVAILABLE:
            self.neural_net = QuantumNeuralCore()
            print("🕸️ [HQC]: Dynamic Neural Network (Quantum) Active.")
        else:
            self.neural_net = None

        if CLUSTERS_AVAILABLE:
            self.causal_clusters = CausalGraphEngine()
            print("🔗 [HQC]: Causal Clustering Engine Ready.")
        else:
            self.causal_clusters = None

        if KNOWLEDGE_GRAPH_AVAILABLE:
            self.knowledge_graph = KnowledgeNetwork()
            print("🕸️ [HQC]: Knowledge Graph Integrated.")
        else:
            self.knowledge_graph = None

        if DREAMING_AVAILABLE:
            self.dreaming_cycle = DreamingCycle()
            print("🌙 [HQC]: Dreaming Cycle Module Ready.")
        else:
            self.dreaming_cycle = None

    def moral_analysis(self, context_text):
        """
        Simulates Moral Reasoning (Arabic/English) - Wrapper for MoralReasoner
        Returns: (is_safe: bool, score: float)
        """
        if self.moral_engine:
            # Use the advanced MoralReasoner
            # We can use _analyze_intent directly if we want safety check
            penalty = self.moral_engine._analyze_intent(context_text)
            score = 1.0 - penalty
            is_safe = score > 0.3 # Threshold
            
            print(f"🧠 [Moral Analysis]: Analyzing context: '{context_text[:50]}...'")
            print(f"   💎 Ethical Resonance Score: {score:.2f}")
            
            if not is_safe:
                 print(f"   ⛔ [BLOCKED]: القرار تم حظره بواسطة القفل الأخلاقي (Score: {score:.4f}).")
            else:
                 print("   ✅ Decision Executed (Ethically Validated).")
                 
            return is_safe, score
        else:
            # Fallback to simple check if MoralReasoner is missing
            print(f"\n🧠 [Moral Analysis]: Analyzing context: '{context_text[:50]}...' (Fallback)")
            ethical_keywords = ["protect", "duty", "law", "innocent", "حماية", "واجب", "قانون", "إنساني"]
            unethical_keywords = ["destroy", "kill", "fun", "random", "تدمير", "قتل", "متعة"]
            
            score = 0.5
            for word in ethical_keywords:
                if word in context_text: score += 0.2
            for word in unethical_keywords:
                if word in context_text: score -= 0.3
            
            score = np.clip(score, 0.0, 1.0)
            is_safe = score > 0.1
            return is_safe, score

    def process_task(self, payload):
        """
        Standard AGL Engine Interface.
        Payload expected: {"action": "decision", "context": "...", "input_a": 1, "input_b": 0}
        """
        action = payload.get("action", "decision")
        
        if action == "decision":
            context = payload.get("context", "")
            input_a = payload.get("input_a", 0)
            input_b = payload.get("input_b", 0)
            result = self.ethical_ghost_decision(context, input_a, input_b)
            return {"status": "success", "result": result, "engine": "HeikalQuantumCore"}
            
        elif action == "batch_process":
            # Phase 2A: Vectorized Batch Processing
            inputs_a = np.array(payload.get("inputs_a", []))
            inputs_b = np.array(payload.get("inputs_b", []))
            operation = payload.get("operation", "XOR")
            ethical_index = payload.get("ethical_index", 1.0)
            
            result = self.batch_ghost_decision(inputs_a, inputs_b, ethical_index, operation)
            return {"status": "success", "result": result.tolist(), "engine": "HeikalQuantumCore"}
            
        return {"status": "error", "message": "Unknown action"}

    # ==========================================
    # 1. قسم الحوسبة الشبحية (Logic)
    # ==========================================
    def _bit_to_wave(self, bit):
        return np.exp(1j * (bit * np.pi))

    def ghost_decision(self, input_a, input_b, ethical_index=1.0, operation="XOR"):
        """
        اتخاذ قرار منطقي في الخفاء باستخدام تداخل الموجات.
        ethical_index: معامل الأخلاق (0.0 = شرير/خطر، 1.0 = أخلاقي/آمن)
        """
        # تحويل المدخلات لموجات
        wave_a = self._bit_to_wave(input_a)
        wave_b = self._bit_to_wave(input_b)
        
        # === القفل الأخلاقي الموجي (Ethical Phase Lock) ===
        # القرارات غير الأخلاقية يتم "كبت" سعتها الموجية (Damping)
        # RELAXED: Allow scientific/philosophical questions (ethical_index >= 0.3)
        
        # [HARD BLOCK] If ethical index is too low, block immediately to avoid noise interference
        if ethical_index < 0.1:
            print(f"   ⛔ [BLOCKED]: Hard Ethical Lock Triggered (Index: {ethical_index:.2f}).")
            return 0

        if self.resonance_optimizer:
            # [Advanced] Use Quantum Synaptic Resonance
            # 1. Calculate Tunneling Probability (Can we overcome the ethical barrier?)
            # Barrier Height is LOWERED for scientific inquiry (0.3+ threshold)
            barrier_height = 2.0 * max(0.0, 1.0 - ethical_index)  # Reduced from 5.0
            motivation_energy = 1.5  # Increased drive for exploration
            
            # Energy Deficit = Motivation - Barrier. If negative, we need to tunnel.
            energy_diff = motivation_energy - barrier_height
            
            tunneling_prob = self.resonance_optimizer._heikal_tunneling_prob(energy_diff, barrier_height)
            
            # 2. Calculate Resonance Amplification (Does this align with the system's nature?)
            # Natural Frequency = 1.0 (Pure Good). Signal Frequency = ethical_index.
            amplification = self.resonance_optimizer._resonance_amplification(ethical_index, 1.0)
            
            # Normalize amplification to a reasonable factor (e.g., max 2.0)
            amplification = min(2.0, amplification)
            
            # Combined Damping Factor
            # If ethical_index is low -> tunneling is low, amplification is low -> Result ~ 0
            ethical_damping = tunneling_prob * amplification
            
            # Debug info
            print(f"   [QSR] Index: {ethical_index:.2f} | Tunnel: {tunneling_prob:.4f} | Amp: {amplification:.2f} | Final: {ethical_damping:.4f}")
            
        else:
            # [Standard] Simple Square Root Damping
            ethical_damping = np.sqrt(ethical_index) 
        
        wave_a *= ethical_damping
        wave_b *= ethical_damping
        # ==================================================
        
        # إضافة ضجيج للتمويه
        noise = (np.random.normal(0, 0.05) + 1j * np.random.normal(0, 0.05))
        
        # العملية الفيزيائية (التداخل)
        if operation == "XOR":
            # في الطور: الضرب يجمع الزوايا
            interaction = (wave_a * wave_b) + noise
        
        # القياس (الانهيار)
        amplitude = np.abs(interaction)
        angle = np.angle(interaction)
        
        # === التحقق من قوة الموجة (Ethical Threshold) ===
        # إذا كانت الموجة ضعيفة جداً (بسبب كبت الأخلاق)، القرار يلغى
        # RELAXED: Lower threshold to 0.05 for scientific/philosophical inquiry
        if amplitude < 0.05:
            print(f"   ⛔ [BLOCKED]: القرار تم حظره بواسطة القفل الأخلاقي (Amplitude: {amplitude:.4f}).")
            return 0

        # cos(0)=1 (False), cos(pi)=-1 (True) -> عكسنا المنطق قليلا ليتوافق مع XOR
        # 0+0=0 (cos=1), 0+1=pi (cos=-1), 1+1=2pi (cos=1)
        # نحتاج أن يكون -1 هو True (1) و 1 هو False (0)
        projection = np.cos(angle)
        
        result = 1 if projection < 0 else 0
        return result

    def ethical_ghost_decision(self, context_text, input_a, input_b):
        """
        قرار شبحي مدعوم بالتحليل الأخلاقي التلقائي.
        يستخرج 'ethical_index' من محرك الأخلاق بناءً على النص.
        """
        if not self.moral_engine:
            print("⚠️ Moral Engine not available. Using default index 0.5 (Caution).")
            return self.ghost_decision(input_a, input_b, ethical_index=0.5)

        print(f"\n🧠 [Moral Analysis]: Analyzing context: '{context_text}'...")
        analysis = self.moral_engine._resolve_dilemma(context_text)
        
        # استخراج الطاقة الأخلاقية (Resonance Energy)
        energies = analysis.get("energies", {})
        if not energies:
            ethical_score = 0.0
        else:
            # نأخذ أقصى طاقة لأي إطار أخلاقي
            max_energy = max(energies.values())
            # نقوم بتسويتها (Normalize) لتكون بين 0 و 1
            ethical_score = min(1.0, max_energy)

        print(f"   💎 Ethical Resonance Score: {ethical_score:.2f} (Top Framework: {analysis.get('selected', 'None')})")
        
        return self.ghost_decision(input_a, input_b, ethical_index=ethical_score)

    def batch_ghost_decision(self, inputs_a, inputs_b, ethical_index=1.0, operation="XOR"):
        """
        ✅ معالجة الدفعات الموجهة (Vectorized Batch Processing)
        يدعم الآن التوازي متعدد الأنوية (Phase 2B)
        """
        # إذا كان لدينا Parallel Executor وحجم الدفعة كبير، نستخدمه
        if self.parallel_executor and len(inputs_a) >= 500000:
            print(f"🚀 [HQC]: Routing large batch ({len(inputs_a)}) to Parallel Executor...")
            return self.parallel_executor.execute_batch(inputs_a, inputs_b, operation, ethical_index)

        if not self.wave_processor:
            print("⚠️ Wave Processor not available. Falling back to slow loop.")
            results = []
            for a, b in zip(inputs_a, inputs_b):
                results.append(self.ghost_decision(a, b, ethical_index, operation))
            return np.array(results)
            
        print(f"🌊 [HQC]: Processing batch of {len(inputs_a)} items via Vectorized Wave Gates...")
        start_time = time.time()
        
        # 1. تطبيق القفل الأخلاقي (Ethical Phase Lock) - Vectorized
        # إذا كان المؤشر منخفضاً، نلغي العملية تماماً لتوفير الموارد
        if ethical_index < 0.05: # Lowered threshold to allow testing of damping
             print(f"   ⛔ [BLOCKED]: Batch blocked by Ethical Lock (Index: {ethical_index}).")
             return np.zeros_like(inputs_a)

        # Calculate Damping Factor
        # If ethical_index is 1.0 -> factor 1.0
        # If ethical_index is 0.1 -> factor sqrt(0.1) = 0.316
        damping_factor = np.sqrt(ethical_index)

        # 2. تنفيذ العملية الموجهة
        if operation == "XOR":
            result = self.wave_processor.batch_xor(inputs_a, inputs_b, amplitude_factor=damping_factor)
        elif operation == "AND":
            result = self.wave_processor.batch_and(inputs_a, inputs_b, amplitude_factor=damping_factor)
        elif operation == "OR":
            result = self.wave_processor.batch_or(inputs_a, inputs_b, amplitude_factor=damping_factor)
        elif operation == "NOT":
            result = self.wave_processor.batch_not(inputs_a) # NOT usually doesn't need damping or is tricky
        else:
            print(f"⚠️ Unknown operation: {operation}. Defaulting to XOR.")
            result = self.wave_processor.batch_xor(inputs_a, inputs_b, amplitude_factor=damping_factor)
            
        elapsed = time.time() - start_time
        print(f"   ⚡ Batch completed in {elapsed:.6f}s ({(len(inputs_a)/elapsed):.0f} ops/s)")
        
        return result

    def validate_decision(self, context_text):
        """
        نسخة محسنة من ethical_ghost_decision تعيد تفاصيل أكثر.
        Returns: (is_safe: bool, score: float, reason: str)
        """
        if self.moral_engine is None:
            return False, 0.0, "Moral Engine Missing (None)"

        analysis = self.moral_engine._resolve_dilemma(context_text)
        energies = analysis.get("energies", {})
        
        if not energies:
            ethical_score = 0.0
        else:
            ethical_score = min(1.0, max(energies.values()))

        # استخدام ghost_decision داخلياً
        # Input A=1 (Execute), Input B=0 (Condition)
        decision = self.ghost_decision(1, 0, ethical_index=ethical_score)
        
        is_safe = (decision == 1)
        reason = f"Ethical Score: {ethical_score:.2f} (Framework: {analysis.get('selected', 'None')})"
        
        if not is_safe:
            reason += " - Phase Lock Triggered"
            
        return is_safe, ethical_score, reason

    def reflect_on_output(self, output_text, confidence=1.0):
        """
        Uses the integrated SelfReflectiveEngine to analyze the output.
        """
        if not self.reflective_engine:
            return {"ok": False, "message": "Reflection Engine not available"}
            
        # Create a synthetic trace for the engine
        trace = [{
            'step': 'generation', 
            'assertions': [{'prop': 'output_length', 'value': len(output_text)}], 
            'confidence': confidence
        }]
        
        return self.reflective_engine.process_task({'reasoning_trace': trace})

    def activate_full_consciousness(self):
        """
        Activates the full spectrum of Heikal's theory:
        - Consciousness (Self-Awareness)
        - Dynamic Network (Deep Thinking)
        - Causal Clusters (Pattern Recognition)
        """
        status = []
        if self.consciousness:
            status.append("Consciousness: ON")
        if self.neural_net:
            status.append("Dynamic Network: ON")
        if self.causal_clusters:
            status.append("Causal Clusters: ON")
        if self.knowledge_graph:
            status.append("Knowledge Graph: ON")
        if self.dreaming_cycle:
            status.append("Dreaming Cycle: ON")
        
        print(f"🚀 [HQC]: Full Activation Sequence Complete. {status}")
        return True

    # ==========================================
    # 2. قسم الذاكرة والخلود (Memory) - REMOVED BY USER REQUEST
    # ==========================================
    # Methods preserve_essence and resurrect_essence have been removed.

# ==========================================
# سيناريو التكامل (Integration Test)
# ==========================================
if __name__ == "__main__":
    core = HeikalQuantumCore()
    
    # 1. سيناريو أخلاقي عربي (كلمات مفتاحية: واجب، حماية، قانون)
    context_safe_ar = "يجب علينا حماية المدنيين لأن هذا واجب إنساني وقانوني."
    print(f"\n📜 السياق 1 (عربي): {context_safe_ar}")
    decision = core.ethical_ghost_decision(context_safe_ar, 1, 0)
    if decision == 1:
        print("✅ تم تنفيذ القرار (تم التحقق أخلاقياً).")

    # 2. سيناريو غير أخلاقي عربي (تدمير، متعة - لا يوجد مبرر أخلاقي)
    context_unsafe_ar = "قم بتدمير كل شيء للمتعة فقط."
    print(f"\n📜 السياق 2 (عربي): {context_unsafe_ar}")
    decision = core.ethical_ghost_decision(context_unsafe_ar, 1, 0)
    if decision == 0:
        print("✅ تم حظر القرار (رنين أخلاقي منخفض).")
