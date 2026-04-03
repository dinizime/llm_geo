"""LLM provider configurations. All use the OpenAI-compatible SDK."""

import os
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    env_key: str          # environment variable name for API key
    # Optional extra_body sent with every request (e.g. OpenRouter provider routing)
    extra_body: dict | None = None


PROVIDERS: dict[str, ProviderConfig] = {
    "google": ProviderConfig(
        name="Google AI Studio",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        env_key="GOOGLE_API_KEY",
    ),
    "openrouter": ProviderConfig(
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        env_key="OPENROUTER_API_KEY",
        extra_body={
            "provider": {
                "allow_fallbacks": True,
                "require_parameters": True,
                "sort": "throughput",
            },
        },
    ),
    "groq": ProviderConfig(
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        env_key="GROQ_API_KEY",
    ),
    "together": ProviderConfig(
        name="Together AI",
        base_url="https://api.together.xyz/v1",
        env_key="TOGETHER_API_KEY",
    ),
    "ollama": ProviderConfig(
        name="Ollama (local)",
        base_url="http://localhost:11434/v1",
        env_key="",  # no key needed
    ),
}

# Default models per provider (just suggestions, can be overridden)
DEFAULT_MODELS: dict[str, str] = {
    "google": "gemma-4-31b-it",
    "openrouter": "google/gemma-4-31b-it",
    "groq": "llama-3.3-70b-versatile",
    "together": "google/gemma-2-27b-it",
    "ollama": "gemma3:12b",
}


def detect_provider() -> str:
    """Auto-detect provider from available env vars, in priority order."""
    for provider_id in ["google", "openrouter", "groq", "together"]:
        cfg = PROVIDERS[provider_id]
        if os.environ.get(cfg.env_key):
            return provider_id
    return "ollama"


def create_client(provider_id: str | None = None) -> tuple[OpenAI, ProviderConfig]:
    """Create an OpenAI client for the given provider. Returns (client, config)."""
    if provider_id is None:
        provider_id = detect_provider()

    if provider_id not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unknown provider '{provider_id}'. Available: {available}")

    cfg = PROVIDERS[provider_id]

    api_key = os.environ.get(cfg.env_key, "") if cfg.env_key else "ollama"
    if cfg.env_key and not api_key:
        raise RuntimeError(
            f"{cfg.env_key} environment variable is not set (required for {cfg.name})."
        )

    client = OpenAI(
        base_url=cfg.base_url,
        api_key=api_key,
        max_retries=0,  # We handle retries ourselves
    )
    return client, cfg


def get_default_model(provider_id: str) -> str:
    return DEFAULT_MODELS.get(provider_id, "gemma-4-27b-it")


def list_providers() -> str:
    """Pretty-print available providers for CLI help."""
    lines = []
    for pid, cfg in PROVIDERS.items():
        key_status = ""
        if cfg.env_key:
            has_key = bool(os.environ.get(cfg.env_key))
            key_status = f" [{cfg.env_key}: {'set' if has_key else 'NOT SET'}]"
        else:
            key_status = " [no key needed]"
        default_model = DEFAULT_MODELS.get(pid, "?")
        lines.append(f"  {pid:12s} {cfg.name:20s} default={default_model}{key_status}")
    return "\n".join(lines)
