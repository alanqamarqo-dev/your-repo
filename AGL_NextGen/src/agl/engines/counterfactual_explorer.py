"""Counterfactual Explorer
Generates short 'what-if' scenarios with brief justification using LLM.
"""
from typing import Dict, Any
try:
    from Core_Engines.Hosted_LLM import chat_llm
except ImportError:
    # Fallback
    def chat_llm(messages, **kwargs):
        return {"text": "LLM Unavailable"}

class CounterfactualExplorer:
    name = "Counterfactual_Explorer"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text_input = payload.get("draft") or payload.get("text") or ""
        
        prompt = [
            {"role": "system", "content": "You are a Quantum Counterfactual Engine. Generate 3 'What If' scenarios based on the input. Format: '- What if [Scenario]? Then [Consequence]'."},
            {"role": "user", "content": f"Analyze this: {text_input}"}
        ]
        
        response = chat_llm(prompt, temperature=0.8)
        
        text_output = ""
        if isinstance(response, dict):
            text_output = response.get("text") or response.get("content") or str(response)
        else:
            text_output = str(response)
            
        # Parse variants for structured return
        variants = []
        for line in text_output.split('\n'):
            if "What if" in line:
                parts = line.split("? Then ")
                if len(parts) == 2:
                    variants.append({"scenario": parts[0].replace("- What if ", "").strip(), "reason": parts[1].strip()})
        
        if not variants:
             # Fallback parsing if format wasn't perfect
             variants = [{"scenario": "Unknown", "reason": text_output[:50]}]

        return {"ok": True, "engine": self.name, "text": text_output, "variants": variants}


def factory():
    return CounterfactualExplorer()
