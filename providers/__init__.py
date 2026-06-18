"""Provider registry — map ``LLM_PROVIDER`` to an implementation."""
from __future__ import annotations

from .base import LLMProvider
from .fake import FakeProvider


def get_provider(cfg) -> LLMProvider:
    """Build the LLM provider named by ``cfg.llm_provider``."""
    name = cfg.llm_provider.lower()
    if name == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(cfg.require_anthropic(), cfg.llm_model)
    if name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(cfg.anthropic_api_key or "", cfg.llm_model)
    if name == "fake":
        return FakeProvider()
    raise ValueError(
        f"Unknown LLM_PROVIDER: {cfg.llm_provider!r} "
        "(supported: anthropic, openai, fake)"
    )


__all__ = ["LLMProvider", "FakeProvider", "get_provider"]
