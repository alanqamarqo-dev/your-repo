"""Seed the system memory (ConsciousBridge) with many events.

Usage:
    python scripts/seed_memory.py [N]

Default N=12000. Adds mostly 'observation' events to LTM.
"""
import sys
from Core_Memory.bridge_singleton import get_bridge

def main():
    n = 12000
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except Exception:
            pass
    br = get_bridge()
    if br is None:
        print("No ConsciousBridge available; cannot seed memory.")
        return
    print(f"Seeding memory with {n} events...")
    batch = 0
    for i in range(n):
        br.put('observation', {'idx': i, 'text': f'auto-seed event {i}'}, to='ltm')
        if (i+1) % 1000 == 0:
            batch += 1
            print(f"  inserted {i+1} events...")
    stats = {"stm": len(br.stm), "ltm": len(br.ltm)}
    print("Seeding complete. Memory stats:", stats)

if __name__ == '__main__':
    main()
