from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'run_all.ps1'
s = p.read_text(encoding='utf-8')
# Re-write with BOM (utf-8-sig)
p.write_text(s, encoding='utf-8-sig')
print('Wrote', p, 'as utf-8-sig')
