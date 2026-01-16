
def find_operating_law(observations):
    import itertools
    
    # Validate and clean the observations list
    cleaned_observations = []
    for obs in observations:
        if isinstance(obs, (list, tuple)):
            cleaned_obs = [item for sublist in obs for item in (sublist,) if isinstance(item, (int))]
            cleaned_observations.append(cleaned_obs)
    
    # Brute-force search for the operating law
    for x1, y1, output1 in itertools.product(*cleaned_observations):
        for x2, y2, output2 in itertools.product(*cleaned_observations):
            if x1 != x2 and y1 != y2:
                try:
                    # Attempt to calculate the output using a simple linear combination
                    coefficients = [x1 * y2 - x2 * y1]
                    for x3, y3, _ in cleaned_observations:
                        if (x3 == x1 and y3 == y1) or (x3 == x2 and y3 == y2):
                            continue
                        output3 = coefficients[0] + x3 * y2 - x2 * y3
                        if not isinstance(output3, int):
                            raise ValueError("Output is not an integer")
                    # Check the consistency of the found law with all observations
                    for x, y, expected_output in cleaned_observations:
                        calculated_output = coefficients[0] + x * y2 - x2 * y
                        if calculated_output != expected_output:
                            break
                    else:
                        return (coefficients[0], x1, y1, output1)
                except Exception as e:
                    continue
    
    # If no consistent law is found, raise an error
    raise ValueError("No consistent operating law found for the given observations")

# Given data points
observations = [
    ([2, 3], 5),
    ([1, 4], 5),
    ([0, 7], 7),
    ([3, 2], 5),
    ([3, 3], 10)
]

try:
    # Find the operating law
    coefficients = find_operating_law(observations)
    
    # Output the True Law in a formatted manner
    true_law = f"True Law: y * {coefficients[1]} - x * {coefficients[2]} + {coefficients[0]}"
    print(true_law)
except ValueError as e:
    print(e)
