
from typing import List

def calculate_fibonacci(n: int) -> int:
    """
    Calculate the n-th Fibonacci number using memoization.
    
    :param n: The position in the Fibonacci sequence.
    :return: The n-th Fibonacci number.
    """
    if n <= 1:
        return n
    memo = [0, 1] + [0] * (n - 1)
    for i in range(2, n + 1):
        memo[i] = memo[i - 1] + memo[i - 2]
    return memo[n]

def process_data(data: List[int]) -> List[int]:
    """
    Process a list of integers by doubling the even numbers.
    
    :param data: A list of integers.
    :return: A new list with even numbers doubled and odd numbers unchanged.
    """
    return [i * 2 if i % 2 == 0 else i for i in data]

if __name__ == "__main__":
    start = time.time()
    print(f"Fib 30: {calculate_fibonacci(30)}")
    print(f"Time: {time.time() - start}")
    
    my_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(f"Processed: {process_data(my_list)}")
