from __future__ import annotations

from .providers.llamacpp import LlamaCppProvider


def get_provider():
    """Return the configured default AI provider."""
    return LlamaCppProvider()


def ask(
    prompt: str,
    system: str = "You are HIVE, a technical AI assistant.",
    max_tokens: int = 512,
) -> str:
    """Send a prompt to the configured AI provider."""
    provider = get_provider()

    return provider.chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
    )



def get_status() -> dict:
    """Return the configured AI provider's live status."""
    return get_provider().status()
