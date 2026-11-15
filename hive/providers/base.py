from __future__ import annotations

from typing import Protocol


class AIProvider(Protocol):
    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> str:
        ...
