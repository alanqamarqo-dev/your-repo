"""Generate numbers and compute mean/std deviation without numpy."""

import random


def generate_random_integers(count: int, min_val: int, max_val: int) -> list[int]:
    """Return a list of `count` random integers between `min_val` and `max_val` inclusive."""

    return [random.randint(min_val, max_val) for _ in range(count)]


def calculate_mean(numbers: list[int]) -> float:
    """Compute the arithmetic mean of a non-empty list."""

    if not numbers:
        raise ValueError("numbers list must not be empty")
    return sum(numbers) / len(numbers)


def calculate_standard_deviation(numbers: list[int], mean_value: float) -> float:
    """Compute the population standard deviation given the mean."""

    if not numbers:
        raise ValueError("numbers list must not be empty")
    variance = sum((x - mean_value) ** 2 for x in numbers) / len(numbers)
    return variance ** 0.5


if __name__ == "__main__":
    random_integers = generate_random_integers(100, 1, 1000)
    mean_value = calculate_mean(random_integers)
    std_deviation = calculate_standard_deviation(random_integers, mean_value)
    print("Generated 100 integers between 1 and 1000.")
    print(f"Mean: {mean_value:.4f}")
    print(f"Standard Deviation: {std_deviation:.4f}")