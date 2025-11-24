from pathlib import Path
import json
import re
import math
import collections
from typing import List, Dict, Optional

# fallbacks to existing modules if available
try:
    from reasoning.narrative_synthesizer import synthesize
except Exception:
    synthesize = None

ART = Path("artifacts")
HYP = ART / "hypotheses.jsonl"
FACTS = ART / "harvested_facts.jsonl"
OUT_JSON = ART / "theory_bundle.json"


# Lightweight Arabic normalizer and deduper
AR_ABBREV = {
    'الألدهيدات':'ألدهيدات','الكيتونات':'كيتونات','الأحماض الكربوكسيلية':'أحماض كربوكسيلية',
    'الكحول':'كحول','نيوتن':'نيوتن','الاحتكاك':'احتكاك','القدرة':'قدرة','التيار':'تيار','الجهد':'جهد'
}

def normalize_text(s: str) -> str:
    if s is None:
        return ''
    s = str(s).strip()
    s = re.sub(r'\s+', ' ', s)
    # light canonicalization for hamza/AL
    s = s.replace('الـ', 'ال').replace('أ', 'ا').replace('إ', 'ا').replace('آ','ا')
    for k,v in AR_ABBREV.items():
        s = s.replace(k, v)
    return s


def is_self_link(text: str) -> bool:
    # detect quoted segments '...' or «...» repeated
    q = re.findall(r"['\u00AB\u00BB\u00AB\u00BB](.+?)['\u00AB\u00BB]", text)
    if len(q) >= 2 and normalize_text(q[0]) == normalize_text(q[1]):
        return True
    # fallback: if same normalized text repeated
    parts = [p.strip() for p in re.split(r'[,;\n\-|ـ]', text) if p.strip()]
    if len(parts) >= 2 and normalize_text(parts[0]) == normalize_text(parts[1]):
        return True
    return False


def read_jsonl(path: Path) -> List[Dict]:
    out = []
    if not path.exists():
        return out
    with path.open('r', encoding='utf-8') as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln: continue
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    return out


def pick_topk_per_domain(items: List[Dict], k_total=40, domains=None, cap_ratio=0.34) -> List[Dict]:
    if not domains:
        domains = sorted({it.get('domain','unknown') for it in items})
    per_domain_cap = max(1, math.floor(k_total * cap_ratio))
    bucket = collections.defaultdict(list)
    for it in items:
        bucket[it.get('domain','unknown')].append(it)
    picked = []
    per_dom_k = max(1, k_total // max(1, len(domains)))
    for d in domains:
        dd = sorted(bucket.get(d, []), key=lambda x: x.get('confidence',0), reverse=True)[:max(per_dom_k, per_domain_cap)]
        picked.extend(dd)
    # trim to k_total by confidence
    return sorted(picked, key=lambda x: x.get('confidence',0), reverse=True)[:k_total]


def extract_entities(s: str):
    s = normalize_text(s)
    ents = set()
    pats = [r'-OH', r'-CHO', r'COOH', r'C\(=O\)', r'نيوتن', r'احتكاك', r'قدرة', r'تيار', r'جهد', r'ديناميكا']
    for pat in pats:
        if re.search(pat, s, flags=re.I):
            ents.add(pat)
    for kw in ['ألدهيدات','كيتونات','أحماض كربوكسيلية','كحول','مجموعة وظيفية','قانون نيوتن','طاقة']:
        if kw in s:
            ents.add(kw)
    # also add quoted tokens
    quotes = re.findall(r"['\u00AB\u00BB](.+?)['\u00AB\u00BB]", s)
    for q in quotes:
        ents.add(normalize_text(q))
    return ents


def build_links(narratives: List[Dict]):
    links = collections.Counter()
    ent_to_ids = collections.defaultdict(set)
    for i, n in enumerate(narratives):
        ents = extract_entities(n.get('text',''))
        for e in ents:
            ent_to_ids[e].add(i)
    ents = list(ent_to_ids.keys())
    for i in range(len(ents)):
        for j in range(i+1, len(ents)):
            a,b = ents[i], ents[j]
            inter = ent_to_ids[a] & ent_to_ids[b]
            # connect if they co-occur in >=2 narratives
            if len(inter) >= 2:
                links[tuple(sorted([a,b]))] += len(inter)
    result = [{'a':a, 'b':b, 'weight':w} for (a,b),w in links.items()]
    return sorted(result, key=lambda x: x['weight'], reverse=True)


def filter_narratives(raw_narrs: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for n in raw_narrs:
        txt = n.get('text') or ''
        if not txt: continue
        if is_self_link(txt):
            continue
        norm = normalize_text(txt)
        key = hashlib_sha256(norm)
        if key in seen:
            continue
        # reject repeated identical supports
        support = n.get('support') or []
        if isinstance(support, list) and len(support) >= 2 and normalize_text(support[0]) == normalize_text(support[1]):
            continue
        if len(norm) < 30:
            continue
        seen.add(key)
        n['text'] = norm
        out.append(n)
    return out


def hashlib_sha256(s: str) -> str:
    try:
        import hashlib
        return hashlib.sha256(s.encode('utf-8')).hexdigest()
    except Exception:
        return str(hash(s))


def estimate_coherence(narratives: List[Dict]) -> float:
    # Simple TF vectors + cosine similarity between adjacent narratives
    def tokenize(t: str):
        t = re.sub(r"[^\w\u0600-\u06FF]+", ' ', t)
        return [w for w in t.split() if len(w) > 1]

    docs = [tokenize(n.get('text','').lower()) for n in narratives]
    if len(docs) < 2:
        return 1.0
    # build vocabulary
    vocab = {}
    for d in docs:
        for w in d:
            if w not in vocab:
                vocab[w] = len(vocab)
    import math
    vectors = []
    for d in docs:
        vec = [0.0]*len(vocab)
        counts = collections.Counter(d)
        for w,c in counts.items():
            vec[vocab[w]] = c
        # normalize
        norm = math.sqrt(sum(x*x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        vectors.append(vec)
    # cosine between adjacent
    sims = []
    for i in range(len(vectors)-1):
        a = vectors[i]; b = vectors[i+1]
        dot = sum(x*y for x,y in zip(a,b))
        sims.append(dot)
    if not sims:
        return 0.0
    # clamp between 0 and 1
    avg = sum(sims)/len(sims)
    return max(0.0, min(1.0, avg))


def run(domains: Optional[List[str]] = None):
    # Load hypotheses; fallback to synthesize if not present
    raw_hyps = read_jsonl(HYP)
    if not raw_hyps and synthesize is not None:
        facts_idx = {}
        if FACTS.exists():
            with FACTS.open('r', encoding='utf-8') as f:
                for line in f:
                    try:
                        o = json.loads(line)
                        ts = o.get('ts')
                        if ts:
                            facts_idx[ts] = o.get('text','')
                    except Exception:
                        pass
        nar = synthesize(HYP, facts_idx, max_items=80)
        raw_hyps = nar.get('narratives', [])

    # If still empty, nothing to do
    if not raw_hyps:
        print('No hypotheses/narratives found; run reasoning cycle first.')
        return OUT_JSON

    # Normalize records: some files use 'hypothesis' as the text field
    normed = []
    for r in raw_hyps:
        rec = dict(r)
        if 'text' not in rec and 'hypothesis' in rec:
            rec['text'] = rec.get('hypothesis')
        # ensure domain exists
        if 'domain' not in rec:
            rec['domain'] = rec.get('subject') or 'unknown'
        # ensure support is list
        if 'support' not in rec:
            rec['support'] = rec.get('supports') or []
        normed.append(rec)

    # Basic filtering
    filtered = filter_narratives(normed)

    # Domains to ensure coverage
    if domains is None:
        domains = ["physics.classical","electricity.basics","chemistry.organic"]

    narratives = pick_topk_per_domain(filtered, k_total=40, domains=domains, cap_ratio=0.34)

    links = build_links(narratives)

    metrics = {
        'coherence': round(estimate_coherence(narratives), 3),
        'consistency': 1.0,
        'falsifiability': 1.0,
        'coverage': round(len({n.get('domain') for n in narratives})/max(1,len(domains)), 3),
        'links_count': len(links),
        'narratives_count': len(narratives),
        'domains_count': len({n.get('domain') for n in narratives})
    }

    bundle = {"narratives": narratives, "links": links, "metrics": metrics}
    ART.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding='utf-8')
    return OUT_JSON


if __name__ == "__main__":
    out = run()
    print(f"WROTE {out}")
