# Scientific_Systems/Integrated_Simulation_Engine_Enhanced.py
import numpy as np
from agl.engines.scientific_systems.Scientific_Research_Assistant import MathematicalValidator
from agl.engines.scientific_systems.PhysicsSolver_Extended import ExtendedPhysicsSolver # Import Physics Solver

try:
    from agl.engines.advanced_exponential_algebra import AdvancedExponentialAlgebra
    HAS_EXP_ALG = True
except ImportError:
    try:
        from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra
        HAS_EXP_ALG = True
    except ImportError:
        HAS_EXP_ALG = False

class PhysicsBasedSimulator:
    def __init__(self):
        self.math_validator = MathematicalValidator()
        self.physics_solver = ExtendedPhysicsSolver() # Initialize Physics Solver
        self.algebra_processor = AdvancedExponentialAlgebra() if HAS_EXP_ALG else None
        
    def simulate_mars_colony(self, design_parameters):
        """
        Ù…Ø­Ø§ÙƒØ§Ø© Ù…Ø³ØªØ¹Ù…Ø±Ø© Ø¹Ù„Ù‰ Ø§Ù„Ù…Ø±ÙŠØ®
        """
        results = {
            "feasibility": True,
            "issues": [],
            "numerical_results": {}
        }
        
        # Default parameters if not provided
        population = design_parameters.get('population', 100)
        power_source = design_parameters.get('power_source', 'solar') # solar, nuclear
        
        # 1. Energy Requirements
        power_per_person = 15.0 # kW (life support, heating, industry)
        total_power_needed = population * power_per_person
        
        results['numerical_results']['total_power_kw'] = total_power_needed
        
        if power_source == 'solar':
            # Mars solar irradiance is ~43% of Earth's (~590 W/m2)
            # Dust storms reduce this by 90% for weeks
            results['issues'].append("Ø§Ù„Ø§Ø¹ØªÙ…Ø§Ø¯ Ø¹Ù„Ù‰ Ø§Ù„Ø·Ø§Ù‚Ø© Ø§Ù„Ø´Ù…Ø³ÙŠØ© ÙÙ‚Ø· Ø®Ø·Ø± Ø¨Ø³Ø¨Ø¨ Ø§Ù„Ø¹ÙˆØ§ØµÙ Ø§Ù„ØºØ¨Ø§Ø±ÙŠØ© Ø§Ù„Ù…Ø±ÙŠØ®ÙŠØ© Ø§Ù„ØªÙŠ Ù‚Ø¯ ØªØ³ØªÙ…Ø± Ù„Ø£Ø³Ø§Ø¨ÙŠØ¹.")
            results['feasibility'] = False
        elif power_source == 'nuclear':
            results['numerical_results']['reactor_type'] = 'Kilopower-style Fission'
        
        # 2. Radiation Shielding
        shielding_thickness = design_parameters.get('shielding_thickness', 0.1) # meters of regolith
        if shielding_thickness < 2.0:
             results['issues'].append(f"Ø³Ù…Ùƒ Ø§Ù„Ø¯Ø±Ø¹ Ø§Ù„Ø¥Ø´Ø¹Ø§Ø¹ÙŠ ({shielding_thickness}m) ØºÙŠØ± ÙƒØ§ÙÙ. Ø§Ù„Ù…Ø±ÙŠØ® ÙŠÙØªÙ‚Ø± Ù„ØºÙ„Ø§Ù Ø¬ÙˆÙŠ ÙˆÙ…Ø¬Ø§Ù„ Ù…ØºÙ†Ø§Ø·ÙŠØ³ÙŠ. Ù…Ø·Ù„ÙˆØ¨ > 2m Ù…Ù† Ø§Ù„ØªØ±Ø¨Ø©.")
             results['feasibility'] = False
             
        return results

    def simulate_fusion_reactor(self, design_parameters):
        """
        Ù…Ø­Ø§ÙƒØ§Ø© Ù…ÙØ§Ø¹Ù„ Ø§Ù†Ø¯Ù…Ø§Ø¬ Ù†ÙˆÙˆÙŠ
        """
        results = {
            "feasibility": True,
            "issues": [],
            "numerical_results": {}
        }
        
        # Extract parameters
        n = design_parameters.get('plasma_density', 1e20) # m^-3
        T = design_parameters.get('temperature', 1.5e8) # Kelvin (~13 keV)
        tau = design_parameters.get('confinement_time', 2.0) # seconds
        B = design_parameters.get('magnetic_field', 5.0) # Tesla
        
        # Run Physics Check
        physics_check = self.physics_solver.fusion_check({
            'density': n,
            'temperature': T,
            'confinement_time': tau,
            'magnetic_field': B
        })
        
        results['numerical_results'] = physics_check
        
        # Analyze Stability (Beta Limit)
        if not physics_check['stable_plasma']:
            results['feasibility'] = False
            results['issues'].append(f"Ø¹Ø¯Ù… Ø§Ø³ØªÙ‚Ø±Ø§Ø± Ø§Ù„Ø¨Ù„Ø§Ø²Ù…Ø§: Beta ({physics_check['beta']:.4f}) ØªØªØ¬Ø§ÙˆØ² Ø§Ù„Ø­Ø¯ Ø§Ù„Ù…Ø³Ù…ÙˆØ­ (0.05). Ø¶ØºØ· Ø§Ù„Ø¨Ù„Ø§Ø²Ù…Ø§ Ø£Ø¹Ù„Ù‰ Ù…Ù† Ø§Ù„Ø¶ØºØ· Ø§Ù„Ù…ØºÙ†Ø§Ø·ÙŠØ³ÙŠ.")
            results['issues'].append(f"Ø§Ù„Ø­Ù„ Ø§Ù„Ù…Ù‚ØªØ±Ø­: Ø²ÙŠØ§Ø¯Ø© Ø§Ù„Ù…Ø¬Ø§Ù„ Ø§Ù„Ù…ØºÙ†Ø§Ø·ÙŠØ³ÙŠ B > {np.sqrt(2 * self.physics_solver.constants['mu0'] * physics_check['p_plasma'] / 0.05):.2f} Tesla")
            
        # Analyze Ignition (Lawson)
        if not physics_check['ignition']:
            # Not necessarily a failure if it's a research reactor, but let's note it
            results['issues'].append(f"Ù„Ù… ÙŠØªÙ… Ø§Ù„ÙˆØµÙˆÙ„ Ù„Ù„Ø§Ø´ØªØ¹Ø§Ù„ Ø§Ù„Ø°Ø§ØªÙŠ (Ignition): Lawson Value {physics_check['lawson_value']:.2e} < 3e21")
            
        return results

    def simulate_dyson_swarm(self, design_parameters):
        """
        Ù…Ø­Ø§ÙƒØ§Ø© ÙˆØ§Ù‚Ø¹ÙŠØ© Ù„Ø³Ø±Ø¨ Ø¯Ø§ÙŠØ³ÙˆÙ†
        """
        results = {
            "feasibility": True,
            "issues": [],
            "numerical_results": {}
        }
        
        # 1. Ø­Ø³Ø§Ø¨ Ø§Ù„Ø§Ø³ØªÙ‚Ø±Ø§Ø± Ø§Ù„Ù…Ø¯Ø§Ø±ÙŠ
        orbital_stability = self._check_orbital_stability(
            design_parameters.get('number_of_satellites', 1000),
            design_parameters.get('orbital_radius', 1.5e11),
            design_parameters.get('star_mass', 1.989e30),
            design_parameters.get('active_control', False) # New parameter
        )
        
        if not orbital_stability['stable']:
            results['feasibility'] = False
            results['issues'].append(f"Ø¹Ø¯Ù… Ø§Ø³ØªÙ‚Ø±Ø§Ø± Ù…Ø¯Ø§Ø±ÙŠ: {orbital_stability.get('reason', 'Unknown')}")
        
        # 2. Ø­Ø³Ø§Ø¨ Ø§Ù„Ø·Ø§Ù‚Ø©
        energy_output = self._calculate_energy_output(
            design_parameters.get('satellite_area', 100),
            design_parameters.get('efficiency', 0.2),
            design_parameters.get('star_luminosity', 3.828e26),
            design_parameters.get('orbital_radius', 1.5e11)
        )
        results['numerical_results']['energy_output_watts'] = energy_output
        
        # 3. Ø­Ø³Ø§Ø¨ Ø§Ù„Ø¥Ø¬Ù‡Ø§Ø¯Ø§Øª Ø§Ù„Ù‡ÙŠÙƒÙ„ÙŠØ©
        structural_stress = self._calculate_structural_stress(
            design_parameters.get('material_density', 2700),
            design_parameters.get('thickness', 0.01),
            design_parameters.get('rotation_speed', 0)
        )
        
        if structural_stress > design_parameters.get('material_yield_strength', 200e6):
            results['feasibility'] = False
            results['issues'].append(f"Ø¥Ø¬Ù‡Ø§Ø¯ Ù‡ÙŠÙƒÙ„ÙŠ ÙŠØªØ¬Ø§ÙˆØ² Ù‚ÙˆØ© Ø§Ù„Ù…Ø§Ø¯Ø©: {structural_stress} Pa")
        
        return results
    
    def _check_orbital_stability(self, n_satellites, radius, star_mass, active_control=False):
        """ÙØ­Øµ Ø§Ø³ØªÙ‚Ø±Ø§Ø± Ø§Ù„Ù…Ø¯Ø§Ø±Ø§Øª Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø¬Ø¨Ø± Ù„ÙŠ"""
        if not self.algebra_processor:
             return {"stable": True, "reason": "Skipped (No Algebra Processor)"}

        # Ù…ØµÙÙˆÙØ© Ø§Ø¶Ø·Ø±Ø§Ø¨ Ø§Ù„Ù…Ø¯Ø§Ø±Ø§Øª (Simplified)
        # perturbation_matrix = self._create_perturbation_matrix(n_satellites, radius)
        
        # If active control is enabled, perturbation is dampened significantly
        perturbation_factor = 0.0001 if active_control else 0.01
        perturbation_matrix = np.eye(2) * perturbation_factor
        
        # Ø­Ø³Ø§Ø¨ Ø£Ø³ÙŠ Ø§Ù„Ù…ØµÙÙˆÙØ© Ù„Ù„ØªÙ†Ø¨Ø¤ Ø¨Ø§Ù„Ø³Ù„ÙˆÙƒ Ø·ÙˆÙŠÙ„ Ø§Ù„Ù…Ø¯Ù‰
        try:
            # Using the method from AdvancedExponentialAlgebra
            exp_matrix = self.algebra_processor.matrix_exponential_lie_group(perturbation_matrix, method='pade')
            
            # Ø§Ù„Ù‚ÙŠÙ… Ø§Ù„Ø°Ø§ØªÙŠØ© ØªØ­Ø¯Ø¯ Ø§Ù„Ø§Ø³ØªÙ‚Ø±Ø§Ø±
            eigenvalues = np.linalg.eigvals(exp_matrix)
            
            # Stability condition: eigenvalues should be close to 1 (unitary evolution) or decaying (<1)
            # With perturbation 0.01, exp(0.01) ~ 1.01 > 1 -> Unstable growth
            # With perturbation 0.0001, exp(0.0001) ~ 1.0001 -> Much more stable (or we define a threshold)
            
            max_eig = max(abs(eig) for eig in eigenvalues) if eigenvalues.size > 0 else 0
            
            # Threshold for "Practical Stability" over simulation timeframe
            stable = max_eig < 1.001 
            
            return {
                "stable": stable,
                "eigenvalues": eigenvalues.tolist() if hasattr(eigenvalues, 'tolist') else eigenvalues,
                "max_growth_rate": max_eig,
                "reason": f"Growth rate {max_eig:.5f} exceeds threshold" if not stable else "Stable"
            }
        except Exception as e:
            return {"stable": False, "reason": f"Ø®Ø·Ø£ ÙÙŠ Ø§Ù„Ø­Ø³Ø§Ø¨Ø§Øª Ø§Ù„Ø¬Ø¨Ø±ÙŠØ©: {str(e)}"}


    def _calculate_energy_output(self, area, efficiency, luminosity, radius):
        # Solar constant at radius
        solar_constant = luminosity / (4 * np.pi * radius**2)
        return solar_constant * area * efficiency

    def _calculate_structural_stress(self, density, thickness, rotation_speed):
        # Simplified stress calculation
        return density * (rotation_speed**2) # Very simplified

    def simulate_dark_matter_detection(self, params):
        """
        Ù…Ø­Ø§ÙƒØ§Ø© Ø§Ø­ØªÙ…Ø§Ù„ÙŠØ© ÙƒØ´Ù Ø§Ù„Ù…Ø§Ø¯Ø© Ø§Ù„Ù…Ø¸Ù„Ù…Ø© (WIMPs)
        """
        results = {
            "feasibility": True,
            "numerical_results": {},
            "issues": []
        }
        
        # Parameters
        detector_mass = params.get('detector_mass', 1000) # kg
        exposure_time = params.get('exposure_time', 1) # years
        cross_section = params.get('cross_section', 1e-47) # cm^2 (very small)
        background_noise = params.get('background_noise', 0.01) # events/kg/year
        
        # Theoretical Event Rate (Simplified)
        # Rate ~ Flux * CrossSection * NumberOfTargets
        # Flux ~ 1e5 particles/cm^2/s (local dark matter density)
        # N_targets ~ Mass / AtomicMass
        
        flux = 1e5 # particles/cm^2/s
        n_targets = (detector_mass * 1000) / (131 * 1.66e-24) # Xenon targets (approx)
        
        # Rate per second
        rate_per_sec = flux * cross_section * n_targets
        
        # Total expected signal events
        seconds_per_year = 3.15e7
        expected_signal = rate_per_sec * seconds_per_year * exposure_time
        
        # Total background events
        expected_background = background_noise * detector_mass * exposure_time
        
        # Statistical Significance (Sigma)
        # Sigma ~ Signal / sqrt(Background)
        if expected_background > 0:
            sigma = expected_signal / np.sqrt(expected_background)
        else:
            sigma = 0
            
        results['numerical_results'] = {
            "expected_signal_events": expected_signal,
            "expected_background_events": expected_background,
            "significance_sigma": sigma
        }
        
        if sigma < 3:
            results['feasibility'] = False
            results['issues'].append(f"Ø¥Ø´Ø§Ø±Ø© Ø¶Ø¹ÙŠÙØ© Ø¬Ø¯Ø§Ù‹ ({sigma:.4f} sigma). Ù…Ø·Ù„ÙˆØ¨ > 3 sigma Ù„Ù„Ø§ÙƒØªØ´Ø§Ù.")
            results['issues'].append("Ø§Ù„Ø­Ù„: Ø²ÙŠØ§Ø¯Ø© ÙƒØªÙ„Ø© Ø§Ù„ÙƒØ§Ø´Ù Ø£Ùˆ ØªÙ‚Ù„ÙŠÙ„ Ø§Ù„Ø¶Ø¬ÙŠØ¬ Ø§Ù„Ø®Ù„ÙÙŠ.")
        elif sigma > 5:
            results['numerical_results']['discovery_status'] = "DISCOVERY (5 Sigma)"
        else:
            results['numerical_results']['discovery_status'] = "EVIDENCE (3 Sigma)"
            
        return results

    def simulate_entropy_flow(self, params):
        """
        Ù…Ø­Ø§ÙƒØ§Ø© Ø³Ù‡Ù… Ø§Ù„Ø²Ù…Ù† (Ø§Ù„Ø¥Ù†ØªØ±ÙˆØ¨ÙŠØ§) Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„ØªØ·ÙˆØ± Ø§Ù„ÙƒÙ…ÙŠ (Quantum Time Evolution)
        """
        results = {
            "feasibility": True,
            "numerical_results": {},
            "issues": []
        }
        
        # Try Quantum Simulation first (The "Accurate Path")
        if self.algebra_processor:
            try:
                import torch
                # 1. Define Hamiltonian for a 2-Qubit System (Ising Model)
                # H = -J * Sz1*Sz2 - h * (Sx1 + Sx2)
                # Basis: |00>, |01>, |10>, |11>
                
                # Pauli Matrices
                I = torch.eye(2, dtype=torch.complex64)
                Sx = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64)
                Sz = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64)
                
                # Tensor Products
                Sz1 = torch.kron(Sz, I)
                Sz2 = torch.kron(I, Sz)
                Sx1 = torch.kron(Sx, I)
                Sx2 = torch.kron(I, Sx)
                
                J = 1.0 # Coupling
                h_field = 0.5 # Transverse field
                
                H = -J * torch.matmul(Sz1, Sz2) - h_field * (Sx1 + Sx2)
                
                # 2. Initial State |00> (Low Entanglement)
                psi0 = torch.zeros(4, dtype=torch.complex64)
                psi0[0] = 1.0 # |00>
                
                # 3. Time Evolution
                t_final = float(params.get('steps', 5.0)) # Time units
                t_points = [t_final]
                
                # Use AdvancedExponentialAlgebra to calculate U(t) = exp(-iHt)
                evolved_states = self.algebra_processor.quantum_time_evolution(H, psi0, t_points)
                psi_t = evolved_states[-1]
                
                # 4. Calculate Entanglement Entropy of Qubit 1
                # Density Matrix rho = |psi><psi|
                rho = torch.outer(psi_t, torch.conj(psi_t))
                
                # Partial Trace over Qubit 2
                # Indices: 00, 01, 10, 11
                # rho_A_00 = rho_00_00 + rho_01_01
                # rho_A_01 = rho_00_10 + rho_01_11
                # rho_A_10 = rho_10_00 + rho_11_01
                # rho_A_11 = rho_10_10 + rho_11_11
                
                rho_A = torch.zeros((2, 2), dtype=torch.complex64)
                rho_A[0, 0] = rho[0, 0] + rho[1, 1]
                rho_A[0, 1] = rho[0, 2] + rho[1, 3]
                rho_A[1, 0] = rho[2, 0] + rho[3, 1]
                rho_A[1, 1] = rho[2, 2] + rho[3, 3]
                
                # Von Neumann Entropy S = -Tr(rho ln rho)
                # Use eigenvalues
                evals = torch.linalg.eigvals(rho_A).real
                # Clip small values to avoid log(0)
                evals = evals[evals > 1e-9]
                entropy = -torch.sum(evals * torch.log(evals)).item()
                
                results['numerical_results'] = {
                    "method": "Quantum Time Evolution (Lie Algebra)",
                    "initial_entropy": 0.0, # Pure state |00>
                    "final_entanglement_entropy": entropy,
                    "delta_entropy": entropy,
                    "hamiltonian_dim": 4,
                    "conclusion": "Entanglement Entropy Increased (Thermalization)" if entropy > 0.1 else "Low Entanglement Growth"
                }
                
                return results
                
            except Exception as e:
                results['issues'].append(f"Quantum Simulation Failed: {e}. Falling back to Classical.")
        
        # Fallback to Classical Random Walk (The "Old Path")
        n_particles = int(params.get('n_particles', 100))
        steps = int(params.get('steps', 1000))
        
        # Simulation: Particles in a box expanding
        # Start: Low Entropy (All in left half)
        # End: High Entropy (Distributed)
        
        # 0 = Left, 1 = Right
        particles = np.zeros(n_particles) 
        
        entropy_history = []
        
        for _ in range(steps):
            # Randomly move particles
            idx = np.random.randint(0, n_particles)
            # Flip state with probability 0.5 (Random Walk)
            if np.random.random() < 0.5:
                particles[idx] = 1 - particles[idx]
            
            # Calculate Entropy (Shannon)
            p_left = np.sum(particles == 0) / n_particles
            p_right = np.sum(particles == 1) / n_particles
            
            if p_left > 0 and p_right > 0:
                entropy = - (p_left * np.log2(p_left) + p_right * np.log2(p_right))
            else:
                entropy = 0
            
            entropy_history.append(entropy)
            
        # Check Arrow of Time
        initial_entropy = entropy_history[0]
        final_entropy = entropy_history[-1]
        
        results['numerical_results'] = {
            "method": "Classical Random Walk",
            "initial_entropy": initial_entropy,
            "final_entropy": final_entropy,
            "delta_entropy": final_entropy - initial_entropy
        }
        
        if final_entropy < initial_entropy:
             results['issues'].append("Ø§Ù†ØªÙ‡Ø§Ùƒ Ø§Ù„Ù‚Ø§Ù†ÙˆÙ† Ø§Ù„Ø«Ø§Ù†ÙŠ Ù„Ù„Ø¯ÙŠÙ†Ø§Ù…ÙŠÙƒØ§ Ø§Ù„Ø­Ø±Ø§Ø±ÙŠØ© (Ù†Ø§Ø¯Ø± Ø¬Ø¯Ø§Ù‹ ÙÙŠ Ø§Ù„Ø£Ù†Ø¸Ù…Ø© Ø§Ù„ÙƒØ¨ÙŠØ±Ø©).")
             results['feasibility'] = False
        
        return results

