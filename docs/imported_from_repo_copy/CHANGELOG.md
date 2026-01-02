# Changelog

## G.1 - Initial KB snapshot and CI setup

- Create Knowledge_Base snapshot `G.1`
- Add GitHub Actions CI workflow that installs pinned dependencies, runs a JSON encoding check, and runs tests
- Add `tools/normalize_json.py` to normalize JSON files to UTF-8 without BOM and remove trailing garbage
- Add `requirements-pinned.txt` with pinned dependency versions
- Replace Unicode checkmark in `scripts/train_phaseD.py` with ASCII-safe output to avoid Windows encoding issues
