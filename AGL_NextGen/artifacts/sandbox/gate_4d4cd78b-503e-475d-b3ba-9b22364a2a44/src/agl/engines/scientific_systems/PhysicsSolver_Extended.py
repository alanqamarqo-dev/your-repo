# Scientific_Systems/PhysicsSolver_Extended.py
import numpy as np

class ExtendedPhysicsSolver:
    def __init__(self):
        self.constants = {
            'G': 6.67430e-11,      # ثابت الجذب العام
            'c': 299792458,        # سرعة الضوء
            'k': 1.380649e-23,     # ثابت بولتزمان
            'sigma': 5.670374419e-8, # ثابت ستيفان-بولتزمان
            'h': 6.62607015e-34,   # ثابت بلانك
            'mu0': 1.25663706e-6   # نفاذية الفراغ المغناطيسية
        }
    
    def keplers_laws(self, orbital_params):
        """تطبيق قوانين كبلر للمدارات"""
        # القانون الأول: المدارات إهليلجية
        # القانون الثاني: مساحات متساوية في أزمنة متساوية
        # القانون الثالث: T² ∝ a³
        
        semi_major_axis = orbital_params.get('semi_major_axis')
        star_mass = orbital_params.get('star_mass')
        
        if semi_major_axis and star_mass:
            G = self.constants['G']
            period = 2 * np.pi * np.sqrt(semi_major_axis**3 / (G * star_mass))
            return {"orbital_period": period}
        return {}
    
    def thermodynamics_check(self, system_params):
        """فحص قوانين الديناميكا الحرارية"""
        # القانون الصفري: التوازن الحراري
        # القانون الأول: حفظ الطاقة
        # القانون الثاني: الإنتروبيا لا تنقص
        # القانون الثالث: الإنتروبيا عند الصفر المطلق
        
        energy_in = system_params.get('energy_input')
        energy_out = system_params.get('energy_output')
        work_done = system_params.get('work_done')
        
        # القانون الأول: ΔU = Q - W
        if all(v is not None for v in [energy_in, energy_out, work_done]):
            delta_u = energy_in - energy_out - work_done
            if abs(delta_u) > 1e-6:  # خطأ عددي صغير مسموح
                return False, f"ينتهي قانون حفظ الطاقة: ΔU = {delta_u:.2f} J"
        
        return True, "يلبي قوانين الديناميكا الحرارية"
    
    def relativity_check(self, velocities, distances):
        """فحص امتثال للنسبية"""
        c = self.constants['c']
        
        for v in velocities:
            if v >= c:
                return False, f"السرعة {v} تساوي أو تتجاوز سرعة الضوء"
        
        # تأثيرات النسبية العامة للكتل الكبيرة
        large_masses = [m for m in distances.get('masses', []) if m > 1e30]
        if large_masses and distances.get('proximity', float('inf')) < 1e6:
            return False, "اقتراب شديد من كتلة هائلة - تأثيرات نسبية عامة قوية"
        
        return True, "يلبي شروط النسبية"

    def fusion_check(self, plasma_params):
        """فحص شروط الاندماج النووي (Lawson Criterion & Beta Limit)"""
        # Lawson Criterion for D-T: n * T * tau >= 3e21 keV s m^-3
        # Note: T is usually in keV. If provided in Kelvin, convert. 1 keV ~ 1.16e7 K
        
        n = plasma_params.get('density', 0) # m^-3
        T_kelvin = plasma_params.get('temperature', 0) # Kelvin
        tau = plasma_params.get('confinement_time', 0) # seconds
        B = plasma_params.get('magnetic_field', 0) # Tesla
        
        # Convert T to keV
        T_keV = T_kelvin / 1.16e7
        
        # 1. Lawson Criterion
        lawson_product = n * T_keV * tau
        lawson_threshold = 3e21 # Approximate for ignition
        
        ignition = lawson_product >= lawson_threshold
        
        # 2. Beta Limit (Stability)
        # P_plasma = n * k * T
        # P_mag = B^2 / (2 * mu0)
        # Beta = P_plasma / P_mag
        
        k = self.constants['k']
        mu0 = self.constants['mu0']
        
        p_plasma = n * k * T_kelvin
        p_mag = (B**2) / (2 * mu0) if B > 0 else 0
        
        beta = p_plasma / p_mag if p_mag > 0 else float('inf')
        
        # Typical Tokamak limit ~ 5% (0.05)
        stable_beta = beta < 0.05
        
        return {
            "ignition": ignition,
            "lawson_value": lawson_product,
            "beta": beta,
            "stable_plasma": stable_beta,
            "p_plasma": p_plasma,
            "p_mag": p_mag
        }
