# Simple demo data generator for common laws
import os, csv, math, random

os.makedirs('data', exist_ok=True)

# Hooke: F = k*x
with open('data/spring_samples.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['F','x'])
    k = 12.5
    for i in range(1,101):
        x = i*0.01
        F = k * x + random.gauss(0, 0.02)
        writer.writerow([F, x])

# Ohm: V = I*R
with open('data/ohm_samples.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['V','I'])
    R = 10.0
    for i in range(1,101):
        I = i*0.01
        V = R * I + random.gauss(0, 0.01)
        writer.writerow([V, I])

# Power law example: T = a * x^n
with open('data/power_samples.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['T','x'])
    a = 2.0
    n = 1.5
    for i in range(1,101):
        x = i*0.1
        T = a * (x**n) + random.gauss(0, 0.05)
        writer.writerow([T, x])

print('Demo data generated in data/*.csv')
