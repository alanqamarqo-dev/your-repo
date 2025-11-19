from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from reasoning.theory_pipeline import run
from infra.reporting.viz_theory_report import render

def main():
    out = run()
    r = render(out)
    print('WROTE', out, 'and', r)

if __name__ == '__main__':
    main()
