# Changelog

All notable changes are documented here. Format: [Keep a Changelog](https://keepachangelog.com/), versioning: [SemVer](https://semver.org/).

## [0.2.0] - 2026-10-16
### Changed
- **Python 3.10+ is now required** (`requires-python = ">=3.10"`); Python 3.9 is end-of-life and is no longer supported. CI tests Python 3.10 and 3.12, and README, CONTRIBUTING and SECURITY state the new floor.
- Dependency: `Pillow>=12.3.0` (was `>=10.1`), which itself requires Python 3.10+.
- README: Korean summary at the top, CI/License/Release badges, and a `License` section that links `SECURITY.md`.
- CI actions bumped: `actions/checkout` 4 → 7, `actions/setup-python` 5 → 7, `gitleaks/gitleaks-action` 2 → 3, `dependabot/fetch-metadata` 2 → 3.

### Added
- `requirements-dev.txt` (runtime requirements + pytest) and pytest configuration in `pyproject.toml` that always lists skip reasons. A fresh install per the README previously had no pytest, so `python -m pytest` failed with "No module named pytest". CI now runs the suite with pytest.
- README Testing section documents the dev install and that the ffmpeg-dependent chorus test is skipped when ffmpeg is unavailable.
- `CONTRIBUTING.md`.
- Dependabot weekly updates for pip and GitHub Actions, with auto-merge of patch/minor updates once checks pass.

## [0.1.0] - 2026-06-19
### Added
- Initial public release.
