from __future__ import annotations

import base64
import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path

import httpx
from pydantic import BaseModel, Field


class VisionResult(BaseModel):
    image_type: str = "unknown"
    caption_vlm: str
    visible_text: list[str] = Field(default_factory=list)
    search_terms: list[str] = Field(default_factory=list)
    confidence_note: str = ""


class VisionProvider(ABC):
    @abstractmethod
    def describe(self, image: Path, context: str) -> VisionResult: ...


class DisabledVisionProvider(VisionProvider):
    def describe(self, image: Path, context: str) -> VisionResult:
        raise RuntimeError("VLM 未啟用；不會產生推測性圖片描述。")


class OpenAICompatibleVisionProvider(VisionProvider):
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 120, retries: int = 2):
        if not model:
            raise ValueError("VISION_MODEL 未設定")
        self.base_url, self.api_key, self.model, self.timeout, self.retries = base_url.rstrip("/"), api_key, model, timeout, retries

    def describe(self, image: Path, context: str) -> VisionResult:
        payload = base64.b64encode(image.read_bytes()).decode()
        prompt = "只描述圖片中可直接觀察的內容，區分觀察與推論；保留可辨識技術文字、數值與單位，絕不可捏造。無法判讀時明說限制。回傳 JSON：image_type, caption_vlm, visible_text, search_terms, confidence_note。\n鄰近文字：" + context[:4000]
        body = {"model": self.model, "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{payload}"}}]}]}
        return VisionResult.model_validate(_post_json(self.base_url, self.api_key, body, self.timeout, self.retries))


def _post_json(base_url: str, api_key: str, body: dict, timeout: int, retries: int) -> dict:
    error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = httpx.post(f"{base_url}/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json=body, timeout=timeout)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except (httpx.RequestError, httpx.HTTPStatusError, KeyError, json.JSONDecodeError) as exc:
            error = exc
            if attempt < retries:
                time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"模型請求在 {retries + 1} 次嘗試後失敗：{error}") from error


def provider_from_env(model: str | None, timeout: int, retries: int) -> VisionProvider:
    return OpenAICompatibleVisionProvider(os.getenv("OPENAI_COMPATIBLE_BASE_URL", "http://localhost:11434/v1"), os.getenv("OPENAI_COMPATIBLE_API_KEY", "ollama"), model or os.getenv("VISION_MODEL", ""), timeout, retries)
