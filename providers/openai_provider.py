"""OpenAI LLM provider — extension slot.

This is the worked example of how to add a backend: implement ``generate`` and
register the provider name in ``providers/__init__.py``. Left as a stub so the
pluggable boundary is concrete without pulling in an unused dependency.
"""
from __future__ import annotations

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    def generate(self, prompt: str, *, max_tokens: int = 2000,
                 temperature: float = 0.9) -> str:
        # To enable: `pip install openai`, then mirror AnthropicProvider —
        #   from openai import OpenAI
        #   client = OpenAI(api_key=self._api_key)
        #   resp = client.chat.completions.create(model=self._model, ...)
        #   return resp.choices[0].message.content
        raise NotImplementedError(
            "OpenAIProvider is a stub. Implement generate() and set "
            "LLM_PROVIDER=openai to use it. See AnthropicProvider for the shape."
        )
