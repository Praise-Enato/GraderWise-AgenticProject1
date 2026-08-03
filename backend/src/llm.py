"""Model router — one interface, swap the model per task.

Replaces the duplicated ChatOpenAI/DeepSeek config that lived in both agent.py
and rubric_parser.py (eng review: DRY). It also implements the multimodal-
architecture decision: start minimal (DeepSeek for text tasks now; Gemini
configured for vision/video in Phase 1b), and keep every model swappable so you
can A/B a specialist against the measured agreement number without a rewrite.

The task->config selection is pure and unit-tested. Client construction lazily
imports the provider SDK, so importing this module (and testing the routing
logic) needs neither langchain nor API keys.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import Dict, Optional


@dataclass(frozen=True)
class ModelConfig:
    provider: str            # "deepseek" | "openai" | "gemini"
    model: str
    api_key_env: str
    base_url: Optional[str] = None
    supports_vision: bool = False
    supports_video: bool = False


# Task -> model. "Start minimal": DeepSeek (OpenAI-compatible) for all text work;
# Gemini for the multimodal tasks that DeepSeek cannot do. Swap by passing
# `overrides` to get_model_config / get_llm, or by editing this table.
DEEPSEEK_TEXT = ModelConfig(
    provider="deepseek", model="deepseek-chat",
    api_key_env="DEEPSEEK_API_KEY", base_url="https://api.deepseek.com",
)
GEMINI_MULTIMODAL = ModelConfig(
    provider="gemini",
    # Model id is env-overridable (GEMINI_MODEL) because Google retires model ids
    # over time and availability varies by API key/account — e.g. gemini-2.5-flash
    # was pulled for new keys ("no longer available to new users"). Set GEMINI_MODEL
    # in .env to swap without a code change. gemini-2.0-flash is a current GA default.
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    api_key_env="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",  # OpenAI-compatible endpoint
    supports_vision=True, supports_video=True,
)

DEFAULT_TASK_MODELS: Dict[str, ModelConfig] = {
    "grade": DEEPSEEK_TEXT,        # score the plan text (Phase 1a)
    "feedback": DEEPSEEK_TEXT,     # BYUMS-voice participant feedback
    "rubric": DEEPSEEK_TEXT,       # parse the rubric into structured criteria
    "eligibility": DEEPSEEK_TEXT,  # (optional) model-assisted DQ / AI-content check
    "vision": GEMINI_MULTIMODAL,   # read slide images (financials, license, bank) — Phase 1b
    "video": GEMINI_MULTIMODAL,    # grade the YouTube video (20%) — Phase 1b
}


def known_tasks() -> list:
    return sorted(DEFAULT_TASK_MODELS.keys())


def get_model_config(task: str, overrides: Optional[Dict[str, ModelConfig]] = None) -> ModelConfig:
    """Resolve a task to its ModelConfig. `overrides` lets a caller A/B a model
    without touching the default table."""
    table = dict(DEFAULT_TASK_MODELS)
    if overrides:
        table.update(overrides)
    if task not in table:
        raise ValueError(f"unknown task '{task}'. Known tasks: {sorted(table.keys())}")
    return table[task]


def require_api_key(config: ModelConfig) -> str:
    """Return the API key for a config, raising a clear error if it's missing.
    Pure and testable (reads os.environ)."""
    key = os.getenv(config.api_key_env)
    if not key:
        raise RuntimeError(
            f"Missing API key: set ${config.api_key_env} for provider "
            f"'{config.provider}' (model {config.model})."
        )
    return key


def get_llm(
    task: str,
    temperature: float = 0.0,
    max_retries: int = 3,
    request_timeout: int = 120,
    overrides: Optional[Dict[str, ModelConfig]] = None,
    **kwargs,
):
    """Construct a chat client for a task.

    DeepSeek, OpenAI, and Gemini all return a langchain ChatOpenAI (lazily
    imported), Gemini via its OpenAI-compatible endpoint. The API key is checked
    (require_api_key) before the client is constructed.
    """
    config = get_model_config(task, overrides)
    api_key = require_api_key(config)

    # DeepSeek, OpenAI, and Gemini all speak the OpenAI-compatible chat API, so
    # one ChatOpenAI path serves all three (Gemini via its OpenAI-compat base_url).
    if config.provider in ("deepseek", "openai", "gemini"):
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:  # pragma: no cover - depends on heavy optional dep
            raise ImportError(
                "langchain_openai is required. Install project requirements.txt."
            ) from e
        return ChatOpenAI(
            model=config.model,
            openai_api_key=api_key,
            openai_api_base=config.base_url,
            temperature=temperature,
            max_retries=max_retries,
            request_timeout=request_timeout,
            **kwargs,
        )

    raise ValueError(f"Unsupported provider: {config.provider}")  # pragma: no cover


def with_model(config: ModelConfig, model: str) -> ModelConfig:
    """Return a copy of a config with a different model id (for A/B testing)."""
    return replace(config, model=model)
