
import os
from typing import Protocol

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class LLMProvider(Protocol):
    """Common interface for LLM providers."""

    def complete(self, prompt: str) -> str:
        ...


class GroqLLMClient:
    """Adapter for the existing Groq model."""

    def __init__(self):
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        self.client = Groq(api_key=api_key)

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        return response.choices[0].message.content or ""


def get_llm_provider() -> LLMProvider:
    """Select the configured LLM provider."""

    provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()

    if provider == "azure":
        from backend.core.llm.azure_client import AzureLLMClient
        return AzureLLMClient()

    if provider == "groq":
        return GroqLLMClient()

    raise ValueError(f"Unsupported LLM provider: {provider}")
