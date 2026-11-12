
import os
from pathlib import Path

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from openai import OpenAI


# Load local backend configuration.
# Existing environment variables take precedence.
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)


class AzureLLMClient:
    """Microsoft Foundry model client using Entra ID authentication."""

    def __init__(self):
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("MODEL_DEPLOYMENT")

        if not endpoint or not deployment:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT and MODEL_DEPLOYMENT "
                "must be configured."
            )

        credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=True
        )

        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default",
        )

        self.client = OpenAI(
            base_url=endpoint.rstrip("/") + "/",
            api_key=token_provider,
            timeout=30.0,
            max_retries=2,
        )

        self.deployment = deployment

    def complete(self, prompt: str) -> str:
        """Generate a text response from the configured deployment."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise AI assistant.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return response.choices[0].message.content or ""
