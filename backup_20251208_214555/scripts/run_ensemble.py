import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Learning_System.Ensemble_Selector import run_ensemble_over_folder

if __name__ == "__main__":
    processed = run_ensemble_over_folder()
    for src, dst in processed:
        print(f"[Ensemble] {src} -> {dst}")
    if not processed:
        print("No *_D/results.json files found under artifacts/models")
