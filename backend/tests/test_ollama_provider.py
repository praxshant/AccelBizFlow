import json

import pytest

from app.services.advisor.providers import (
    AdvisorMessage,
    AdvisorProviderError,
    DeterministicAdvisorProvider,
    FallbackAdvisorProvider,
    OllamaProvider,
)


def test_ollama_provider_defaults_to_local_model(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    provider = OllamaProvider()

    assert provider.model == "llama3.2"
    assert provider.base_url == "http://localhost:11434"
    assert AdvisorMessage(role="user", content="clinic").role == "user"


def test_ollama_provider_rejects_unknown_message_role():
    provider = OllamaProvider()

    with pytest.raises(AdvisorProviderError, match="Unsupported advisor message role"):
        provider.extract_profile([AdvisorMessage(role="tool", content="unsafe")])


def test_ollama_provider_rejects_malformed_structured_output(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"response": '{"segment": 42}'}).encode()

    monkeypatch.setattr(
        "app.services.advisor.providers.urlopen",
        lambda request, timeout: Response(),
    )

    with pytest.raises(AdvisorProviderError, match="schema validation"):
        OllamaProvider().extract_profile([AdvisorMessage(role="user", content="clinic")])


def test_fallback_provider_uses_deterministic_profile_when_models_fail():
    class FailingProvider:
        def extract_profile(self, messages):
            raise AdvisorProviderError("unavailable")

    result = FallbackAdvisorProvider(
        FailingProvider(),
        FailingProvider(),
    ).extract_profile([AdvisorMessage(role="user", content="clinic")])

    assert result["business_type"] is None
    assert "segment" in result["missing_fields"]
