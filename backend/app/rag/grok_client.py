"""
PetroNexus xAI / Grok API Client
Interfaces with the xAI API (Grok models) using standard OpenAI-compatible endpoints with httpx.
Features:
- Configurable timeout (default 30s)
- Exponential backoff retry on transient network errors, timeouts, 429 (rate-limit), and 5xx errors
- Fast-fail on non-retryable errors (401 invalid key, 403 insufficient credits)
- Zero-exposure logging: Never logs API keys, tokens, or private document/prompt content
- Grounded fallback mechanism when API key is unconfigured or credits are unavailable
"""
import os
import asyncio
from typing import Dict, Any, Optional
import httpx
from backend.app.config import settings
from backend.app.utils.logger import logger

class GrokClient:

    def __init__(self):
        self.base_url = "https://api.x.ai/v1"
        self._max_retries = 3
        self._timeout_seconds = 30.0

    @property
    def api_key(self) -> str:
        return os.getenv("XAI_API_KEY") or settings.XAI_API_KEY or ""

    @property
    def model(self) -> str:
        return os.getenv("GROK_MODEL") or settings.GROK_MODEL or "grok-2-latest"

    def is_configured(self) -> bool:
        k = self.api_key.strip()
        return bool(k and len(k) > 10)

    async def query(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Sends prompt to xAI Grok API with retry and backoff.
        Returns the assistant's reply text, or None if unavailable/errored.
        """
        result = await self.query_with_metadata(system_prompt, user_prompt)
        return result.get("content")

    async def query_with_metadata(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Sends prompt to xAI Grok with metadata tracking and error handling.
        Never logs sensitive prompt text or secrets.
        """
        if not self.is_configured():
            logger.info("xAI API key not configured. Operating in high-fidelity grounded synthesis mode.")
            return {"content": None, "model": self.model, "status": "NOT_CONFIGURED", "error": "API key not set"}

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
            "temperature": 0.2, # Low temperature for strict factual engineering accuracy
            "max_tokens": 1500
        }

        # Safe summary for audit logging (NEVER log the raw prompt containing private text)
        prompt_len = len(system_prompt) + len(user_prompt)
        logger.info(f"Dispatching query to xAI Grok (model: {self.model}, payload_len: {prompt_len} chars)")

        backoffs = [1.0, 2.0, 4.0]
        last_error = None

        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        actual_model = data.get("model", self.model)
                        logger.info(f"xAI Grok query completed successfully (model: {actual_model}, resp_len: {len(content)} chars)")
                        return {
                            "content": content,
                            "model": actual_model,
                            "status": "SUCCESS",
                            "error": None
                        }
                    
                    # Rate limit (429) - Retry with backoff or respect Retry-After
                    elif resp.status_code == 429:
                        retry_after = resp.headers.get("Retry-After")
                        delay = float(retry_after) if retry_after and retry_after.isdigit() else backoffs[attempt]
                        logger.warning(f"xAI Grok rate-limited (HTTP 429). Retrying in {delay}s (attempt {attempt+1}/{self._max_retries})...")
                        await asyncio.sleep(delay)
                        continue

                    # Server error (5xx) - Transient, retry
                    elif resp.status_code >= 500:
                        delay = backoffs[attempt]
                        logger.warning(f"xAI Grok server error (HTTP {resp.status_code}). Retrying in {delay}s (attempt {attempt+1}/{self._max_retries})...")
                        await asyncio.sleep(delay)
                        continue

                    # Non-retryable client errors (400, 401, 403, etc.) - Fast fail
                    else:
                        error_detail = "API error"
                        try:
                            err_json = resp.json()
                            error_detail = err_json.get("error", err_json.get("message", "Permission or authentication error"))
                        except Exception:
                            error_detail = f"HTTP {resp.status_code}"
                        
                        logger.error(f"xAI Grok client error (HTTP {resp.status_code}): {error_detail}")
                        return {
                            "content": None,
                            "model": self.model,
                            "status": f"HTTP_{resp.status_code}",
                            "error": str(error_detail)
                        }

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                delay = backoffs[attempt]
                logger.warning(f"xAI Grok network/timeout exception ({net_err.__class__.__name__}). Retrying in {delay}s (attempt {attempt+1}/{self._max_retries})...")
                last_error = str(net_err)
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"xAI Grok unexpected error ({e.__class__.__name__})")
                last_error = str(e)
                break

        return {
            "content": None,
            "model": self.model,
            "status": "FAILED",
            "error": last_error or "Max retries exceeded"
        }
