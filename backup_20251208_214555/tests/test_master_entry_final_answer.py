import runpy
import sys
import io
import os
import re


def test_master_entry_plan_prints_final_answer():
    """Run the entry script with --plan and assert a final answer marker is printed.

    This test is conservative: it accepts either the explicit
    '--- FINAL ANSWER ---' marker or the fallback markers that the
    runner prints when it reads the DB ('FALLBACK DB LTM ANSWER' / 'FALLBACK LTM ANSWER').
    """
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(repo)

    buf = io.StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.stdout = buf
        sys.stderr = buf
        sys.argv = ['scripts/agl_master_entry.py', '--plan', '-q', 'ما هي أعراض الإنفلونزا']
        # run the script as __main__ to exercise the CLI path
        runpy.run_path('scripts/agl_master_entry.py', run_name='__main__')
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    out = buf.getvalue()
    # Look for any of the expected markers
    marker_re = re.compile(r'---\s*FINAL ANSWER\s*---|---\s*FALLBACK DB LTM ANSWER\s*---|---\s*FALLBACK LTM ANSWER\s*---')
    assert marker_re.search(out), f"Final answer marker not found in output:\n{out}"

    # Ensure there's some non-empty text after the marker
    m = marker_re.search(out)
    assert m is not None
    tail = out[m.end():].strip()
    # first non-empty line after marker should be present
    first_line = None
    for ln in tail.splitlines():
        s = ln.strip()
        if s:
            first_line = s
            break
    assert first_line, f"No answer text found after final marker. Output:\n{out}"

    # Harden: assert the answer contains at least one expected medical keyword
    keywords = [
        'عدوى فيروسية',
        'درجة مئوية',
        'سعال جاف',
        'حمى',
        'آلام',
        'صداع',
    ]
    lower_out = out.lower()
    found = False
    for kw in keywords:
        if kw in lower_out:
            found = True
            break
    assert found, f"No medical keyword found in output. Expected one of: {keywords}\nOutput:\n{out}"
