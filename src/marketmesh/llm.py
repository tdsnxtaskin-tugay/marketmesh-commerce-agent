"""Optional Azure OpenAI helper for natural-language reasoning narration.

The agent's *decisions* are deterministic (auditable). The LLM is only used to phrase
a human-friendly rationale. When Azure OpenAI is not configured, a deterministic
templated narration is returned so the demo never depends on a model.
"""

from __future__ import annotations

import logging

from .config import AzureOpenAIConfig, load_settings

logger = logging.getLogger("marketmesh.llm")


class Narrator:
    def __init__(self, config: AzureOpenAIConfig | None = None) -> None:
        self.config = config or load_settings().azure_openai
        self._client = None
        if self.config.configured:
            self._client = self._try_client()

    @property
    def live(self) -> bool:
        return self._client is not None

    def _try_client(self):  # pragma: no cover - requires live creds
        try:
            from openai import AzureOpenAI

            client = AzureOpenAI(
                api_key=self.config.api_key,
                azure_endpoint=self.config.endpoint,
                api_version=self.config.api_version,
            )
            logger.info("Azure OpenAI narration enabled (%s).", self.config.deployment)
            return client
        except Exception as exc:
            logger.warning("Azure OpenAI configured but init failed: %s. Using templated.", exc)
            return None

    def narrate(self, system: str, prompt: str, *, fallback: str) -> str:
        if self._client is None:
            return fallback
        try:  # pragma: no cover - requires live creds
            resp = self._client.chat.completions.create(
                model=self.config.deployment,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=400,
            )
            return resp.choices[0].message.content or fallback
        except Exception as exc:
            logger.warning("Azure OpenAI call failed: %s. Using templated narration.", exc)
            return fallback
