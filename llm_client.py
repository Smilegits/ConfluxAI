"""
LLM client — wraps OpenAI or Azure OpenAI for sync generation and streaming.
Set LLM_PROVIDER=azure in .env to use Azure OpenAI.
"""
from __future__ import annotations
import logging
from typing import Generator

from openai import AzureOpenAI, OpenAI
from config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        if settings.llm_provider == "azure":
            if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
                raise ValueError("Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in .env")
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )
            self.model = settings.azure_openai_deployment
            logger.info("LLMClient using Azure OpenAI (endpoint=%s, deployment=%s)",
                        settings.azure_openai_endpoint, self.model)
        else:
            if not settings.openai_api_key:
                raise ValueError("Set OPENAI_API_KEY in .env")
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
            logger.info("LLMClient using OpenAI (model=%s)", self.model)

    def generate(self, user_msg: str, system: str = "", max_tokens: int | None = None) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
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
            model=self.model,
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
            model=self.model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            messages=full_messages,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
