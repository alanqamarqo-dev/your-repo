import sys
sys.path.insert(0, '.')
from Self_Improvement.safe_self_mod import SafeSelfModificationSystem
from Self_Improvement.algorithm_optimizer import AlgorithmSelfOptimizer
from Self_Improvement.memory_restructurer import MemorySelfRestructurer
from Self_Improvement.rollback import AutomaticRollbackSystem

ssm = SafeSelfModificationSystem()
res = ssm.safe_self_modify({'steps': [{'op':'noop'}]})
print('SSM result:', res)
opt = AlgorithmSelfOptimizer()
opt.optimize_reasoning_algorithms()
mr = MemorySelfRestructurer()
mr.restructure_memory()
rb = AutomaticRollbackSystem()
print('snapshot created:', rb.create_snapshot())
