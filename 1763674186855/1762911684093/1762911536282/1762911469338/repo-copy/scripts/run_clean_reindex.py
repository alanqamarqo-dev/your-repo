import sys, re
sys.path.insert(0, r'D:\AGL\repo-copy')
from Core_Memory.bridge_singleton import get_bridge
b = get_bridge()
keys = list(b.ltm.keys())
drop = []
for k in keys:
    v = b.ltm[k]
    s = str(v).lower()
    if re.search(r'auto[-_ ]seed', s) or len(s) < 40:
        drop.append(k)
for k in drop:
    b.ltm.pop(k, None)
print("removed_noisy =", len(drop))
b.export_ltm_to_db()
n = b.build_semantic_index()
print("reindexed_docs =", n)
