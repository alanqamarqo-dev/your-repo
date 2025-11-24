"""Rollback mechanism shim for compatibility with AGL imports."""
try:
    from Safety_Control.Safe_Rollback_System import SafeRollbackSystem as RollbackMechanism  # type: ignore
except Exception:
    class RollbackMechanism:
        def __init__(self):
            self._checkpoints = []

        def record(self, state):
            self._checkpoints.append(state)

        def rollback(self):
            return self._checkpoints.pop() if self._checkpoints else None

