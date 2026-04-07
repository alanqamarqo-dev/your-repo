# Changelog

All notable changes to AGL Security Tool will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.1.1] - 2026-04-08

### Fixed
- **Environment unification**: Cleaned 25+ files with broken imports (sys.path hacks, dual try/except imports, phantom `agl.engines.*` references)
- **state_extraction/**: Fixed 8 modules with `sys.path.insert` hacks → canonical `from agl_security_tool.` imports
- **action_space/**: Fixed 4 modules with bare imports → canonical package imports
- **api/full_audit.py**: Removed unnecessary `sys.path.insert`
- **api/auth.py**: Replaced `passlib` with direct `bcrypt` (passlib incompatible with bcrypt >= 4.1)
- **api/database_mongo.py**: Fixed BOM/mojibake encoding issue
- **core.py**: Removed phantom `agl.engines.*` imports and dead code (`self._analyzer`, `self._suite`)
- **vscode_bridge.py**: Removed `AGL_NextGen` path reference from `detect_engines()`
- **__main__.py**: Fixed version string from 1.1.0 to 2.1.0

### Added
- **docs/ENVIRONMENT.md**: Comprehensive dependency, environment, Docker, and troubleshooting guide
- **E2E pipeline verification**: Full pipeline tested on Beedle Lender.sol — all 11 engines, all 8 layers verified
- **docker-compose.yml**: Added `agl-audit` service for full pipeline audits
- **Dockerfile**: Added `audit` build stage for `agl-audit` CLI
- **DEPLOYMENT.md**: Production deployment guide with reverse proxy, secrets, testing

### Changed
- **README.md**: Complete rewrite with E2E verification status, full CLI reference, architecture diagram
- **CHANGELOG.md**: Updated with all changes since v2.1.0
- **requirements.txt/requirements-lock.txt**: Unified dependencies, `passlib` → `bcrypt`
- **pyproject.toml**: Unified with requirements files, `pydantic`/`psutil` moved to core deps

## [2.1.0] - 2026-03-28

### Added
- 8-layer audit pipeline (`audit_pipeline.py`) with full orchestration
- Z3 symbolic engine for formal verification (`z3_symbolic_engine.py`)
- Exploit reasoning with Z3 SAT proofs (`exploit_reasoning.py`)
- Heikal mathematical risk scoring (`heikal_math/`)
- Contract intelligence: Noisy-OR aggregation + MetaClassifier (`contract_intelligence.py`)
- Weight optimizer with SGD training (`weight_optimizer.py`)
- 39 semantic detectors across 13 categories
- State extraction engine (Layer 1-4): execution semantics, function effects, state mutation
- Action space builder + attack engine + guided search (MCTS)
- PoC generator with Foundry/Hardhat templates (`poc_generator.py`)
- Benchmark runner with SWC ground truth (`benchmark_runner.py`)
- FastAPI server with JWT auth, WebSocket, rate limiting (`api/`)
- Project scanner for Foundry/Hardhat/Truffle detection (`project_scanner.py`)
- Solidity flattener with import resolution (`solidity_flattener.py`)
- On-chain context integration (`onchain_context.py`)
- Docker support (CLI + API modes)
- Bilingual comments (Arabic + English) in core modules

### Changed
- Risk scoring upgraded to trained logistic regression (P(exploit) = sigma function)
- Detector confidence levels calibrated against real-world benchmarks

## [2.0.0] - 2026-02-15

### Added
- `RiskCore` probability engine replacing simple severity labels
- Formal verification layer with Z3 solver
- Tool backends: native Slither, Mythril, Semgrep runners
- Deep analyzer for cross-contract analysis
- Training contracts infrastructure (`training_contracts/`)

### Changed
- Restructured from single-file to modular package
- Detectors migrated to `BaseDetector` pattern with registry
- Parser upgraded with operation-level extraction (OpType enums)

### Removed
- Legacy regex-only detection mode
- Flat severity strings (replaced by `Severity` enum)

## [1.0.0] - 2026-01-10

### Added
- Initial release
- Core Solidity parser with function/state variable extraction
- 15 basic vulnerability detectors (reentrancy, access control, common patterns)
- CLI interface (`python -m agl_security_tool`)
- JSON and Markdown report output
- Basic risk scoring (HIGH/MEDIUM/LOW)
