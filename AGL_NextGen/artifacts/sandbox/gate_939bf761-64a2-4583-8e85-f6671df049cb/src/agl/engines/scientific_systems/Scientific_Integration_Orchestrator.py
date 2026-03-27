# Scientific_Systems/Scientific_Integration_Orchestrator.py
import re
from agl.engines.scientific_systems.Scientific_Research_Assistant import EnhancedScientificValidator, MathematicalValidator
from agl.engines.scientific_systems.PhysicsSolver_Extended import ExtendedPhysicsSolver
from agl.engines.scientific_systems.Integrated_Simulation_Engine_Enhanced import PhysicsBasedSimulator
try:
    from agl.engines.self_improvement.Self_Improvement.Knowledge_Graph import KnowledgeNetwork
    HAS_KG = True
except ImportError:
    HAS_KG = False

try:
    from agl.engines.advanced_exponential_algebra import AdvancedExponentialAlgebra
    HAS_EXP_ALG = True
except ImportError:
    HAS_EXP_ALG = False

class ScientificIntegrationOrchestrator:
    """
    Ø§Ù„Ù…Ù†Ø³Ù‚ Ø§Ù„Ø°ÙŠ ÙŠØ±Ø¨Ø· ÙƒÙ„ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø¹Ù„Ù…ÙŠØ© Ù…Ø¹Ø§Ù‹
    """
    def __init__(self):
        # ØªØ­Ù…ÙŠÙ„ Ø¬Ù…ÙŠØ¹ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ù…ØªØ§Ø­Ø©
        self.math_brain = MathematicalValidator()
        self.physics_solver = ExtendedPhysicsSolver()
        self.simulator = PhysicsBasedSimulator()
        self.algebra_processor = AdvancedExponentialAlgebra() if HAS_EXP_ALG else None
        self.validator = EnhancedScientificValidator()
        
        # Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ù…Ø¹Ø±ÙØ© Ø§Ù„Ø¹Ù„Ù…ÙŠØ©
        if HAS_KG:
            self.knowledge_base = KnowledgeNetwork()
            print("   âœ… [Scientific] Knowledge Graph Connected.")
        else:
            self.knowledge_base = {} # Placeholder
            print("   âš ï¸ [Scientific] Knowledge Graph NOT found. Using empty dict.")
    
    def analyze_scientific_design(self, design_text):
        """
        ØªØ­Ù„ÙŠÙ„ Ø´Ø§Ù…Ù„ Ù„Ù„ØªØµÙ…ÙŠÙ… Ø§Ù„Ø¹Ù„Ù…ÙŠ Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø¬Ù…ÙŠØ¹ Ø§Ù„Ø£Ø¯ÙˆØ§Øª
        """
        analysis = {
            "design": design_text,
            "validations": [],
            "calculations": [],
            "issues": [],
            "feasibility_score": 1.0
        }
        
        # Ø§Ù„Ù…Ø±Ø­Ù„Ø© 1: Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„ØªÙ†Ø§Ù‚Ø¶Ø§Øª
        physics_issues = self.validator.validate_physics_proposal(design_text)
        analysis["issues"].extend(physics_issues)
        
        # Ø§Ù„Ù…Ø±Ø­Ù„Ø© 2: Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø§Ù„Ù…Ø¹Ø·ÙŠØ§Øª
        extracted_data = self._extract_scientific_data(design_text)
        
        # Ø§Ù„Ù…Ø±Ø­Ù„Ø© 3: Ø¥Ø¬Ø±Ø§Ø¡ Ø§Ù„Ø­Ø³Ø§Ø¨Ø§Øª
        if extracted_data.get('orbital_params'):
            orbital_results = self.physics_solver.keplers_laws(extracted_data['orbital_params'])
            analysis["calculations"].append({"orbital_mechanics": orbital_results})
        
        if extracted_data.get('energy_params'):
            # Placeholder for energy analysis call
            pass
        
        # Ø§Ù„Ù…Ø±Ø­Ù„Ø© 4: Ø§Ù„Ù…Ø­Ø§ÙƒØ§Ø© (Ø¥Ø°Ø§ ÙƒØ§Ù†Øª Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª ÙƒØ§ÙÙŠØ©)
        simulation_type = self._detect_simulation_type(design_text)
        analysis["simulation_type"] = simulation_type
        
        if simulation_type == "dyson_swarm" and self._has_sufficient_data_for_simulation(extracted_data):
            simulation_results = self.simulator.simulate_dyson_swarm(extracted_data)
            analysis["simulation"] = simulation_results
        elif simulation_type == "fusion":
            simulation_results = self.simulator.simulate_fusion_reactor(extracted_data)
            analysis["simulation"] = simulation_results
        elif simulation_type == "mars_colony":
            simulation_results = self.simulator.simulate_mars_colony(extracted_data)
            analysis["simulation"] = simulation_results
        elif simulation_type == "dark_matter":
            # Use defaults if data missing
            simulation_results = self.simulator.simulate_dark_matter_detection(extracted_data)
            analysis["simulation"] = simulation_results
        elif simulation_type == "entropy":
            simulation_results = self.simulator.simulate_entropy_flow(extracted_data)
            analysis["simulation"] = simulation_results
            
        if "simulation" in analysis and not analysis["simulation"].get('feasibility', True):
            analysis["feasibility_score"] *= 0.5
            analysis["issues"].extend(analysis["simulation"].get('issues', []))
        
        # Ø§Ù„Ù…Ø±Ø­Ù„Ø© 5: ØªÙˆÙ„ÙŠØ¯ Ø¥Ø«Ø¨Ø§Øª Ø±ÙŠØ§Ø¶ÙŠ (Ø¥Ø°Ø§ Ø£Ù…ÙƒÙ†)
        if self.algebra_processor:
            analysis["mathematical_proof"] = self._generate_proof(simulation_type, extracted_data)

        # Ø§Ù„Ù…Ø±Ø­Ù„Ø© 6: ØªÙ‚ÙŠÙŠÙ… Ø§Ù„Ø¬Ø¯ÙˆÙ‰ Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠ
        analysis["feasibility_score"] *= (1 - 0.1 * len(analysis["issues"]))
        analysis["feasibility_score"] = max(0.0, min(1.0, analysis["feasibility_score"]))
        
        # Ø§Ù„Ù…Ø±Ø­Ù„Ø© 7: ØªÙˆÙ„ÙŠØ¯ ØªÙ‚Ø±ÙŠØ± Ù…ÙØµÙ„
        analysis["report"] = self._generate_detailed_report(analysis)
        
        return analysis

    def _detect_simulation_type(self, text):
        text_lower = text.lower()
        if "dark matter" in text_lower or "wimp" in text_lower:
            return "dark_matter"
        if "entropy" in text_lower or "time" in text_lower or "arrow" in text_lower:
            return "entropy"
        if "fusion" in text_lower or "plasma" in text_lower or "reactor" in text_lower or "Ù…ÙØ§Ø¹Ù„" in text_lower:
            return "fusion"
        if "mars" in text_lower or "Ù…Ø±ÙŠØ®" in text_lower:
            return "mars_colony"
        return "dyson_swarm" # Default

    def _generate_proof(self, sim_type, data):
        """ØªÙˆÙ„ÙŠØ¯ Ø¥Ø«Ø¨Ø§Øª Ø±ÙŠØ§Ø¶ÙŠ Ø±Ù…Ø²ÙŠ"""
        proof = []
        if sim_type == "dark_matter":
            proof.append("Theorem: WIMP Detection Probability")
            proof.append("Let R be the event rate, Î¦ be flux, Ïƒ be cross-section, N be targets.")
            proof.append("R = Î¦ Â· Ïƒ Â· N")
            proof.append("Significance Î£ = (R Â· t) / sqrt(B Â· t)")
            proof.append("For Discovery: Î£ > 5")
        elif sim_type == "entropy":
            if HAS_EXP_ALG:
                proof.append("Theorem: Quantum Entanglement Growth (Thermalization)")
                proof.append("Hamiltonian H = -J Î£ Ïƒ_z^i Ïƒ_z^{i+1} - h Î£ Ïƒ_x^i")
                proof.append("Time Evolution: |Ïˆ(t)âŸ© = exp(-iHt) |Ïˆ(0)âŸ©")
                proof.append("Reduced Density Matrix: Ï_A = Tr_B(|Ïˆ(t)âŸ©âŸ¨Ïˆ(t)|)")
                proof.append("Von Neumann Entropy: S_A = -Tr(Ï_A ln Ï_A)")
                proof.append("Result: S_A increases over time due to entanglement (Quantum Thermalization).")
            else:
                proof.append("Theorem: H-Theorem (Boltzmann)")
                proof.append("dS/dt â‰¥ 0 for isolated systems")
                proof.append("S = -k Î£ p_i ln(p_i)")
                proof.append("Limit t->inf: S -> S_max (Equilibrium)")
        else:
            proof.append("Standard Model Verification")
        return "\n".join(proof)

    def _extract_scientific_data(self, text):
        """Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø¹Ù„Ù…ÙŠØ© Ù…Ù† Ø§Ù„Ù†Øµ"""
        data = {}
        
        # Ø§Ù„Ø¨Ø­Ø« Ø¹Ù† Ø£Ø±Ù‚Ø§Ù… ÙˆÙˆØ­Ø¯Ø§Øª (Updated to support scientific notation)
        
        # Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø§Ù„Ù…Ø³Ø§ÙØ§Øª
        distance_pattern = r'(\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*(km|m|AU|ly)'
        distances = re.findall(distance_pattern, text, re.IGNORECASE)
        if distances:
            data['distances'] = self._convert_to_meters(distances)
            # Heuristic: assume the largest distance is orbital radius if not specified
            if data['distances']:
                 data['orbital_params'] = {'semi_major_axis': max(data['distances'])}

        # Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø§Ù„ÙƒØªÙ„
        mass_pattern = r'(\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*(kg|ton|solar mass)'
        masses = re.findall(mass_pattern, text, re.IGNORECASE)
        if masses:
            data['masses'] = self._convert_to_kg(masses)
            # Heuristic: assume largest mass is star mass
            if data['masses']:
                 if 'orbital_params' not in data: data['orbital_params'] = {}
                 data['orbital_params']['star_mass'] = max(data['masses'])
                 data['star_mass'] = max(data['masses'])
        
        # Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø§Ù„Ø·Ø§Ù‚Ø©
        energy_pattern = r'(\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*(W|kW|MW|GW|TW)'
        energies = re.findall(energy_pattern, text, re.IGNORECASE)
        if energies:
            data['energies'] = self._convert_to_watts(energies)
            if data['energies']:
                 data['star_luminosity'] = max(data['energies']) # Assume largest is star luminosity

        # Extract other simulation params if possible (simple heuristics)
        if 'orbital_params' in data and 'semi_major_axis' in data['orbital_params']:
             data['orbital_radius'] = data['orbital_params']['semi_major_axis']
        
        return data

    def _convert_to_meters(self, distances):
        res = []
        for val, unit in distances:
            v = float(val)
            u = unit.lower()
            if u == 'km': v *= 1e3
            elif u == 'au': v *= 1.496e11
            elif u == 'ly': v *= 9.461e15
            res.append(v)
        return res

    def _convert_to_kg(self, masses):
        res = []
        for val, unit in masses:
            v = float(val)
            u = unit.lower()
            if u == 'ton': v *= 1000
            elif u == 'solar mass': v *= 1.989e30
            res.append(v)
        return res

    def _convert_to_watts(self, energies):
        res = []
        for val, unit in energies:
            v = float(val)
            u = unit.lower()
            if u == 'kw': v *= 1e3
            elif u == 'mw': v *= 1e6
            elif u == 'gw': v *= 1e9
            elif u == 'tw': v *= 1e12
            res.append(v)
        return res

    def _has_sufficient_data_for_simulation(self, data):
        # Check if we have enough data
        # We need at least orbital radius and star mass for stability
        # And luminosity for energy
        return 'orbital_radius' in data and 'star_mass' in data and 'star_luminosity' in data


    def _generate_detailed_report(self, analysis):
        return f"Feasibility: {analysis['feasibility_score']:.2f}, Issues: {len(analysis['issues'])}"

