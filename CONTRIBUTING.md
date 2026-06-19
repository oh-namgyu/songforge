# Contributing to SongForge

Thanks for your interest! SongForge turns a topic into a finished, publishable song package
(AI lyrics → ACE-Step music/vocals → chorus detection → video → upload plan).

## Development setup

```bash
git clone https://github.com/oh-namgyu/songforge
cd songforge
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # fill in your own keys
```

ACE-Step (music/vocals) is **bring-your-own** — see [ACE_STEP_API.md](ACE_STEP_API.md). `ffmpeg` must be on PATH.

## Running tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

CI runs the same on Python 3.9 and 3.11 plus a `gitleaks` secret scan. Please make sure tests pass
and no secrets are committed before opening a PR.

## Guidelines

- Keep modules small and single-purpose (the codebase favors short, composable files).
- No secrets, API keys, or personal paths in commits — `.env` is git-ignored; use `.env.example`.
- Match the existing style; add or update a test when you change behavior.
- One focused change per PR with a short, clear description of the *why*.

## Reporting issues

Open a GitHub issue with steps to reproduce, expected vs. actual, and your OS / Python version.
For security concerns, follow [SECURITY.md](SECURITY.md) instead of filing a public issue.

## License

By contributing you agree your contributions are licensed under the project's [Apache-2.0](LICENSE) license.
