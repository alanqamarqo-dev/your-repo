topic = "Solve the equation: 2x + 5 = 15"
topic_lower = topic.lower()
math_keywords = ["solve", "calculate", "equation", "حل", "احسب", "معادلة", "عادلة"]
is_math = any(kw in topic_lower for kw in math_keywords) and (any(c.isdigit() for c in topic) or "=" in topic)

print(f"topic_lower: {topic_lower}")
print(f"has_keyword: {any(kw in topic_lower for kw in math_keywords)}")
print(f"has_digit: {any(c.isdigit() for c in topic)}")
print(f"has_equal: {'=' in topic}")
print(f"is_math_task: {is_math}")
