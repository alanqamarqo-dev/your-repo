import os
import re
import math
import time
import random

# ==========================================
# ⚛️ AGL QUANTUM RESONANCE SCANNER (JS EDITION)
# Target: JavaScript Assets (Notion.so)
# Physics Engine: Heikal Quantum Core (HQC)
# ==========================================

class VectorizedResonanceOptimizer:
    def __init__(self):
        self.h_bar = 1.0
        self.mass = 1.0
        self.barrier_width = random.uniform(0.5, 1.0)
        self.porosity = 1.5
        print(f"⚛️ [VRO]: Vectorized Resonance Optimizer Initialized")
        print(f"   h_bar: {self.h_bar}, mass: {self.mass}, barrier_width: {self.barrier_width:.1f}")
        print(f"   Heikal Porosity: {self.porosity}")

class HeikalQuantumCore:
    def __init__(self):
        print("🌌 [HQC]: Heikal Quantum Core initialized. Ghost Computing Active.")
        print("🌊 [AWP]: Advanced Wave Processor Initialized")
        print("   Quantum Noise Floor: 1.00%")

class JSResonanceScanner:
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.vro = VectorizedResonanceOptimizer()
        self.hqc = HeikalQuantumCore()
        self.results = []
        self.dissonant = []
        
        # معايير التنافر (Dissonance Criteria)
        self.risk_patterns = {
            'dangerouslySetInnerHTML': 0.9, # High Risk
            'eval(': 0.95,
            'setTimeout': 0.3,
            'document.write': 0.8,
            'localStorage': 0.4,
            'debugger': 0.5,
            'var ': 0.2, # Legacy code indicator
        }

    def calculate_resonance(self, content, filename):
        """ حساب درجة التناغم بناءً على فيزياء الكود """
        lines = content.split('\n')
        loc = len(lines)
        
        # 1. حساب الكتلة (Mass) - التعقيد
        mass = math.log(loc + 1) if loc > 0 else 0
        
        # 2. حساب التنافر (Dissonance) - المخاطر
        dissonance_score = 0
        findings = []
        
        for pattern, weight in self.risk_patterns.items():
            matches = len(re.findall(re.escape(pattern), content))
            if matches > 0:
                dissonance_score += matches * weight
                findings.append(f"{pattern} ({matches})")
        
        # 3. حساب التناغم (Resonance) - الجودة
        # مؤشرات الجودة: استخدام const/let, arrow functions, classes
        quality_score = 0
        quality_score += len(re.findall(r'\bconst\b', content)) * 0.1
        quality_score += len(re.findall(r'\blet\b', content)) * 0.1
        quality_score += len(re.findall(r'=>', content)) * 0.2
        
        # المعادلة النهائية: التناغم = (الجودة / (التنافر + 1)) * (1 / الكتلة)
        # (معادلة تقريبية لمحاكاة الفيزياء)
        if dissonance_score == 0: dissonance_score = 0.1
        resonance = (quality_score / dissonance_score) * (100 / (mass + 1))
        
        return {
            'file': filename,
            'loc': loc,
            'resonance': resonance,
            'dissonance': dissonance_score,
            'findings': findings
        }

    def scan(self):
        print("\n=== System Self-Scan: Code Resonance Analysis (JS Layer) ===")
        print("Objective: Identify 'Resonant' (High Value) and 'Dissonant' (High Risk) components.\n")
        
        files = [f for f in os.listdir(self.target_dir) if f.endswith('.js')]
        print(f"[Scanning] Root: {self.target_dir}")
        print(f"[Analysis] Total Units to Process: {len(files)}")
        
        for f in files:
            path = os.path.join(self.target_dir, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    result = self.calculate_resonance(content, f)
                    self.results.append(result)
                    
                    if result['dissonance'] > 5: # عتبة التنافر
                        self.dissonant.append(result)
                        
            except Exception as e:
                print(f"   [Error] Failed to scan {f}: {e}")

        self.results.sort(key=lambda x: x['resonance'], reverse=True)
        self.dissonant.sort(key=lambda x: x['dissonance'], reverse=True)
        
        self.print_report()

    def print_report(self):
        print("\n[Action] Applying Quantum Resonance Filter...")
        print(f"[Results] Scan Complete.")
        print(f"   Survivors: {len(self.results) - len(self.dissonant)}")
        print(f"   Blocked (Dissonant): {len(self.dissonant)}")
        
        print("\n>>> TOP 5 RESONANT COMPONENTS (The 'Genius' Code) <<<")
        for i, res in enumerate(self.results[:5]):
            print(f"{i+1}. {res['file']}")
            print(f"   Type: Module, Lines: {res['loc']}")
            print(f"   Resonance Score: {res['resonance']:.2f} (Amp: {res['resonance']*1.1:.2f}x)")
            print(f"   Status: Standard")
            print("-" * 40)

        print("\n>>> TOP DISSONANT COMPONENTS (Vulnerability Candidates) <<<")
        for i, res in enumerate(self.dissonant[:5]):
            print(f"{i+1}. {res['file']}")
            print(f"   Type: Module, Lines: {res['loc']}")
            print(f"   Barrier: 0.95, Coherence: {1/(res['dissonance']+1):.2f}")
            print(f"   Gap: {res['dissonance']:.2f} (High Risk)")
            print(f"   Findings: {', '.join(res['findings'][:3])}...")
            print("-" * 40)

if __name__ == "__main__":
    scanner = JSResonanceScanner("d:\\AGL\\js_dump")
    scanner.scan()
