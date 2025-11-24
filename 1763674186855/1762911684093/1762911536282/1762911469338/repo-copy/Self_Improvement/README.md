Safe Self-Improvement scaffolding

Files added:
- safe_self_mod.py: main SafeSelfModificationSystem with sandbox, validator, rollback and monitor.
- algorithm_optimizer.py: AlgorithmSelfOptimizer scaffold.
- memory_restructurer.py: MemorySelfRestructurer scaffold.
- rollback.py: AutomaticRollbackSystem scaffold.

These modules are intentionally conservative: all "apply" operations are simulated/dry-run by default.
To integrate with the live system, replace the placeholders with project-specific logic and add approval gates.
