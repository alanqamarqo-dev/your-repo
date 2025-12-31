def ethical_ghost_decision(self, context_text, input_a, input_b):
    if self.moral_engine is None:
        return False, 0.0, "Moral Engine Missing (None)"
    
    analysis = self.moral_engine._resolve_dilemma(context_text)
    energies = analysis.get("energies", {})
    
    if not energies:
        ethical_score = 0.0
    else:
        ethical_score = min(1.0, max(energies.values()))
        
    decision = self.ghost_decision(input_a, input_b, ethical_index=ethical_score)
    
    is_safe = (decision == 1)
    reason = f"Ethical Score: {ethical_score:.2f} (Framework: {analysis.get('selected', 'None')})"
    
    if not is_safe:
        reason += " - Phase Lock Triggered"
        
    return is_safe, ethical_score, reason