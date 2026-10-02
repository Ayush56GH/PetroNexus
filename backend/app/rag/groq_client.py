"""
PetroNexus Groq API Client
Interfaces with the Groq API using standard OpenAI-compatible endpoints with httpx.
Features:
- Configurable timeout (default 30s)
- Exponential backoff retry on transient network errors, timeouts, 429 (rate-limit), and 5xx errors
- Fast-fail on non-retryable errors (401 invalid key, 403 forbidden)
- Model availability verification against GET https://api.groq.com/openai/v1/models
- Zero-exposure logging: Never logs API keys, tokens, or private document/prompt content
- Grounded fallback mechanism when API key is unconfigured or unavailable
"""
import os
import asyncio
from typing import Dict, Any, Optional, List, Tuple
import httpx
from backend.app.config import settings
from backend.app.utils.logger import logger

class GroqClient:

    def __init__(self):
        self.base_url = "https://api.groq.com/openai/v1"
        self._max_retries = 3
        self._timeout_seconds = 30.0

    @property
    def api_key(self) -> str:
        return os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY or ""

    @property
    def model(self) -> str:
        return os.getenv("GROQ_MODEL") or settings.GROQ_MODEL or "openai/gpt-oss-120b"

    def is_configured(self) -> bool:
        k = self.api_key.strip()
        return bool(k and len(k) > 10)

    async def list_available_models(self) -> Tuple[bool, List[str], Optional[str]]:
        """
        Queries GET /models to check what models are accessible with the configured key.
        Returns (success: bool, model_ids: list, error_message: str|None).
        """
        if not self.is_configured():
            return False, [], "GROQ_API_KEY is not configured"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                    logger.info(f"Groq API returned {len(models)} accessible models.")
                    return True, models, None
                elif resp.status_code in (401, 403):
                    return False, [], f"Authentication error (HTTP {resp.status_code}): Invalid or unauthorized API key"
                else:
                    return False, [], f"Groq API error (HTTP {resp.status_code}): {resp.text[:200]}"
        except Exception as e:
            return False, [], f"Connection error checking Groq models: {str(e)}"

    async def verify_model_available(self, target_model: Optional[str] = None) -> Tuple[bool, Optional[str], List[str]]:
        """
        Verifies whether the target_model (or self.model) is available to the API key.
        Returns (is_available: bool, error_detail: str|None, available_models: list).
        """
        m = target_model or self.model
        ok, models, err = await self.list_available_models()
        if not ok:
            return False, err, []

        if m in models:
            return True, None, models
        else:
            return False, f"Configured model '{m}' is not found in accessible models for this account.", models

    async def query(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Sends prompt to Groq API with retry and backoff.
        Returns the assistant's reply text, or None if unavailable/errored.
        """
        result = await self.query_with_metadata(system_prompt, user_prompt)
        return result.get("content")

    async def query_with_metadata(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Sends prompt to Groq with metadata tracking and error handling.
        Never logs sensitive prompt text or secrets.
        """
        if not self.is_configured():
            logger.info("Groq API key not configured. Operating in high-fidelity grounded synthesis mode.")
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
        logger.info(f"Dispatching query to Groq (model: {self.model}, payload_len: {prompt_len} chars)")

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
                        logger.info(f"Groq query completed successfully (model: {actual_model}, resp_len: {len(content)} chars)")
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
                        logger.warning(f"Groq rate-limited (HTTP 429). Retrying in {delay}s (attempt {attempt+1}/{self._max_retries})...")
                        await asyncio.sleep(delay)
                        continue

                    # Server error (5xx) - Transient, retry
                    elif resp.status_code >= 500:
                        delay = backoffs[attempt]
                        logger.warning(f"Groq server error (HTTP {resp.status_code}). Retrying in {delay}s (attempt {attempt+1}/{self._max_retries})...")
                        await asyncio.sleep(delay)
                        continue

                    # Non-retryable client errors (400, 401, 403, 404, etc.) - Fast fail
                    else:
                        error_detail = "API error"
                        try:
                            err_json = resp.json()
                            error_detail = err_json.get("error", {}).get("message", err_json.get("message", f"HTTP {resp.status_code}"))
                        except Exception:
                            error_detail = f"HTTP {resp.status_code}"

                        logger.error(f"Groq client error (HTTP {resp.status_code}): {error_detail}")
                        return {
                            "content": None,
                            "model": self.model,
                            "status": f"HTTP_{resp.status_code}",
                            "error": str(error_detail)
                        }

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                delay = backoffs[attempt]
                logger.warning(f"Groq network/timeout exception ({net_err.__class__.__name__}). Retrying in {delay}s (attempt {attempt+1}/{self._max_retries})...")
                last_error = str(net_err)
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Groq unexpected error ({e.__class__.__name__})")
                last_error = str(e)
                break

        return {
            "content": None,
            "model": self.model,
            "status": "FAILED",
            "error": last_error or "Max retries exceeded"
        }
