
import sys
import os
import json

# Add repo-copy to path
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(current_dir, '..', 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

try:
    from Learning_System.Self_Engineer import SelfEngineer
    from Core_Engines.Model_Structure_Searcher import StructureCandidate
except ImportError as e:
    print(f"❌ Failed to import SelfEngineer modules: {e}")
    sys.exit(1)

def test_self_engineering_cycle():
    print("\n🧬 === Starting Self-Engineering Simulation === 🧬")
    
    # 1. Initialize Self-Engineer
    print("\n1️⃣  Initializing Self-Engineer...")
    engineer = SelfEngineer(cfg={'promotion': {'min_rmse_improvement_pct': 0.1}})
    
    # 2. Simulate a problem (Diagnosis Phase)
    print("\n2️⃣  Diagnosing System State...")
    # Simulate a report saying the current model is performing poorly on 'predict_power'
    models_report = {
        'task': 'predict_power',
        'current_rmse': 5.0,
        'status': 'underperforming'
    }
    data_profile = {
        'inputs': ['voltage', 'current'],
        'output': 'power',
        'ranges': {'voltage': [0, 10], 'current': [0, 5]}
    }
    
    diagnosis = engineer.diagnose(models_report, data_profile)
    print(f"   🔍 Diagnosis Result: {json.dumps(diagnosis, indent=2, ensure_ascii=False)}")
    
    # 3. Propose new structures (Evolution Phase)
    print("\n3️⃣  Proposing New Structures (Evolution)...")
    task = diagnosis.get('suggested_task', 'predict_power')
    constraints = diagnosis.get('constraints', {})
    
    candidates = engineer.propose(task, data_profile, constraints, budget=3)
    
    print(f"   💡 Generated {len(candidates)} candidates:")
    for i, cand in enumerate(candidates):
        print(f"      [{i+1}] ID: {cand.id} | Expr: {cand.expr} | Complexity: {cand.complexity}")

    # 4. Fit and Score (Selection Phase)
    print("\n4️⃣  Fitting and Scoring Candidates (Natural Selection)...")
    # Mock training data (not used in the stub, but required by signature)
    train_data = []
    val_data = []
    
    best_score = float('inf')
    best_candidate = None
    
    for cand in candidates:
        # The stub fit_and_score returns a dict with metrics
        result = engineer.fit_and_score(cand, train_data, val_data)
        
        # In the stub, rmse is calculated based on complexity (lower complexity -> higher rmse in the stub logic? let's check)
        # Stub logic: rmse = max(0.01, 1.0 / (1.0 + complexity)) -> Higher complexity = Lower RMSE (better)
        
        score = result.get('metrics', {}).get('rmse', 999)
        print(f"      🧪 Testing {cand.id}: RMSE = {score:.4f} (Complexity: {cand.complexity})")
        
        if score < best_score:
            best_score = score
            best_candidate = cand

    # 5. Conclusion
    print("\n5️⃣  Evolution Result:")
    if best_candidate:
        print(f"   🏆 Best Candidate: {best_candidate.id}")
        print(f"   📝 Expression: {best_candidate.expr}")
        print(f"   📉 Improvement: Current RMSE {models_report['current_rmse']} -> New RMSE {best_score:.4f}")
        
        if best_score < models_report['current_rmse']:
            print("   ✅ SUCCESS: Self-improvement achieved!")
        else:
            print("   ⚠️  No improvement found.")
    else:
        print("   ❌ No valid candidates found.")

if __name__ == "__main__":
    test_self_engineering_cycle()
