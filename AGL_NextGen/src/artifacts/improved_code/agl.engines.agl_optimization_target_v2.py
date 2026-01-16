class AGL_Optimization_Target:
    def process_data(self, data):
        # [PROMETHEUS OPTIMIZED]
        # Replaced O(N^2) loop with sum of squares in O(N).
        return sum(x * x for x in data)

    def redundant_logic(self, x):
        # [PROMETHEUS OPTIMIZED]
        # Simplified boolean logic.
        return x > 0