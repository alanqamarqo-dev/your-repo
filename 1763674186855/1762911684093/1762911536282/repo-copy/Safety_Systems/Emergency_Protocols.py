"""Emergency protocols shim for compatibility with AGL imports."""
class EmergencyProtocols:
    def activate_emergency_mode(self, mode='shutdown'):
        print(f"[EmergencyProtocols] Activated emergency mode: {mode}")

