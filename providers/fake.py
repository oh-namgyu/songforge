"""Deterministic provider for tests and dry runs — no network, no API key.

Returns a valid song spec (or whatever spec it was constructed with), so the
pipeline can be exercised end-to-end in CI without calling a real LLM.
"""
from __future__ import annotations

import json

from .base import LLMProvider

VALID_SPEC = {
    "slug": "city_of_quiet_rain",
    "title": "City of Quiet Rain",
    "theme": "finding stillness in a sleepless city",
    "full_lyrics": (
        "[verse]\nNeon bleeds across the glass\nevery hour too slow to pass\n\n"
        "[chorus]\nCity of quiet rain\nwash the noise away again\n\n"
        "[verse]\nFootsteps fold into the dark\na streetlight keeps a fading spark\n\n"
        "[chorus]\nCity of quiet rain\nwash the noise away again"
    ),
    "hook": "City of quiet rain\nwash the noise away again",
    "bg_query": "rainy night city window",
    "description": "A hush settles over the late-night city as the rain takes over.",
    "tags": ["lofi", "rain", "night city", "chill", "ambient",
             "study", "sleep", "calm"],
}


class FakeProvider(LLMProvider):
    def __init__(self, spec: dict | None = None, raw: str | None = None):
        # `raw` lets a test force malformed/garbage output.
        self._raw = raw
        self._spec = spec if spec is not None else VALID_SPEC

    def generate(self, prompt: str, *, max_tokens: int = 2000,
                 temperature: float = 0.9) -> str:
        if self._raw is not None:
            return self._raw
        return json.dumps(self._spec, ensure_ascii=False)
