from typing import Dict

class EvolutionTestEngine:
    """
    A simple engine that performs Fibonacci calculation inefficiently.
    Used to test the RecursiveImprover.
    """
    def __init__(self):
        self.name = "EvolutionTestEngine"
        
    def fib(self, n: int) -> int:
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
        
    def process_task(self, payload: Dict[str, int]) -> Dict[str, int]:
        n = payload.get('n', 10)
        return {"fib_result": self.fib(n)}

# Optimized version using memoization for better performance
class ImprovedEvolutionTestEngine(EvolutionTestEngine):
    def __init__(self):
        super().__init__()
        self.memo: Dict[int, int] = {0: 0, 1: 1}

    def fib(self, n: int) -> int:
        if n not in self.memo:
            self.memo[n] = self.fib(n - 1) + self.fib(n - 2)
        return self.memo[n]

# Example usage
if __name__ == "__main__":
    improved_engine = ImprovedEvolutionTestEngine()
    result = improved_engine.process_task({"n": 10})
    print(result)