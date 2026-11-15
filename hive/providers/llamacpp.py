from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    """Raised when an AI provider cannot complete a request."""


class LlamaCppProvider:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ):
        self.base_url = (
            base_url or os.getenv(
                "HIVE_LLM_BASE_URL",
                "http://127.0.0.1:8080/v1"
            )
        ).rstrip("/")

        self.model = model or os.getenv(
            "HIVE_LLM_MODEL",
            "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"
        )

        self.timeout = timeout

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> str:
        if not messages:
            raise ValueError("At least one message is required.")

        if max_tokens < 1:
            raise ValueError("max_tokens must be positive.")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))

        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(
                f"AI server returned HTTP {exc.code}: {detail}"
            ) from exc

        except (URLError, TimeoutError, OSError) as exc:
            raise ProviderError(
                f"Could not connect to local AI server: {exc}"
            ) from exc

        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ProviderError(
                "AI server returned invalid JSON."
            ) from exc

        try:
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                "AI server returned an unexpected response structure."
            ) from exc

        if not isinstance(content, str):
            raise ProviderError("AI response content was not text.")

        return content
