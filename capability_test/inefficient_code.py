import time

def slow_fib(n):
    if n <= 1: return n
    return slow_fib(n-1) + slow_fib(n-2)

def run_calculation():
    start = time.time()
    print(f"Fib(30) = {slow_fib(30)}")
    print(f"Time taken: {time.time() - start:.4f}s")
