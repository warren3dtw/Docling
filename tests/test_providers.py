import json

import httpx
import pytest

from knowledge_builder.llm import DisabledSummaryProvider
from knowledge_builder.vlm import DisabledVisionProvider, _post_json


def test_model_timeout_is_retried(monkeypatch):
    calls = []

    def fake_post(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise httpx.ReadTimeout("slow")
        return httpx.Response(200, request=httpx.Request("POST", "http://local/v1/chat/completions"), json={"choices": [{"message": {"content": json.dumps({"ok": True})}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr("knowledge_builder.vlm.time.sleep", lambda _: None)
    assert _post_json("http://local/v1", "x", {}, 1, 1) == {"ok": True}
    assert len(calls) == 2


def test_invalid_json_has_readable_error(monkeypatch):
    response = httpx.Response(200, request=httpx.Request("POST", "http://local/v1/chat/completions"), json={"choices": [{"message": {"content": "not-json"}}]})
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: response)
    monkeypatch.setattr("knowledge_builder.vlm.time.sleep", lambda _: None)
    with pytest.raises(RuntimeError, match="2 次嘗試後失敗"):
        _post_json("http://local/v1", "x", {}, 1, 1)


def test_disabled_providers_never_fabricate(tmp_path):
    with pytest.raises(RuntimeError, match="VLM 未啟用"):
        DisabledVisionProvider().describe(tmp_path / "missing.png", "")
    with pytest.raises(RuntimeError, match="LLM 未啟用"):
        DisabledSummaryProvider().summarize("title", "content")
