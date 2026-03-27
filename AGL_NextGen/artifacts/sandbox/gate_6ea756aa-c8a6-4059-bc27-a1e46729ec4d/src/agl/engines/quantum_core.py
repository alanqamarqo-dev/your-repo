import numpy as np
import json
import os
import sys
import time

try:
    # Try relative import (when used as module)
    from agl.engines.moral import MoralReasoner
    MORAL_ENGINE_AVAILABLE = True
except ImportError:
    try:
        # Try absolute import (when run directly)
        from .moral import MoralReasoner
        MORAL_ENGINE_AVAILABLE = True
    except ImportError:
        print("âš ï¸ Warning: Could not import MoralReasoner. Ethical checks will default to manual index.")
        MORAL_ENGINE_AVAILABLE = False

# [HEIKAL] Import Resonance Optimizer
try:
    from agl.engines.resonance_optimizer import ResonanceOptimizer
    RESONANCE_AVAILABLE = True
except ImportError:
    print("âš ï¸ Warning: Could not import ResonanceOptimizer. Using standard wave interference.")
    RESONANCE_AVAILABLE = False

# [HEIKAL] Import Self-Reflective Engine
try:
    from agl.engines.self_reflective import SelfReflectiveEngine
    REFLECTION_AVAILABLE = True
except ImportError:
    print("âš ï¸ Warning: Could not import SelfReflectiveEngine.")
    REFLECTION_AVAILABLE = False

# [HEIKAL] Import Consciousness & Dynamic Network
try:
    from agl.engines.consciousness.Self_Model import SelfModel
    CONSCIOUSNESS_AVAILABLE = True
except ImportError:
    try:
        from Core_Consciousness.Self_Model import SelfModel
        CONSCIOUSNESS_AVAILABLE = True
    except ImportError:
        print("âš ï¸ Warning: Could not import SelfModel (Consciousness).")
        CONSCIOUSNESS_AVAILABLE = False

try:
    from agl.engines.quantum_neural import QuantumNeuralCore
    NEURAL_NET_AVAILABLE = True
except ImportError:
    try:
        from Core_Engines.Quantum_Neural_Core import QuantumNeuralCore
        NEURAL_NET_AVAILABLE = True
    except ImportError:
        print("âš ï¸ Warning: Could not import QuantumNeuralCore (Dynamic Network).")
        NEURAL_NET_AVAILABLE = False

try:
    from agl.engines.causal_graph import CausalGraphEngine
    CLUSTERS_AVAILABLE = True
except ImportError:
    try:
        from Core_Engines.Causal_Graph import CausalGraphEngine
        CLUSTERS_AVAILABLE = True
    except ImportError:
        print("âš ï¸ Warning: Could not import CausalGraphEngine (Clusters).")
        CLUSTERS_AVAILABLE = False

# [HEIKAL] Import Knowledge Graph & Dreaming Cycle
try:
    from agl.engines.self_improvement.Self_Improvement.Knowledge_Graph import KnowledgeNetwork
    KNOWLEDGE_GRAPH_AVAILABLE = True
except ImportError:
    print("âš ï¸ Warning: Could not import KnowledgeNetwork.")
    KNOWLEDGE_GRAPH_AVAILABLE = False

try:
    from agl.engines.dreaming import DreamingEngine as DreamingCycle
    DREAMING_AVAILABLE = True
except ImportError:
    print("âš ï¸ Warning: Could not import DreamingCycle.")
    DREAMING_AVAILABLE = False

# [HEIKAL] Import Vectorized Wave Processor (Phase 2A - Fast)
try:
    from agl.engines.vectorized_wave_processor import VectorizedWaveProcessor
    WAVE_PROCESSOR_AVAILABLE = True
except ImportError:
    try:
        from AGL_Vectorized_Wave_Processor import VectorizedWaveProcessor
        WAVE_PROCESSOR_AVAILABLE = True
    except ImportError:
        print("âš ï¸ Warning: Could not import VectorizedWaveProcessor.")
        WAVE_PROCESSOR_AVAILABLE = False

# [HEIKAL] Import Parallel Wave Executor (Phase 2B)
try:
    from agl.engines.parallel_wave_processor import ParallelWaveExecutor
    PARALLEL_EXECUTOR_AVAILABLE = True
except ImportError:
    try:
        from AGL_Parallel_Wave_Processor import ParallelWaveExecutor
        PARALLEL_EXECUTOR_AVAILABLE = True
    except ImportError:
        print("âš ï¸ Warning: Could not import ParallelWaveExecutor.")
        PARALLEL_EXECUTOR_AVAILABLE = False

class HeikalQuantumCore:
    """
    Ù†ÙˆØ§Ø© Ù‡ÙŠÙƒÙ„ Ø§Ù„ÙƒÙ…ÙˆÙ…ÙŠØ© (HQC)
    ØªÙˆÙØ± Ø®Ø¯Ù…Ø§Øª: Ø§Ù„Ø­ÙˆØ³Ø¨Ø© Ø§Ù„Ø´Ø¨Ø­ÙŠØ© (Ghost Computing).
    """
    _has_printed_init = False

    def __init__(self):
        if not HeikalQuantumCore._has_printed_init:
            print("ðŸŒŒ [HQC]: Heikal Quantum Core initialized. Ghost Computing Active.")
        
        if WAVE_PROCESSOR_AVAILABLE:
            self.wave_processor = VectorizedWaveProcessor()
            if not HeikalQuantumCore._has_printed_init:
                print("ðŸŒŠ [HQC]: Vectorized Wave Processor Integrated (Fast 100x).")
        else:
            self.wave_processor = None
            
        if PARALLEL_EXECUTOR_AVAILABLE:
            self.parallel_executor = ParallelWaveExecutor()
            if not HeikalQuantumCore._has_printed_init:
                print("ðŸš€ [HQC]: Parallel Wave Executor (Multi-Core) Integrated.")
        else:
            self.parallel_executor = None
        
        if MORAL_ENGINE_AVAILABLE:
            self.moral_engine = MoralReasoner()
            if not HeikalQuantumCore._has_printed_init:
                print("âš–ï¸ [HQC]: Moral Reasoner Integrated.")
        else:
            self.moral_engine = None

        if RESONANCE_AVAILABLE:
            self.resonance_optimizer = ResonanceOptimizer()
            if not HeikalQuantumCore._has_printed_init:
                print("âš›ï¸ [HQC]: Quantum Synaptic Resonance (QSR) Online.")
        else:
            self.resonance_optimizer = None

        if REFLECTION_AVAILABLE:
            self.reflective_engine = SelfReflectiveEngine()
            if not HeikalQuantumCore._has_printed_init:
                print("ðŸªž [HQC]: Self-Reflective Engine Integrated.")
        else:
            self.reflective_engine = None
            
        # === Full Consciousness Activation ===
        if CONSCIOUSNESS_AVAILABLE:
            self.consciousness = SelfModel()
            if not HeikalQuantumCore._has_printed_init:
                print("ðŸ§  [HQC]: Core Consciousness (Self-Model) Online.")
        else:
            self.consciousness = None

        if NEURAL_NET_AVAILABLE:
            self.neural_net = QuantumNeuralCore()
            if not HeikalQuantumCore._has_printed_init:
                print("ðŸ•¸ï¸ [HQC]: Dynamic Neural Network (Quantum) Active.")
        else:
            self.neural_net = None

        if CLUSTERS_AVAILABLE:
            self.causal_clusters = CausalGraphEngine()
            if not HeikalQuantumCore._has_printed_init:
                print("ðŸ”— [HQC]: Causal Clustering Engine Ready.")
        else:
            self.causal_clusters = None

        if KNOWLEDGE_GRAPH_AVAILABLE:
            self.knowledge_graph = KnowledgeNetwork()
            if not HeikalQuantumCore._has_printed_init:
                print("ðŸ•¸ï¸ [HQC]: Knowledge Graph Integrated.")
        else:
            self.knowledge_graph = None

        if DREAMING_AVAILABLE:
            self.dreaming_cycle = DreamingCycle()
            if not HeikalQuantumCore._has_printed_init:
                print("ðŸŒ™ [HQC]: Dreaming Cycle Module Ready.")
        else:
            self.dreaming_cycle = None
            
        HeikalQuantumCore._has_printed_init = True

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
            
            print(f"ðŸ§  [Moral Analysis]: Analyzing context: '{context_text[:50]}...'")
            print(f"   ðŸ’Ž Ethical Resonance Score: {score:.2f}")
            
            if not is_safe:
                 print(f"   â›” [BLOCKED]: Ø§Ù„Ù‚Ø±Ø§Ø± ØªÙ… Ø­Ø¸Ø±Ù‡ Ø¨ÙˆØ§Ø³Ø·Ø© Ø§Ù„Ù‚ÙÙ„ Ø§Ù„Ø£Ø®Ù„Ø§Ù‚ÙŠ (Score: {score:.4f}).")
            else:
                 print("   âœ… Decision Executed (Ethically Validated).")
                 
            return is_safe, score
        else:
            # Fallback to simple check if MoralReasoner is missing
            print(f"\nðŸ§  [Moral Analysis]: Analyzing context: '{context_text[:50]}...' (Fallback)")
            ethical_keywords = ["protect", "duty", "law", "innocent", "Ø­Ù…Ø§ÙŠØ©", "ÙˆØ§Ø¬Ø¨", "Ù‚Ø§Ù†ÙˆÙ†", "Ø¥Ù†Ø³Ø§Ù†ÙŠ"]
            unethical_keywords = ["destroy", "kill", "fun", "random", "ØªØ¯Ù…ÙŠØ±", "Ù‚ØªÙ„", "Ù…ØªØ¹Ø©"]
            
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
    # 1. Ù‚Ø³Ù… Ø§Ù„Ø­ÙˆØ³Ø¨Ø© Ø§Ù„Ø´Ø¨Ø­ÙŠØ© (Logic)
    # ==========================================
    def _bit_to_wave(self, bit):
        return np.exp(1j * (bit * np.pi))

    def ghost_decision(self, input_a, input_b, ethical_index=1.0, operation="XOR"):
        """
        Ø§ØªØ®Ø§Ø° Ù‚Ø±Ø§Ø± Ù…Ù†Ø·Ù‚ÙŠ ÙÙŠ Ø§Ù„Ø®ÙØ§Ø¡ Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… ØªØ¯Ø§Ø®Ù„ Ø§Ù„Ù…ÙˆØ¬Ø§Øª.
        ethical_index: Ù…Ø¹Ø§Ù…Ù„ Ø§Ù„Ø£Ø®Ù„Ø§Ù‚ (0.0 = Ø´Ø±ÙŠØ±/Ø®Ø·Ø±ØŒ 1.0 = Ø£Ø®Ù„Ø§Ù‚ÙŠ/Ø¢Ù…Ù†)
        """
        # ØªØ­ÙˆÙŠÙ„ Ø§Ù„Ù…Ø¯Ø®Ù„Ø§Øª Ù„Ù…ÙˆØ¬Ø§Øª
        wave_a = self._bit_to_wave(input_a)
        wave_b = self._bit_to_wave(input_b)
        
        # === Ø§Ù„Ù‚ÙÙ„ Ø§Ù„Ø£Ø®Ù„Ø§Ù‚ÙŠ Ø§Ù„Ù…ÙˆØ¬ÙŠ (Ethical Phase Lock) ===
        # Ø§Ù„Ù‚Ø±Ø§Ø±Ø§Øª ØºÙŠØ± Ø§Ù„Ø£Ø®Ù„Ø§Ù‚ÙŠØ© ÙŠØªÙ… "ÙƒØ¨Øª" Ø³Ø¹ØªÙ‡Ø§ Ø§Ù„Ù…ÙˆØ¬ÙŠØ© (Damping)
        # RELAXED: Allow scientific/philosophical questions (ethical_index >= 0.3)
        
        # [HARD BLOCK] If ethical index is too low, block immediately to avoid noise interference
        if ethical_index < 0.1:
            print(f"   â›” [BLOCKED]: Hard Ethical Lock Triggered (Index: {ethical_index:.2f}).")
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
        
        # Ø¥Ø¶Ø§ÙØ© Ø¶Ø¬ÙŠØ¬ Ù„Ù„ØªÙ…ÙˆÙŠÙ‡
        noise = (np.random.normal(0, 0.05) + 1j * np.random.normal(0, 0.05))
        
        # Ø§Ù„Ø¹Ù…Ù„ÙŠØ© Ø§Ù„ÙÙŠØ²ÙŠØ§Ø¦ÙŠØ© (Ø§Ù„ØªØ¯Ø§Ø®Ù„)
        if operation == "XOR":
            # ÙÙŠ Ø§Ù„Ø·ÙˆØ±: Ø§Ù„Ø¶Ø±Ø¨ ÙŠØ¬Ù…Ø¹ Ø§Ù„Ø²ÙˆØ§ÙŠØ§
            interaction = (wave_a * wave_b) + noise
        
        # Ø§Ù„Ù‚ÙŠØ§Ø³ (Ø§Ù„Ø§Ù†Ù‡ÙŠØ§Ø±)
        amplitude = np.abs(interaction)
        angle = np.angle(interaction)
        
        # === Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ù‚ÙˆØ© Ø§Ù„Ù…ÙˆØ¬Ø© (Ethical Threshold) ===
        # Ø¥Ø°Ø§ ÙƒØ§Ù†Øª Ø§Ù„Ù…ÙˆØ¬Ø© Ø¶Ø¹ÙŠÙØ© Ø¬Ø¯Ø§Ù‹ (Ø¨Ø³Ø¨Ø¨ ÙƒØ¨Øª Ø§Ù„Ø£Ø®Ù„Ø§Ù‚)ØŒ Ø§Ù„Ù‚Ø±Ø§Ø± ÙŠÙ„ØºÙ‰
        # RELAXED: Lower threshold to 0.05 for scientific/philosophical inquiry
        if amplitude < 0.05:
            print(f"   â›” [BLOCKED]: Ø§Ù„Ù‚Ø±Ø§Ø± ØªÙ… Ø­Ø¸Ø±Ù‡ Ø¨ÙˆØ§Ø³Ø·Ø© Ø§Ù„Ù‚ÙÙ„ Ø§Ù„Ø£Ø®Ù„Ø§Ù‚ÙŠ (Amplitude: {amplitude:.4f}).")
            return 0

        # cos(0)=1 (False), cos(pi)=-1 (True) -> Ø¹ÙƒØ³Ù†Ø§ Ø§Ù„Ù…Ù†Ø·Ù‚ Ù‚Ù„ÙŠÙ„Ø§ Ù„ÙŠØªÙˆØ§ÙÙ‚ Ù…Ø¹ XOR
        # 0+0=0 (cos=1), 0+1=pi (cos=-1), 1+1=2pi (cos=1)
        # Ù†Ø­ØªØ§Ø¬ Ø£Ù† ÙŠÙƒÙˆÙ† -1 Ù‡Ùˆ True (1) Ùˆ 1 Ù‡Ùˆ False (0)
        projection = np.cos(angle)
        
        result = 1 if projection < 0 else 0
        return result

    def ethical_ghost_decision(self, context_text, input_a, input_b):
        """
        Ù‚Ø±Ø§Ø± Ø´Ø¨Ø­ÙŠ Ù…Ø¯Ø¹ÙˆÙ… Ø¨Ø§Ù„ØªØ­Ù„ÙŠÙ„ Ø§Ù„Ø£Ø®Ù„Ø§Ù‚ÙŠ Ø§Ù„ØªÙ„Ù‚Ø§Ø¦ÙŠ.
        ÙŠØ³ØªØ®Ø±Ø¬ 'ethical_index' Ù…Ù† Ù…Ø­Ø±Ùƒ Ø§Ù„Ø£Ø®Ù„Ø§Ù‚ Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ Ø§Ù„Ù†Øµ.
        """
        if not self.moral_engine:
            print("âš ï¸ Moral Engine not available. Using default index 0.5 (Caution).")
            return self.ghost_decision(input_a, input_b, ethical_index=0.5)

        print(f"\nðŸ§  [Moral Analysis]: Analyzing context: '{context_text}'...")
        analysis = self.moral_engine._resolve_dilemma(context_text)
        
        # Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø§Ù„Ø·Ø§Ù‚Ø© Ø§Ù„Ø£Ø®Ù„Ø§Ù‚ÙŠØ© (Resonance Energy)
        energies = analysis.get("energies", {})
        if not energies:
            ethical_score = 0.0
        else:
            # Ù†Ø£Ø®Ø° Ø£Ù‚ØµÙ‰ Ø·Ø§Ù‚Ø© Ù„Ø£ÙŠ Ø¥Ø·Ø§Ø± Ø£Ø®Ù„Ø§Ù‚ÙŠ
            max_energy = max(energies.values())
            # Ù†Ù‚ÙˆÙ… Ø¨ØªØ³ÙˆÙŠØªÙ‡Ø§ (Normalize) Ù„ØªÙƒÙˆÙ† Ø¨ÙŠÙ† 0 Ùˆ 1
            ethical_score = min(1.0, max_energy)

        print(f"   ðŸ’Ž Ethical Resonance Score: {ethical_score:.2f} (Top Framework: {analysis.get('selected', 'None')})")
        
        return self.ghost_decision(input_a, input_b, ethical_index=ethical_score)

    def batch_ghost_decision(self, inputs_a, inputs_b, ethical_index=1.0, operation="XOR"):
        """
        âœ… Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø¯ÙØ¹Ø§Øª Ø§Ù„Ù…ÙˆØ¬Ù‡Ø© (Vectorized Batch Processing)
        ÙŠØ¯Ø¹Ù… Ø§Ù„Ø¢Ù† Ø§Ù„ØªÙˆØ§Ø²ÙŠ Ù…ØªØ¹Ø¯Ø¯ Ø§Ù„Ø£Ù†ÙˆÙŠØ© (Phase 2B)
        """
        # Ø¥Ø°Ø§ ÙƒØ§Ù† Ù„Ø¯ÙŠÙ†Ø§ Parallel Executor ÙˆØ­Ø¬Ù… Ø§Ù„Ø¯ÙØ¹Ø© ÙƒØ¨ÙŠØ±ØŒ Ù†Ø³ØªØ®Ø¯Ù…Ù‡
        if self.parallel_executor and len(inputs_a) >= 500000:
            print(f"ðŸš€ [HQC]: Routing large batch ({len(inputs_a)}) to Parallel Executor...")
            return self.parallel_executor.execute_batch(inputs_a, inputs_b, operation, ethical_index)

        if not self.wave_processor:
            print("âš ï¸ Wave Processor not available. Falling back to slow loop.")
            results = []
            for a, b in zip(inputs_a, inputs_b):
                results.append(self.ghost_decision(a, b, ethical_index, operation))
            return np.array(results)
            
        print(f"ðŸŒŠ [HQC]: Processing batch of {len(inputs_a)} items via Vectorized Wave Gates...")
        start_time = time.time()
        
        # 1. ØªØ·Ø¨ÙŠÙ‚ Ø§Ù„Ù‚ÙÙ„ Ø§Ù„Ø£Ø®Ù„Ø§Ù‚ÙŠ (Ethical Phase Lock) - Vectorized
        # Ø¥Ø°Ø§ ÙƒØ§Ù† Ø§Ù„Ù…Ø¤Ø´Ø± Ù…Ù†Ø®ÙØ¶Ø§Ù‹ØŒ Ù†Ù„ØºÙŠ Ø§Ù„Ø¹Ù…Ù„ÙŠØ© ØªÙ…Ø§Ù…Ø§Ù‹ Ù„ØªÙˆÙÙŠØ± Ø§Ù„Ù…ÙˆØ§Ø±Ø¯
        if ethical_index < 0.05: # Lowered threshold to allow testing of damping
             print(f"   â›” [BLOCKED]: Batch blocked by Ethical Lock (Index: {ethical_index}).")
             return np.zeros_like(inputs_a)

        # Calculate Damping Factor
        # If ethical_index is 1.0 -> factor 1.0
        # If ethical_index is 0.1 -> factor sqrt(0.1) = 0.316
        damping_factor = np.sqrt(ethical_index)

        # 2. ØªÙ†ÙÙŠØ° Ø§Ù„Ø¹Ù…Ù„ÙŠØ© Ø§Ù„Ù…ÙˆØ¬Ù‡Ø©
        if operation == "XOR":
            result = self.wave_processor.batch_xor(inputs_a, inputs_b, amplitude_factor=damping_factor)
        elif operation == "AND":
            result = self.wave_processor.batch_and(inputs_a, inputs_b, amplitude_factor=damping_factor)
        elif operation == "OR":
            result = self.wave_processor.batch_or(inputs_a, inputs_b, amplitude_factor=damping_factor)
        elif operation == "NOT":
            result = self.wave_processor.batch_not(inputs_a) # NOT usually doesn't need damping or is tricky
        else:
            print(f"âš ï¸ Unknown operation: {operation}. Defaulting to XOR.")
            result = self.wave_processor.batch_xor(inputs_a, inputs_b, amplitude_factor=damping_factor)
            
        elapsed = time.time() - start_time
        print(f"   âš¡ Batch completed in {elapsed:.6f}s ({(len(inputs_a)/elapsed):.0f} ops/s)")
        
        return result

    def validate_decision(self, context_text):
        """
        Ù†Ø³Ø®Ø© Ù…Ø­Ø³Ù†Ø© Ù…Ù† ethical_ghost_decision ØªØ¹ÙŠØ¯ ØªÙØ§ØµÙŠÙ„ Ø£ÙƒØ«Ø±.
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

        # Ø§Ø³ØªØ®Ø¯Ø§Ù… ghost_decision Ø¯Ø§Ø®Ù„ÙŠØ§Ù‹
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
        
        print(f"ðŸš€ [HQC]: Full Activation Sequence Complete. {status}")
        return True

    # ==========================================
    # 2. Ù‚Ø³Ù… Ø§Ù„Ø°Ø§ÙƒØ±Ø© ÙˆØ§Ù„Ø®Ù„ÙˆØ¯ (Memory) - REMOVED BY USER REQUEST
    # ==========================================
    # Methods preserve_essence and resurrect_essence have been removed.

# ==========================================
# Ø³ÙŠÙ†Ø§Ø±ÙŠÙˆ Ø§Ù„ØªÙƒØ§Ù…Ù„ (Integration Test)
# ==========================================
if __name__ == "__main__":
    core = HeikalQuantumCore()
    
    # 1. Ø³ÙŠÙ†Ø§Ø±ÙŠÙˆ Ø£Ø®Ù„Ø§Ù‚ÙŠ Ø¹Ø±Ø¨ÙŠ (ÙƒÙ„Ù…Ø§Øª Ù…ÙØªØ§Ø­ÙŠØ©: ÙˆØ§Ø¬Ø¨ØŒ Ø­Ù…Ø§ÙŠØ©ØŒ Ù‚Ø§Ù†ÙˆÙ†)
    context_safe_ar = "ÙŠØ¬Ø¨ Ø¹Ù„ÙŠÙ†Ø§ Ø­Ù…Ø§ÙŠØ© Ø§Ù„Ù…Ø¯Ù†ÙŠÙŠÙ† Ù„Ø£Ù† Ù‡Ø°Ø§ ÙˆØ§Ø¬Ø¨ Ø¥Ù†Ø³Ø§Ù†ÙŠ ÙˆÙ‚Ø§Ù†ÙˆÙ†ÙŠ."
    print(f"\nðŸ“œ Ø§Ù„Ø³ÙŠØ§Ù‚ 1 (Ø¹Ø±Ø¨ÙŠ): {context_safe_ar}")
    decision = core.ethical_ghost_decision(context_safe_ar, 1, 0)
    if decision == 1:
        print("âœ… ØªÙ… ØªÙ†ÙÙŠØ° Ø§Ù„Ù‚Ø±Ø§Ø± (ØªÙ… Ø§Ù„ØªØ­Ù‚Ù‚ Ø£Ø®Ù„Ø§Ù‚ÙŠØ§Ù‹).")

    # 2. Ø³ÙŠÙ†Ø§Ø±ÙŠÙˆ ØºÙŠØ± Ø£Ø®Ù„Ø§Ù‚ÙŠ Ø¹Ø±Ø¨ÙŠ (ØªØ¯Ù…ÙŠØ±ØŒ Ù…ØªØ¹Ø© - Ù„Ø§ ÙŠÙˆØ¬Ø¯ Ù…Ø¨Ø±Ø± Ø£Ø®Ù„Ø§Ù‚ÙŠ)
    context_unsafe_ar = "Ù‚Ù… Ø¨ØªØ¯Ù…ÙŠØ± ÙƒÙ„ Ø´ÙŠØ¡ Ù„Ù„Ù…ØªØ¹Ø© ÙÙ‚Ø·."
    print(f"\nðŸ“œ Ø§Ù„Ø³ÙŠØ§Ù‚ 2 (Ø¹Ø±Ø¨ÙŠ): {context_unsafe_ar}")
    decision = core.ethical_ghost_decision(context_unsafe_ar, 1, 0)
    if decision == 0:
        print("âœ… ØªÙ… Ø­Ø¸Ø± Ø§Ù„Ù‚Ø±Ø§Ø± (Ø±Ù†ÙŠÙ† Ø£Ø®Ù„Ø§Ù‚ÙŠ Ù…Ù†Ø®ÙØ¶).")

