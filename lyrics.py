"""Lyric writer — persona + recent themes -> a validated song spec.

The spec (see ``schemas/song_spec.schema.json``) is the contract handed to the
rest of the pipeline. The model is asked for JSON only; we parse, then enforce
the contract in code (no jsonschema dependency).
"""
from __future__ import annotations

import json
import re

from providers import get_provider
from providers.base import LLMProvider

REQUIRED = ("slug", "title", "theme", "full_lyrics", "hook", "tags")
SLUG_RE = re.compile(r"[a-z0-9_]{3,40}")

PROMPT = """You are the songwriter for this artist. Write ONE new original song.

ARTIST
{persona}

LYRIC RULES
{rules}

RECENT THEMES (avoid repeating these — pick a fresh angle within the persona):
{recent}

Respond with ONLY a JSON object (no markdown fence, no commentary):
{{
  "slug": "ascii_snake_case_short",
  "title": "Short Title",
  "theme": "one-line theme summary",
  "full_lyrics": "[verse]\\n...\\n\\n[chorus]\\n...\\n\\n[verse]\\n...\\n\\n[chorus]\\n...",
  "hook": "the chorus hook, max 2 short lines separated by \\n",
  "bg_query": "background video search, 3-5 words",
  "description": "one evocative sentence for the upload description",
  "tags": ["8-14 tags"]
}}"""


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError(f"No JSON object in model output: {text[:200]}")
    return json.loads(match.group(0))


def validate_spec(spec: dict, *, existing_slugs=()) -> dict:
    """Enforce the song-spec contract. Raises ``ValueError`` on any violation."""
    if not isinstance(spec, dict):
        raise ValueError("spec is not a JSON object")
    missing = [k for k in REQUIRED if not spec.get(k)]
    if missing:
        raise ValueError(f"spec missing fields: {missing}")
    if not SLUG_RE.fullmatch(spec["slug"]):
        raise ValueError(f"invalid slug (need [a-z0-9_]{{3,40}}): {spec['slug']!r}")
    if spec["slug"] in set(existing_slugs):
        raise ValueError(f"duplicate slug (would overwrite): {spec['slug']}")
    if "[chorus]" not in spec["full_lyrics"]:
        raise ValueError("full_lyrics has no [chorus] section")
    if not isinstance(spec["tags"], list) or not spec["tags"]:
        raise ValueError("tags must be a non-empty list")
    return spec


def write_spec(cfg, persona: dict, recent_themes=(), *,
               provider: LLMProvider | None = None, existing_slugs=()) -> dict:
    """Generate and validate one song spec.

    ``provider`` can be injected (e.g. ``FakeProvider`` in tests); otherwise it
    is built from ``cfg``.
    """
    provider = provider or get_provider(cfg)
    prompt = PROMPT.format(
        persona=persona.get("persona") or "",
        rules="\n".join(f"- {r}" for r in (persona.get("lyric_rules") or [])),
        recent="\n".join(f"- {t}" for t in (list(recent_themes) or ["(none yet)"])),
    )
    raw = provider.generate(prompt)
    return validate_spec(_parse_json(raw), existing_slugs=existing_slugs)
