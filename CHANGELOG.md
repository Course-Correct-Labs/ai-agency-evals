# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Mirror Loop analysis-only demo module
  - Python script and Jupyter notebook for reproducing ΔI decay curves
  - Cached CSV analysis (no API calls)
  - Figures: `fig_mirrorloop_curve.png`, `fig_novelty_curve.png`
  - 54.1% ΔI reduction demonstrates recursive convergence
- SECURITY.md with secret scanning guidelines
- Enhanced .gitignore for comprehensive secret protection
- Safety and Reproducibility section in README
- Colab badge for Mirror Loop notebook

### Changed
- Updated README header to include four-paper overview
- Python version support clarified: 3.9-3.11+

## [0.1.0] - 2025-10-09

### Added
- Initial public release
- Three evaluation modules: phi_eval, di_eval, ot_bench
- Mock mode for deterministic testing
- CI/CD with GitHub Actions
- Complete documentation and metric cards
- Cost estimation utilities
- CITATION.cff for GitHub citation feature

[Unreleased]: https://github.com/BentleyRolling/ai-agency-evals/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/BentleyRolling/ai-agency-evals/releases/tag/v0.1.0
