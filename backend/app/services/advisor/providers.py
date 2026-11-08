import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class AdvisorProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class AdvisorMessage:
    role: str
    content: str


class ExtractedBusinessProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_type: str | None = None
    segment: str | None = None
    city_tier: int | None = Field(default=None, ge=1)
    employees: int | None = Field(default=None, ge=1)
    sites: int | None = Field(default=None, ge=1)
    gstin_active: bool | None = None
    missing_fields: list[str] = Field(default_factory=list)


class OllamaProvider:
    """Optional local Ollama provider for structured discovery only."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.timeout_seconds = timeout_seconds

    def extract_profile(self, messages: list[AdvisorMessage]) -> dict:
        for message in messages:
            if message.role not in {"system", "user", "assistant"}:
                raise AdvisorProviderError(f"Unsupported advisor message role: {message.role}")
            if not message.content.strip():
                raise AdvisorProviderError("Advisor messages cannot be empty.")
        prompt = (
            "Extract only a JSON business profile from the conversation. "
            "Do not recommend products or make eligibility decisions. "
            "Use keys business_type, segment, city_tier, employees, sites, gstin_active, missing_fields. "
            "Conversation:\\n"
            + "\\n".join(f"{message.role}: {message.content}" for message in messages)
        )
        payload = json.dumps(
            {
                "model": self.model,
                "stream": False,
                "format": "json",
                "prompt": prompt,
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            raise AdvisorProviderError(f"Ollama provider unavailable: {error}") from error
        try:
            extracted = json.loads(result["response"])
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise AdvisorProviderError("Ollama returned invalid structured profile output.") from error
        try:
            return ExtractedBusinessProfile.model_validate(extracted).model_dump()
        except (TypeError, ValidationError) as error:
            raise AdvisorProviderError("Ollama profile failed schema validation.") from error


class DeterministicAdvisorProvider:
    """Safe no-model fallback that requests the full structured profile."""

    def extract_profile(self, messages: list[AdvisorMessage]) -> dict[str, Any]:
        return {
            "business_type": None,
            "segment": None,
            "city_tier": None,
            "employees": None,
            "sites": None,
            "gstin_active": None,
            "missing_fields": [
                "business_type",
                "segment",
                "city_tier",
                "employees",
                "sites",
                "gstin_active",
            ],
        }


class FallbackAdvisorProvider:
    def __init__(self, primary, fallback: OllamaProvider | None = None) -> None:
        self.primary = primary
        self.fallback = fallback or OllamaProvider()
        self.deterministic = DeterministicAdvisorProvider()

    def extract_profile(self, messages: list[AdvisorMessage]) -> dict:
        try:
            return self.primary.extract_profile(messages)
        except AdvisorProviderError:
            try:
                return self.fallback.extract_profile(messages)
            except AdvisorProviderError:
                return self.deterministic.extract_profile(messages)
