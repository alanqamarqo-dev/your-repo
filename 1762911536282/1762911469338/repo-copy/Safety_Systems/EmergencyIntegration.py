from Safety_Systems.EmergencyDoctor import EmergencyDoctor
from typing import Dict, Any


class EmergencyIntegration:
    def __init__(self, orchestrator=None):
        self.orch = orchestrator
        self._doctor = EmergencyDoctor()

    def initialize_emergency_system(self):
        # placeholder for future initialization (e.g., register default policies)
        return True

    def register_temp_container(self, container_id: str, directory: str) -> Dict[str, Any]:
        return self._doctor.create_isolated_container(container_id, purpose="temp")

    def handle_emergency_task(self, container_id: str, code: str, task_data: Dict = None) -> Dict[str, Any]: # type: ignore
        # ensure container exists
        if container_id not in self._doctor.active_containers:
            self._doctor.create_isolated_container(container_id)
        return self._doctor.execute_in_emergency_container(container_id, code, task_data or {})

    def emergency_cleanup_all(self):
        return self._doctor.emergency_cleanup_all()


# Backwards-compatible singleton and functional API
_integration = EmergencyIntegration()


def register_temp_container(container_id: str, directory: str) -> Dict[str, Any]:
    return _integration.register_temp_container(container_id, directory)


def run_emergency_code(container_id: str, code: str, task_data: Dict = None) -> Dict[str, Any]: # type: ignore
    return _integration.handle_emergency_task(container_id, code, task_data or {})
