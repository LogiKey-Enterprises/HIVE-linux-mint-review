import json
from unittest.mock import patch

import pytest

from hive.ai import ask
from hive.providers.llamacpp import LlamaCppProvider, ProviderError


class FakeResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return self.data


def test_local_provider_returns_assistant_response():
    response = {
        "choices": [
            {"message": {"content": "HIVE local AI operational."}}
        ]
    }

    with patch(
        "hive.providers.llamacpp.urlopen",
        return_value=FakeResponse(response),
    ) as mocked:
        provider = LlamaCppProvider()
        result = provider.chat([
            {"role": "user", "content": "Test"}
        ])

    assert result == "HIVE local AI operational."
    request = mocked.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["messages"][0]["content"] == "Test"
    assert request.full_url.endswith("/v1/chat/completions")


def test_provider_uses_configured_model():
    provider = LlamaCppProvider(model="test-model")
    assert provider.model == "test-model"


def test_provider_rejects_empty_messages():
    provider = LlamaCppProvider()

    with pytest.raises(ValueError):
        provider.chat([])


def test_provider_rejects_invalid_token_limit():
    provider = LlamaCppProvider()

    with pytest.raises(ValueError):
        provider.chat(
            [{"role": "user", "content": "Test"}],
            max_tokens=0,
        )


def test_provider_rejects_unexpected_response():
    with patch(
        "hive.providers.llamacpp.urlopen",
        return_value=FakeResponse({"unexpected": True}),
    ):
        provider = LlamaCppProvider()

        with pytest.raises(ProviderError):
            provider.chat([
                {"role": "user", "content": "Test"}
            ])


def test_ask_uses_configured_provider():
    with patch(
        "hive.ai.get_provider"
    ) as mocked:
        mocked.return_value.chat.return_value = "Connected"

        result = ask("Test HIVE")

    assert result == "Connected"
    mocked.return_value.chat.assert_called_once()
