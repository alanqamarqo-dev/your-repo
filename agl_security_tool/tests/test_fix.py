"""Test fix: parse EthAssetManager.sol after the array-IDENT fix."""
import os, sys, time, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LOG = Path(tempfile.gettempdir()) / "diag_fix_test.log"

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def main():
    LOG.write_text("", encoding="utf-8")
    # Look for .sol files in test_contracts/ relative to this project
    SRC = Path(__file__).resolve().parent.parent / "test_contracts" / "vulnerable"
    if not SRC.exists():
        log(f"Test contracts dir not found: {SRC}")
        return
    
    from agl_security_tool.detectors.solidity_ast_parser import SolidityASTParserFull
    parser = SolidityASTParserFull()
    
    # Test all files
    for path in sorted(SRC.glob("*.sol")):
        size_kb = path.stat().st_size / 1024
        log(f"Parsing {path.name} ({size_kb:.1f}KB)...")
        t0 = time.time()
        source = path.read_text(encoding="utf-8", errors="ignore")
        try:
            parsed = parser.parse(source, str(path))
            elapsed = time.time() - t0
            if parsed:
                nf = sum(len(c.functions) for c in parsed)
                log(f"  OK: {len(parsed)} contracts, {nf} funcs in {elapsed:.3f}s")
            else:
                log(f"  Empty parse in {elapsed:.3f}s")
        except Exception as e:
            log(f"  ERROR in {time.time()-t0:.3f}s: {str(e)[:200]}")
    
    log("=== ALL FILES PARSED ===")

if __name__ == "__main__":
    main()
