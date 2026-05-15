"""
LLM client — wraps Azure OpenAI for sync generation and streaming.
"""
from __future__ import annotations
import logging
from typing import Generator

from openai import AzureOpenAI
from config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        if not settings.azure_api_key:
            raise ValueError("Set AZURE_OPENAI_API_KEY in .env")
        if not settings.azure_endpoint:
            raise ValueError("Set AZURE_OPENAI_ENDPOINT in .env")
        self.client = AzureOpenAI(
            api_key=settings.azure_api_key,
            azure_endpoint=settings.azure_endpoint,
            api_version=settings.azure_api_version,
        )
        self.deployment = settings.azure_deployment

    def generate(self, user_msg: str, system: str = "", max_tokens: int | None = None) -> str:
        resp = self.client.chat.completions.create(
            model=self.deployment,
            max_tokens=max_tokens or settings.max_tokens,
            temperature=settings.temperature,
            messages=[
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": user_msg},
            ],
        )
        return resp.choices[0].message.content or ""

    def generate_with_history(self, messages: list[dict], system: str = "") -> str:
        full_messages = [
            {"role": "system", "content": system or "You are a helpful assistant."},
            *messages,
        ]
        resp = self.client.chat.completions.create(
            model=self.deployment,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            messages=full_messages,
        )
        return resp.choices[0].message.content or ""

    def stream_with_history(self, messages: list[dict], system: str = "") -> Generator[str, None, None]:
        full_messages = [
            {"role": "system", "content": system or "You are a helpful assistant."},
            *messages,
        ]
        stream = self.client.chat.completions.create(
            model=self.deployment,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            messages=full_messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
