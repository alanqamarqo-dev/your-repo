import json, pathlib, hashlib
src = pathlib.Path('artifacts/harvested_facts.jsonl')
dst = pathlib.Path('artifacts/harvested_facts_dedup.jsonl')
seen = set(); kept=0; total=0
if not src.exists():
    print('Source file not found:', src)
    raise SystemExit(2)
with src.open('r', encoding='utf-8') as fin, dst.open('w', encoding='utf-8') as fout:
    for line in fin:
        total += 1
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            # skip malformed lines
            continue
        key = hashlib.sha1((obj.get('domain','')+'|'+obj.get('text','')).encode('utf-8')).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        fout.write(json.dumps(obj, ensure_ascii=False)+'\n')
        kept += 1
print("Kept", kept, "of", total, "→", dst)
