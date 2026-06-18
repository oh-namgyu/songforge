"""LLM provider interface.

A provider turns a prompt into text. Swapping the lyric-writing backend
(Anthropic, OpenAI, a local model, …) means implementing this one method —
nothing else in the pipeline knows which backend is in use.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, *, max_tokens: int = 2000,
                 temperature: float = 0.9) -> str:
        """Return the model's text response to ``prompt``."""
        raise NotImplementedError
