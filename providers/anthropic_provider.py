"""Anthropic (Claude) LLM provider — the default lyric writer.

The ``anthropic`` package is imported lazily inside :meth:`generate`, so the
rest of the project (and its tests) can import this module without the SDK
installed or an API key set.
"""
from __future__ import annotations

from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        self._client = None

    def _client_or_init(self):
        if self._client is None:
            import anthropic  # lazy: only needed when actually generating
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def generate(self, prompt: str, *, max_tokens: int = 2000,
                 temperature: float = 0.9) -> str:
        msg = self._client_or_init().messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in msg.content
            if getattr(block, "type", None) == "text"
        )
