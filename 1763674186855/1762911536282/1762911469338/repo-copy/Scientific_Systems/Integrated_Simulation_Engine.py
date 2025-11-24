class IntegratedSimulationEngine:
	"""Lightweight simulation engine stub used by the demo."""
	def __init__(self):
		self.simulation_time = 0.0

	def step(self, dt: float = 0.01):
		self.simulation_time += dt
		return {'time': self.simulation_time}

	def run(self, steps: int = 1, dt: float = 0.01):
		results = []
		for _ in range(steps):
			results.append(self.step(dt))
		return results
