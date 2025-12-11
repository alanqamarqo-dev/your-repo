"""Test bootstrap engines"""
from Core_Engines import bootstrap_register_all_engines

reg = {}
result = bootstrap_register_all_engines(reg, verbose=False, max_seconds=30)

print(f'✅ Registered: {len(reg)} engines')

# Find skipped
skipped = {}
for name, info in result.items():
    if name not in reg:
        skipped[name] = str(info) if info else "unknown"

print(f'\n⚠️  Skipped: {len(skipped)} engines')
for name, reason in list(skipped.items())[:15]:
    print(f'  - {name}: {reason[:80]}')

# Show registered engines
print(f'\n📋 Registered engines:')
for i, name in enumerate(sorted(reg.keys())[:20], 1):
    print(f'  {i}. {name}')
if len(reg) > 20:
    print(f'  ... and {len(reg)-20} more')
