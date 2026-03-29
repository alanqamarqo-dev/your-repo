---
description: "Train and optimize risk scoring weights using the weight optimizer"
tools: [read, edit, search, execute]
argument-hint: "Training task (e.g. initial training, retrain with new data, calibrate)"
---
Run weight training for the risk scoring system.

Steps:
1. Check current weights in `artifacts/risk_weights.json`
2. Run benchmark suite on training contracts
3. Extract training features (S_f, S_h, S_p, E) and labels (y)
4. Balance classes with sample_weights
5. Run 5-fold cross-validation
6. If accuracy > 0.75, train on full data and save weights
7. Check calibration (ECE < 0.10)
8. Report: old vs new weights, accuracy, ECE
