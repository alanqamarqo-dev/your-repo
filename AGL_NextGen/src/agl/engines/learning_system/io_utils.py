import io, json, os

def read_json(path):
    """Read JSON from path using utf-8-sig to tolerate BOM and return the loaded object.

    Use this helper everywhere to avoid BOM issues and unclosed-file ResourceWarnings.
    """
    with io.open(path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def read_text(path, encoding='utf-8-sig'):
    with io.open(path, 'r', encoding=encoding) as f:
        return f.read()


def read_json_with_fallback(primary='Knowledge_Base/Learned_Patterns.json'):
    """Read the canonical KB but fall back to lock or .new if primary missing.

    Returns the loaded JSON object. Does not modify lock files. If no file is
    found, raises FileNotFoundError.
    """
    paths = [primary, primary + '.lock', primary + '.lock.json', primary.replace('.json', '.json.new')]
    last_exc = None
    for p in paths:
        try:
            if os.path.exists(p):
                with io.open(p, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
        except Exception as e:
            last_exc = e
            # try next
            continue
    if last_exc:
        raise last_exc
    raise FileNotFoundError(f"KB not found in any of: {paths}")
