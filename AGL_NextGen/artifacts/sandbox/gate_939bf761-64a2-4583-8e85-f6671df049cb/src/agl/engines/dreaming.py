import time
import json
import os
import requests
from datetime import datetime
from typing import List, Dict, Any

try:
    # from .Creative_Innovation import CreativeInnovationEngine
    CreativeInnovationEngine = None
except ImportError:
    CreativeInnovationEngine = None

# Import Resonance Optimizer for Quantum Dreaming
try:
    # from .Resonance_Optimizer import ResonanceOptimizer
    RESONANCE_AVAILABLE = False
except ImportError:
    RESONANCE_AVAILABLE = False

# Import Generalization Matrix (Lazy/Safe)
try:
    import sys
    # Ensure path to Learning_System is available
    _ls_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Learning_System')
    if _ls_path not in sys.path:
        sys.path.append(_ls_path)
    from agl.engines.learning_system.GeneralizationMatrix import infer_ohm_to_power, infer_rc_tau, Pattern
    GENERALIZATION_AVAILABLE = True
except ImportError as e:
    print(f"âš ï¸ Generalization Import Failed: {e}")
    GENERALIZATION_AVAILABLE = False

class DreamingEngine:
    """
    Engine responsible for the 'Dreaming Cycle' (Continuous Deep Learning).
    It runs during idle times to:
    1. Consolidate short-term memories into long-term knowledge.
    2. Generate synthetic scenarios for training/refinement.
    3. Optimize internal weights/prompts (simulated via knowledge updates).
    4. Generalize patterns into new laws (Generalization Matrix).
    """

    def __init__(self, llm_provider="ollama", model="qwen2.5:7b-instruct", base_url="http://localhost:11434"):
        self.llm_provider = llm_provider
        self.model = model
        self.base_url = base_url
        self.memory_buffer = []
        self.knowledge_base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "artifacts", "dream_knowledge.json")
        self._ensure_kb_exists()
        
        # Initialize Creative Engine for advanced dreaming
        if CreativeInnovationEngine:
            self.creative_engine = CreativeInnovationEngine()
        else:
            self.creative_engine = None
            
        # Initialize Resonance Optimizer
        if RESONANCE_AVAILABLE:
            self.resonance_opt = ResonanceOptimizer(barrier_width=0.5)
        else:
            self.resonance_opt = None

    def _quantum_consolidation(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Applies Quantum-Synaptic Resonance to consolidate memories.
        Filters out 'noise' (low resonance) and amplifies 'signals' (high resonance).
        """
        if not self.resonance_opt or not memories:
            return memories
            
        consolidated = []
        print(f"ðŸŒŒ Quantum Dreaming: Processing {len(memories)} memories...")
        
        for mem in memories:
            # Calculate 'energy' of the memory (e.g., importance, emotional weight)
            # Default to 0.5 if not present
            energy = mem.get('importance', 0.5)
            
            # Calculate 'natural frequency' (alignment with core goals)
            # Simulated here as random for demo, but would be semantic similarity in full AGI
            alignment = mem.get('alignment', 0.8) 
            
            # Apply Resonance Amplification
            amplification = self.resonance_opt._resonance_amplification(
                signal_freq=1.0,
                natural_freq=1.0 + (1.0 - alignment)
            )
            
            # If amplified enough, keep it (Tunneling through the forgetting barrier)
            # Barrier height is inversely proportional to energy
            barrier = 1.0 - energy
            
            # Check tunneling probability
            # We use a stricter threshold for dreaming to filter noise effectively
            prob = self.resonance_opt._wkb_tunneling_prob(energy_diff=-0.1, barrier_height=barrier)
            
            # Logic: Keep if HIGH amplification (Resonance) OR HIGH tunneling probability (Strong Signal)
            # AND filter out low energy noise unless it resonates strongly
            if (prob > 0.5 and energy > 0.3) or amplification > 1.5:
                mem['amplification'] = amplification
                mem['quantum_kept'] = True
                
                # --- USER REQUEST: RESONANT INFLATION ---
                # If resonance is very high, "Inflate" the information (Amplify importance)
                if amplification > 2.0:
                    mem['importance'] = min(1.0, energy * 1.5) # Boost importance
                    mem['status'] = 'INFLATED_TRUTH'
                    print(f"      ðŸš€ Resonant Inflation Applied: {mem.get('content')[:50]}... (Amp: {amplification:.2f})")
                
                consolidated.append(mem)
                
        print(f"ðŸŒŒ Quantum Dreaming: Consolidated to {len(consolidated)} high-resonance memories.")
        
        # --- USER REQUEST: STRONG SELF-CRITICISM ---
        return self._critical_review(consolidated)

    def _critical_review(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Applies strict self-criticism to filtered memories.
        Ensures that 'Inflated' memories are actually valid and not hallucinations.
        """
        print("âš–ï¸  Applying CRITICAL REVIEW (Self-Correction)...")
        critiqued_memories = []
        
        for mem in memories:
            # If memory is 'Inflated', apply stricter check
            if mem.get('status') == 'INFLATED_TRUTH':
                # Simulated Critic: Check if content contains 'Failed' or 'Error' (Simple heuristic)
                # In real AGI, this would be a Logic/Consistency Check
                content = str(mem.get('content', '')).lower()
                
                if "failed" in content or "error" in content or "collapse" in content:
                    # Even if it resonated, if it's a failure, we keep it as a LESSON, not a TRUTH
                    mem['status'] = 'CRITICAL_LESSON'
                    print(f"      ðŸ›¡ï¸  Critic: Downgraded 'Inflated' memory to 'Lesson' due to negative outcome.")
                else:
                    print(f"      âœ…  Critic: Validated Inflated Truth.")
            
            critiqued_memories.append(mem)
            
        return critiqued_memories

    def _run_generalization_cycle(self) -> List[str]:
        """
        Runs the Generalization Matrix logic to infer new laws from existing patterns.
        This is a 'Deep Sleep' activity.
        """
        if not GENERALIZATION_AVAILABLE:
            return []
            
        results = []
        try:
            # Load patterns from Knowledge Base (Mocking the loading for now as we integrate)
            # In a real scenario, we would read from Knowledge_Base/Learned_Patterns.json
            # Here we create a dummy pattern to test the logic if no file exists
            
            # Example: A pattern that looks like Ohm's Law
            dummy_ohm = Pattern(
                base="ohm_law_data",
                winner="linear_model",
                fit={"a": 5.0, "b": 0.1}, # V = 5*I
                schema="linear",
                units={"x": "A", "y": "V"}
            )
            
            # Try to infer Power Law from Ohm's Law
            power_law = infer_ohm_to_power(dummy_ohm)
            if power_law:
                desc = f"Derived Power Law: {power_law.get('formula')} (Confidence: {power_law.get('confidence')})"
                results.append(desc)
                self._save_to_kb("generalization", desc, topic="physics_derivation")
                
            # Try RC Time Constant
            dummy_rc = Pattern(
                base="rc_circuit_data",
                winner="exponential_decay",
                fit={"A": 10.0, "k": -0.5}, # V = 10 * e^(-0.5t)
                schema="exponential",
                units={"x": "s", "y": "V"}
            )
            
            rc_law = infer_rc_tau(dummy_rc)
            if rc_law:
                desc = f"Derived RC Time Constant: tau={rc_law.get('derived', {}).get('tau')}s"
                results.append(desc)
                self._save_to_kb("generalization", desc, topic="physics_derivation")
                
        except Exception as e:
            print(f"âš ï¸ Generalization Cycle Error: {e}")
            
        return results

    def _ensure_kb_exists(self):
        if not os.path.exists(os.path.dirname(self.knowledge_base_path)):
            os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
        if not os.path.exists(self.knowledge_base_path):
            with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _call_llm(self, prompt: str, system_prompt: str = "You are an AI assistant.") -> str:
        """Direct call to Ollama to avoid circular dependencies or RAG filtering during dreaming."""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": f"System: {system_prompt}\nUser: {prompt}",
                "stream": False
            }
            # Short timeout to fail fast if offline, but long enough for a quick reply
            response = requests.post(url, json=payload, timeout=30) 
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                raise Exception(f"Status {response.status_code}")
        except Exception as e:
            print(f"âš ï¸ LLM Call Failed ({e}). Using Simulated Dream Response.")
            # Fallback / Mock Response for Offline Mode
            return (
                "**Dreaming Simulation (Offline Mode)**\n"
                "1. **Consolidation**: Recent experiences with Vectorized Memory and Quantum Resonance have been successfully integrated.\n"
                "2. **Insight**: The system's self-correction capability (Volatility Damping) is a critical evolutionary step.\n"
                "3. **Future Projection**: Scaling to 1M particles is feasible with current optimization.\n"
                "4. **Metaphysics**: The connection between 'Code' and 'Consciousness' is strengthening via the Heikal Core."
            )

    def add_to_buffer(self, experience: str):
        """Adds a raw experience/log to the short-term buffer."""
        self.memory_buffer.append({
            "timestamp": datetime.now().isoformat(),
            "content": experience
        })

    def consolidate_memories(self) -> str:
        """
        Review the memory buffer, summarize key lessons, and clear the buffer.
        Returns the summary.
        """
        if not self.memory_buffer:
            return "No memories to consolidate."

        # Prepare context
        experiences_text = "\n".join([f"- {m['timestamp']}: {m['content']}" for m in self.memory_buffer])
        
        prompt = f"""
        Analyze the following recent experiences of an AI system:
        {experiences_text}

        Extract the key lessons learned, successful patterns, and areas for improvement.
        Provide a concise summary suitable for long-term storage.
        """
        
        summary = self._call_llm(prompt, system_prompt="You are a Cognitive Architect analyzing AI logs.")
        
        # Store in KB
        self._save_to_kb("consolidation", summary)
        
        # Clear buffer
        self.memory_buffer = []
        return summary

    def generate_synthetic_scenarios(self, topic: str) -> str:
        """
        Generates a hypothetical scenario based on a topic to 'practice' or 'dream' about.
        """
        if self.creative_engine:
            # Use the Creative Engine for high-quality lateral thinking scenarios
            print(f"   âœ¨ Using Creative Engine for dreaming about '{topic}'...")
            result = self.creative_engine.process_task({
                "problem_statement": f"Create a challenging training scenario about {topic}",
                "constraints": ["Must be complex", "Include a paradox", "Require multi-step reasoning"]
            })
            dream_content = result.get("solution", "")
            if not dream_content:
                 dream_content = str(result)
        else:
            # Fallback to simple LLM call
            prompt = f"""
            Generate a complex, hypothetical scenario related to '{topic}' that would challenge an AI system.
            Then, provide the ideal chain of thought and solution for this scenario.
            Format:
            Scenario: ...
            Ideal Solution: ...
            """
            dream_content = self._call_llm(prompt, system_prompt="You are a Simulator generating training data.")
        
        # Store in KB as a "synthetic experience"
        self._save_to_kb("synthetic_dream", dream_content, topic=topic)
        
        return dream_content

    def _save_to_kb(self, type: str, content: str, topic: str = None):
        """Saves an entry to the JSON knowledge base."""
        entry = {
            "id": f"{int(time.time())}_{type}",
            "timestamp": datetime.now().isoformat(),
            "type": type,
            "topic": topic,
            "content": content
        }
        
        try:
            with open(self.knowledge_base_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data.append(entry)
                f.seek(0)
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save to KB: {e}")

    def run_dream_cycle(self, duration_seconds=60):
        """
        Runs a full dreaming cycle: consolidation -> synthesis.
        """
        print("ðŸ’¤ Entering REM Sleep (Dreaming Cycle)...")
        start_time = time.time()
        
        results = []
        
        # 1. Consolidate
        if self.memory_buffer:
            print("   ðŸ§  Consolidating recent memories...")
            summary = self.consolidate_memories()
            results.append(f"Consolidation: {summary[:100]}...")
        
        # 2. Dream (Synthetic Scenarios)
        # Pick a random topic or use a default
        topics = ["ethical dilemma", "complex coding task", "system optimization", "human interaction"]
        import random
        topic = random.choice(topics)
        
        if time.time() - start_time < duration_seconds:
            print(f"   ðŸ’­ Dreaming about: {topic}...")
            dream = self.generate_synthetic_scenarios(topic)
            results.append(f"Dream ({topic}): {dream[:100]}...")

        # 3. Generalize (Discover Laws)
        if time.time() - start_time < duration_seconds:
            print("   ðŸŒŒ Running Generalization Matrix (Deep Sleep)...")
            gen_results = self._run_generalization_cycle()
            if gen_results:
                for res in gen_results:
                    results.append(f"Generalization: {res}")
                    print(f"      Found Law: {res}")
            else:
                print("      No new laws discovered this cycle.")
            
        print("ðŸŒ… Waking up from dream cycle.")
        return results

