
def slow_function():
    # This loop is very slow and does nothing useful
    x = 0
    for i in range(1000):
        for j in range(1000):
            x += 1
    print("Done")
    return x
