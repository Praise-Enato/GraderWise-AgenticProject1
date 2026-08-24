"""Tests for the model router.

Covers the pure selection logic and the api-key guard. Client construction
(get_llm) needs langchain + a real key and is not exercised here.
"""
import os

import pytest

from backend.src import llm as L
from backend.src.llm import ModelConfig


def test_text_tasks_route_to_deepseek():
    for task in ("grade", "feedback", "rubric", "eligibility"):
        cfg = L.get_model_config(task)
        assert cfg.provider == "deepseek"
        assert cfg.model == "deepseek-chat"
        assert cfg.api_key_env == "DEEPSEEK_API_KEY"
        assert cfg.supports_video is False


def test_multimodal_tasks_route_to_gemini():
    for task in ("vision", "video"):
        cfg = L.get_model_config(task)
        assert cfg.provider == "gemini"
        assert cfg.supports_vision is True
    assert L.get_model_config("video").supports_video is True


def test_unknown_task_raises_with_known_list():
    with pytest.raises(ValueError) as exc:
        L.get_model_config("nonsense")
    assert "unknown task" in str(exc.value)
    assert "grade" in str(exc.value)  # lists known tasks


def test_overrides_swap_model_without_touching_defaults():
    custom = ModelConfig(provider="openai", model="gpt-4o", api_key_env="OPENAI_API_KEY")
    cfg = L.get_model_config("grade", overrides={"grade": custom})
    assert cfg.model == "gpt-4o"
    # default table is unchanged for other callers
    assert L.get_model_config("grade").model == "deepseek-chat"


def test_known_tasks_listed():
    tasks = L.known_tasks()
    assert "grade" in tasks and "video" in tasks


def test_require_api_key_present(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    assert L.require_api_key(L.DEEPSEEK_TEXT) == "sk-test"


def test_require_api_key_missing_raises(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(RuntimeError) as exc:
        L.require_api_key(L.DEEPSEEK_TEXT)
    assert "DEEPSEEK_API_KEY" in str(exc.value)


def test_get_llm_missing_key_raises_before_import(monkeypatch):
    # Even without langchain installed, a missing key should be the error we get,
    # because require_api_key runs before the lazy provider import.
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(RuntimeError) as exc:
        L.get_llm("grade")
    assert "DEEPSEEK_API_KEY" in str(exc.value)


def test_with_model_copies_config():
    # Tests COPY SEMANTICS, so it compares the original against itself rather than
    # against a literal model id. It previously asserted the id, which meant
    # changing the default broke a test about immutability — and left the real
    # signal (an invalid default) looking like a stale assertion.
    before = L.GEMINI_MULTIMODAL.model
    cfg = L.with_model(L.GEMINI_MULTIMODAL, "gemini-2.5-pro")
    assert cfg.model == "gemini-2.5-pro"
    assert cfg.provider == "gemini"
    assert L.GEMINI_MULTIMODAL.model == before      # original untouched


@pytest.mark.skipif(os.getenv("GEMINI_MODEL") is not None,
                    reason="GEMINI_MODEL is set, so the code default is not in play")
def test_gemini_default_model_is_pinned():
    """The default Gemini id is pinned ON PURPOSE.

    If you change it, change it deliberately and confirm the new id is CALLABLE with
    a real request — not merely present in the models listing. `gemini-3-flash` was
    a default that 404s, and `gemini-2.5-flash` is listed but rejected for new keys.
    A wrong value here is invisible in tests and surfaces to judges as
    "Could not grade automatically".
    """
    assert L.GEMINI_MULTIMODAL.model == "gemini-3.5-flash-lite"


def test_gemini_config_uses_openai_compat_base():
    cfg = L.get_model_config("vision")
    assert cfg.provider == "gemini"
    assert cfg.base_url and "generativelanguage.googleapis.com" in cfg.base_url
