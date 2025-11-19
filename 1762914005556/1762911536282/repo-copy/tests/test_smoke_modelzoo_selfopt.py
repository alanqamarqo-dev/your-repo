from Learning_System import ModelZoo, Self_Optimizer


def test_modelzoo_and_self_optimizer_basic_imports():
    # Import-only smoke: constructing basic objects if available
    try:
        mz = ModelZoo
        assert mz is not None
    except Exception:
        assert False, "ModelZoo import failed"

    # Self_Optimizer may expose a class or functions; exercise None-handling
    try:
        so_mod = Self_Optimizer
        # instantiate if a class named SelfOptimizer exists
        if hasattr(so_mod, 'SelfOptimizer'):
            inst = so_mod.SelfOptimizer(cfg=None) # type: ignore
            assert inst is not None
        else:
            # otherwise ensure module loads
            assert so_mod is not None
    except Exception:
        # allow fallback exceptions but fail if import itself breaks
        assert False, "Self_Optimizer import or basic instantiation failed"
