#!/usr/bin/env python3
"""Print cleaned answers from an AGI evaluation JSON file.
Usage: python .\scripts\print_agi_answers.py artifacts/agi_eval_result_system.json
"""
import sys
import json
import re
import ast

def try_parse_answer(a):
    # If already a dict/list, return pretty string
    if isinstance(a, (dict, list)):
        return json.dumps(a, ensure_ascii=False)
    if not isinstance(a, str):
        return str(a)

    s = a.strip()
    # Try JSON
    try:
        return json.dumps(json.loads(s), ensure_ascii=False)
    except Exception:
        pass

    # Try literal_eval (for Python repr dicts)
    try:
        val = ast.literal_eval(s)
        # if it's a dict with message.content, attempt to extract
        if isinstance(val, dict):
            # common nested shapes
            for k in ('text','reply','message','answer'):
                if k in val and isinstance(val[k], str):
                    return val[k]
            # message may be nested
            msg = val.get('message') or val.get('engine_result')
            if isinstance(msg, dict):
                for k in ('content','text','reply'):
                    if k in msg and isinstance(msg[k], str):
                        return msg[k]
        return str(val)
    except Exception:
        pass

    # Fallback: try to extract content between "content': '...'}"
    m = re.search(r"content\'\s*:\s*\'(.+?)\'\}\,\s*'done'", s, flags=re.S)
    if m:
        return m.group(1).encode('utf-8').decode('unicode_escape')

    # Try to find inner JSON-like string inside 'content': '{\n  "answer": "..."'
    m2 = re.search(r"content\'\s*:\s*\'(\\n.*)\'\}\,\s*'done'", s, flags=re.S)
    if m2:
        inner = m2.group(1)
        # unescape
        try:
            return inner.encode('utf-8').decode('unicode_escape')
        except Exception:
            return inner

    # As last resort, return the original string (trimmed)
    return s[:2000]

def main():
    if len(sys.argv) < 2:
        print('Usage: print_agi_answers.py <eval_json>')
        sys.exit(2)
    path = sys.argv[1]
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for q in data.get('questions', []):
        print('---')
        print(f"{q.get('id')}  {q.get('part')}")
        print('Prompt:')
        print(q.get('prompt'))
        print('\nSystem answer (cleaned):')
        cleaned = try_parse_answer(q.get('answer'))
        # If cleaned contains nested JSON-looking text, try to pretty it
        if isinstance(cleaned, str) and (cleaned.strip().startswith('{') or cleaned.strip().startswith('[')):
            try:
                obj = json.loads(cleaned)
                # if obj has 'message' with 'content' that looks like JSON, prefer that
                if isinstance(obj, dict):
                    if 'message' in obj and isinstance(obj['message'], dict) and 'content' in obj['message']:
                        print(obj['message']['content'])
                    elif 'text' in obj and isinstance(obj['text'], str):
                        print(obj['text'])
                    else:
                        print(json.dumps(obj, ensure_ascii=False, indent=2))
                else:
                    print(json.dumps(obj, ensure_ascii=False, indent=2))
            except Exception:
                print(cleaned)
        else:
            print(cleaned)

        print('\nResponse time (s):', q.get('response_time_sec'))
        print('\n')

if __name__ == '__main__':
    main()
