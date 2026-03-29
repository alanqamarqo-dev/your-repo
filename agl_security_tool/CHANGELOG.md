# Changelog

All notable changes to AGL Security Tool will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
adhering to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-03-29

### Added
- **14 new detectors**: MISSING-SLIPPAGE, SIGNATURE-REPLAY, FLASH-LOAN-NO-CHECK,
  UNCHECKED-CHAINLINK, UNSAFE-CAST, ABI-DECODE-COLLISION, STORAGE-COLLISION,
  UNINITIALIZED-PROXY, SELF-DESTRUCT-RISK, FRONT-RUN-RISK, MISSING-REENTRANCY-GUARD,
  ORACLE-SINGLE-SOURCE, HARDCODED-GAS-LIMIT, MISSING-EVENT-EMISSION
- **PoC generator**: Foundry-based exploit proof-of-concept generation with
  automatic contract name resolution
- **PoC linking**: Individual findings now include `poc` field linking to
  generated PoC test files
- **Config system**: Centralized `.env`-based configuration (`config.py`)
- **CI/CD**: GitHub Actions for tests, lint, and release
- **Docker**: Multi-stage Dockerfile + docker-compose (CLI + API modes)
- **File logging**: Rotating file handler with JSON format option
- **Weight training**: SGD-based weight optimizer with cross-validation

### Fixed
- PoC generator now resolves actual Solidity contract names instead of filenames
- Cross-layer deduplication rate (was negative, now correct)
- Semgrep YAML rules syntax (state-after-external-call pattern)
- BASE_INDEX_SCALE false positive eliminated
- URL typos in codebase removed

### Changed
- Total detectors: 24 -> 39
- Risk weights retrained with new training data
- Benchmark accuracy: 100% Precision, 100% Recall on test suite

## [2.0.0] - 2026-02-15

### Added
- 8-layer analysis pipeline (Layers 0-7)
- Z3 symbolic engine for formal verification
- Exploit reasoning with path analysis
- State extraction engine (Layer 1)
- Action space analysis (Layer 2)
- Attack simulation engine (Layer 3)
- Intelligent search engine (Layer 4)
- RiskCore probability scoring with trained weights
- Contract intelligence (Noisy-OR + MetaClassifier)
- Heikal Math advanced analysis
- Tool backends: Slither, Mythril, Semgrep integration
- Benchmark runner with SWC ground truth
- On-chain context module
- Project scanner for Foundry/Hardhat/Truffle/Bare projects

### Changed
- Full rewrite from v1.x single-pass to multi-layer architecture
- Semantic detection via ParsedContract operations (not regex)

## [1.0.0] - 2025-12-01

### Added
- Initial release
- Basic Solidity vulnerability detection
- Pattern-based analysis
- CLI interface
- JSON/Markdown output formats
