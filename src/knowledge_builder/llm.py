from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from .vlm import _post_json


class SummaryResult(BaseModel):
    summary: str
    keywords: list[str] = Field(default_factory=list)
    search_questions: list[str] = Field(default_factory=list)


class SummaryProvider(ABC):
    @abstractmethod
    def summarize(self, title: str, content: str) -> SummaryResult: ...


class DisabledSummaryProvider(SummaryProvider):
    def summarize(self, title: str, content: str) -> SummaryResult:
        raise RuntimeError("LLM 未啟用；不會產生推測性摘要。")


class OpenAICompatibleSummaryProvider(SummaryProvider):
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 120, retries: int = 2):
        if not model:
            raise ValueError("SUMMARY_MODEL 未設定")
        self.base_url, self.api_key, self.model, self.timeout, self.retries = base_url.rstrip("/"), api_key, model, timeout, retries

    def summarize(self, title: str, content: str) -> SummaryResult:
        prompt = "忠實根據輸入內容，以繁體中文回傳 JSON：summary, keywords, search_questions。不可加入來源沒有的事實，也不可覆寫原文。\n標題：" + title + "\n內容：" + content
        body = {"model": self.model, "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": prompt}]}
        return SummaryResult.model_validate(_post_json(self.base_url, self.api_key, body, self.timeout, self.retries))


def provider_from_env(model: str | None, timeout: int, retries: int) -> SummaryProvider:
    return OpenAICompatibleSummaryProvider(os.getenv("OPENAI_COMPATIBLE_BASE_URL", "http://localhost:11434/v1"), os.getenv("OPENAI_COMPATIBLE_API_KEY", "ollama"), model or os.getenv("SUMMARY_MODEL", ""), timeout, retries)
