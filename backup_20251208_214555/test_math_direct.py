#!/usr/bin/env python3
"""اختبار مباشر للمحرك الرياضي"""

from Core_Engines.Mathematical_Brain import MathematicalBrain

brain = MathematicalBrain()

print("=" * 60)
print("🧮 اختبار المحرك الرياضي مباشرة")
print("=" * 60)

tests = [
    "solve: 2x + 5 = 13",
    "2x+5=13",
    "calculate: 15 + 27 * 3",
    "15+27*3"
]

for test in tests:
    print(f"\n📝 الطلب: {test}")
    result = brain.process_task(test)
    print(f"✅ النتيجة: {result}")

print("\n" + "=" * 60)
