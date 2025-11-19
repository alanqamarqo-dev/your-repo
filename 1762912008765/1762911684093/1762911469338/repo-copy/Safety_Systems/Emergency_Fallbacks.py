"""Fallback emergency safety helpers used when optional emergency experts are missing."""


class EmergencyDoctorFallback:
    def __init__(self):
        pass

    def assess(self, situation: dict) -> dict:
        return {"recommendation": "SAFE_ROLLBACK", "notes": "fallback-assessment"}


class EmergencyIntegrationFallback:
    def __init__(self, registry=None):
        self.registry = registry

    def integrate(self, data: dict) -> dict:
        return {"status": "integrated_fallback"}
