"""SongForge configuration.

Every machine-specific value (API keys, the ACE-Step endpoint, the ffmpeg
binary, font files, the output directory) is loaded here from the environment
or an optional ``.env`` file. The rest of the pipeline imports :func:`load`
and never hardcodes a path, so the same code runs on any machine.

    >>> from config import load
    >>> cfg = load()
    >>> cfg.ace_endpoint
    'http://127.0.0.1:8001'
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class ConfigError(RuntimeError):
    """A required setting is missing. Carries a human-friendly hint."""


def _load_dotenv(path: Path) -> None:
    """Populate ``os.environ`` from a ``KEY=VALUE`` file (does not override
    values already present in the environment). Intentionally tiny so the
    project keeps a minimal dependency surface."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


@dataclass
class Config:
    # ── LLM (lyric writer) ──────────────────────────────────────
    llm_provider: str
    llm_model: str
    anthropic_api_key: str | None
    # ── ACE-Step music backend (bring your own) ─────────────────
    ace_endpoint: str
    ace_spawn_local: bool
    ace_dir: str | None
    ace_uv: str | None
    ace_lm: str
    ace_poll_seconds: int
    ace_poll_max: int
    # ── Media ───────────────────────────────────────────────────
    ffmpeg: str
    font_regular: str | None
    font_bold: str | None
    pexels_api_key: str | None
    # ── Output ──────────────────────────────────────────────────
    out_dir: Path

    def require_anthropic(self) -> str:
        """Return the Anthropic key or raise a friendly error.

        Called only when lyrics are actually generated, so ``load()`` itself
        never fails just because a key is absent."""
        if not self.anthropic_api_key:
            raise ConfigError(
                "ANTHROPIC_API_KEY is not set. Add it to .env (copy "
                ".env.example) or `export ANTHROPIC_API_KEY=...` before running."
            )
        return self.anthropic_api_key

    def require_spawn_paths(self) -> None:
        """Validate the extra settings needed only when SongForge is asked to
        spawn ACE-Step locally instead of using an existing endpoint."""
        missing = [k for k, v in (("ACE_STEP_DIR", self.ace_dir),
                                  ("ACE_STEP_UV", self.ace_uv)) if not v]
        if missing:
            raise ConfigError(
                f"ACE_STEP_SPAWN_LOCAL=true but {', '.join(missing)} not set. "
                "Either set them or use ACE_STEP_SPAWN_LOCAL=false and point "
                "ACE_STEP_ENDPOINT at a running ACE-Step server."
            )


def load(env_file: str | os.PathLike | None = None) -> Config:
    """Load configuration from the environment (and ``.env`` if present)."""
    _load_dotenv(Path(env_file) if env_file else ROOT / ".env")
    out_dir = Path(os.environ.get("SONGFORGE_OUT_DIR", str(ROOT / "out"))).expanduser()
    return Config(
        llm_provider=os.environ.get("LLM_PROVIDER", "anthropic"),
        llm_model=os.environ.get("LLM_MODEL", "claude-sonnet-4-6"),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        ace_endpoint=os.environ.get("ACE_STEP_ENDPOINT", "http://127.0.0.1:8001"),
        ace_spawn_local=_as_bool(os.environ.get("ACE_STEP_SPAWN_LOCAL")),
        ace_dir=os.environ.get("ACE_STEP_DIR") or None,
        ace_uv=os.environ.get("ACE_STEP_UV") or None,
        ace_lm=os.environ.get("ACE_STEP_LM", "acestep-5Hz-lm-1.7B"),
        ace_poll_seconds=_as_int(os.environ.get("ACE_STEP_POLL_SECONDS"), 8),
        ace_poll_max=_as_int(os.environ.get("ACE_STEP_POLL_MAX"), 120),
        ffmpeg=os.environ.get("FFMPEG_PATH", "ffmpeg"),
        font_regular=os.environ.get("FONT_REGULAR") or None,
        font_bold=os.environ.get("FONT_BOLD") or None,
        pexels_api_key=os.environ.get("PEXELS_API_KEY") or None,
        out_dir=out_dir,
    )


if __name__ == "__main__":  # `python config.py` → quick sanity print
    cfg = load()
    print(cfg)
    print("anthropic key:", "set" if cfg.anthropic_api_key else "MISSING (set before generating)")
