"""
PetroNexus xAI / Grok API Client
Interfaces with the xAI API (Grok models) using standard OpenAI-compatible endpoints or httpx.
Provides automated fallback to grounded local deterministic responses if the API key is absent.
"""
from typing import Dict, Any, Optional
import httpx
from backend.app.config import settings
from backend.app.utils.logger import logger

class GrokClient:

    def __init__(self):
        self.api_key = settings.XAI_API_KEY
        self.base_url = "https://api.x.ai/v1"
        self.model = settings.GROK_MODEL

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    async def query(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Sends query to Grok API using async HTTP.
        """
        if not self.is_configured():
            logger.info("xAI API key not configured. Operating in High-Fidelity Grounded Demo Mode.")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2, # Low temperature for strict factual accuracy
            "max_tokens": 1500
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"Grok API error HTTP {resp.status_code}: {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"Grok connection exception: {e}")
            return None
