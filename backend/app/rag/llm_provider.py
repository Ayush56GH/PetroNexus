"""
PetroNexus Unified LLM Provider Factory
Dispatches LLM generation requests to either Groq or xAI based on configuration.
Preserves existing xAI implementation while enabling Groq as the active generation provider.
"""
from typing import Dict, Any, Optional
import os
from backend.app.config import settings
from backend.app.rag.groq_client import GroqClient
from backend.app.rag.grok_client import GrokClient
from backend.app.utils.logger import logger

class LLMProvider:
    """
    Unified LLM client interface for PetroNexus.
    Supports LLM_PROVIDER="groq" and LLM_PROVIDER="xai".
    """
    def __init__(self):
        self.groq_client = GroqClient()
        self.grok_client = GrokClient()

    @property
    def provider_name(self) -> str:
        return os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER).lower().strip()

    def get_active_client(self):
        if self.provider_name == "xai":
            return self.grok_client
        # Default is groq
        return self.groq_client

    def is_configured(self) -> bool:
        return self.get_active_client().is_configured()

    @property
    def model(self) -> str:
        return self.get_active_client().model

    async def query_with_metadata(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Routes the prompt to the configured LLM provider (Groq or xAI).
        """
        client = self.get_active_client()
        logger.info(f"Routing query to LLM provider '{self.provider_name}' (model: {client.model})")
        return await client.query_with_metadata(system_prompt, user_prompt)
