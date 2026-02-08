def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:
        raise ValueError("Cannot calculate average of an empty list")
    total = sum(numbers)
    return total / len(numbers)


if __name__ == "__main__":
    # This will crash with ZeroDivisionError
    result = calculate_average([])
    print(f"Average: {result}")
