import re
from collections import Counter, defaultdict
from pathlib import Path

p = Path('dynamic_modules/mission_control_enhanced.py')
s = p.read_text(encoding='utf-8')

# find quoted tokens that look like engine names (CamelCase, may include digits and underscores)
quoted = re.findall(r"['\"][A-Za-z0-9_]+['\"]", s)
tokens = [q.strip("'\"") for q in quoted]
# filter tokens starting with uppercase letter and containing letters
engines = [t for t in tokens if re.match(r'^[A-Z][A-Za-z0-9_]+$', t)]
counts = Counter(engines)

# find clusters inside define_clusters by locating the 'define_clusters' block
clusters = defaultdict(lambda: defaultdict(list))
m = re.search(r"def define_clusters\(self\) -> Dict\[str, Dict\[str, List\[str\]\]\]:\s*return\s*\{", s)
if m:
    # naive parse: find the return {...} balanced braces
    start = m.start()
    # find the first '{' after 'return'
    ret_pos = s.find('return', start)
    brace_pos = s.find('{', ret_pos)
    # balance braces
    i = brace_pos
    depth = 0
    while i < len(s):
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                end = i+1
                break
        i += 1
    block = s[brace_pos:end]
    # find cluster names and lists
    cluster_matches = re.finditer(r"'(?P<cluster>[^']+)'\s*:\s*\{(?P<body>.*?)\},", block, re.S)
    for cm in cluster_matches:
        cname = cm.group('cluster')
        body = cm.group('body')
        for listname in ('primary','support','review'):
            lm = re.search(rf"'{listname}'\s*:\s*\[(?P<items>.*?)\]", body, re.S)
            if lm:
                items = re.findall(r"['\"]([A-Za-z0-9_]+)['\"]", lm.group('items'))
                clusters[cname][listname] = items

# group similar names by base (strip Engine/Core/Solver/Processor suffixes)
def base_name(name):
    for suf in ('Engine','Core','Solver','Processor'):
        if name.endswith(suf):
            return name[:-len(suf)]
    return name

groups = defaultdict(list)
for name in set(engines):
    groups[base_name(name)].append(name)

# output
print('== Engines found (unique):', len(set(engines)))
for name, cnt in counts.most_common():
    print(f' - {name}: {cnt}')

print('\n== Cluster breakdown:')
for c, parts in clusters.items():
    print(f'Cluster: {c}')
    for role in ('primary','support','review'):
        print('  ', role, ':', parts.get(role, []))

print('\n== Similar/variant groups:')
for b, names in sorted(groups.items(), key=lambda x: (-len(x[1]), x[0])):
    if len(names) > 1:
        print(' *', b, '->', names)

print('\n== Recommendations:')
print(' - Consider mapping variant groups to a single canonical engine implementation (e.g., AdvancedQuantumEngine / QuantumCore -> choose one).')
print(' - Add telemetry in simulate_engine to log when a less-capable engine is used.')
print(' - Centralize engine preference via a small registry file: config/engine_preference.py')
