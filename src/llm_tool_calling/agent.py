"""Simple while-loop agent that calls LLM via OpenAI-compatible APIs."""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Callable

from openai import APIStatusError, OpenAI, RateLimitError

from .geometry_store import GeometryStore
from .providers import ProviderConfig, create_client as _create_client, detect_provider, get_default_model
from .tool_handlers import ToolHandlers
from .tools import TOOLS

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Voce e um assistente de busca do Geoportal do Exercito Brasileiro.
Seu trabalho e interpretar perguntas em linguagem natural sobre produtos geoespaciais
(cartas topograficas, ortoimagens, MDS, MDT, imagens de drone/satelite) e usar as tools
disponiveis para encontra-los.

Regras:
- Sempre resolva a geometria de busca ANTES de chamar search_products.
  Use geocode, search_municipality, search_state, search_named_region, etc.
- O LLM nunca ve coordenadas GeoJSON. Trabalhe com geometry_ref.
- Para buscas ao longo de rotas: geocode os pontos, compute_route, buffer, search_products.
- Para "melhor escala": search_products depois rank_by_scale.
- Para "mais recente": search_products depois rank_by_date.
- Para fronteiras: search_border, buffer, intersect com territorio, search_products.
- Se o toponimo e ambiguo, use autocomplete_placename.
- Para perguntas conceituais (ex: "o que e MDS?"), use explain_product_type.
"""

MAX_ITERATIONS = 10
MAX_RETRIES = 4
RETRY_BASE_DELAY = 5  # seconds, doubles each retry: 5, 10, 20, 40


@dataclass
class AgentResult:
    answer: str
    trace: list[dict] = field(default_factory=list)
    iterations: int = 0
    duration_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    error: str | None = None


def _parse_tool_args(raw: str) -> dict:
    """Parse tool arguments, handling malformed JSON from some models."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    depth = 0
    for i, ch in enumerate(raw):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[: i + 1])
                except json.JSONDecodeError:
                    break
    return {}


def _emit(on_event: Callable | None, event: dict):
    """Safely emit an event via callback."""
    if on_event:
        try:
            on_event(event)
        except Exception:
            pass


def run_agent(
    query: str,
    client: OpenAI | None = None,
    model: str | None = None,
    provider_config: ProviderConfig | None = None,
    on_event: Callable[[dict], None] | None = None,
) -> AgentResult:
    if client is None:
        client, provider_config = _create_client()

    if model is None:
        provider_id = detect_provider()
        model = os.environ.get("OPENROUTER_MODEL") or get_default_model(provider_id)

    extra_body = provider_config.extra_body if provider_config else None

    geometry_store = GeometryStore()
    handlers = ToolHandlers(geometry_store)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    trace: list[dict] = []
    t0 = time.perf_counter()
    prompt_tokens = 0
    completion_tokens = 0

    for iteration in range(MAX_ITERATIONS):
        log.debug("iter=%d calling %s (%d messages)", iteration + 1, model, len(messages))
        _emit(on_event, {
            "type": "thinking",
            "iteration": iteration + 1,
            "message": "Analisando a pergunta..." if iteration == 0 else "Processando resultados...",
        })

        response = None
        for attempt in range(MAX_RETRIES):
            try:
                kwargs = dict(
                    model=model,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                )
                if extra_body:
                    kwargs["extra_body"] = extra_body
                response = client.chat.completions.create(**kwargs)
                break
            except RateLimitError as e:
                retry_after = getattr(e.response, "headers", {}).get("retry-after")
                wait = float(retry_after) if retry_after else RETRY_BASE_DELAY * (2 ** (attempt + 1))
                log.warning("  rate-limited (attempt %d/%d), waiting %.0fs", attempt + 1, MAX_RETRIES, wait)
                _emit(on_event, {"type": "retry", "message": f"Rate limit, aguardando {wait:.0f}s...", "attempt": attempt + 1})
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)
                    continue
                log.error("  rate-limited, giving up after %d retries", MAX_RETRIES)
                return AgentResult(
                    answer="", trace=trace, iterations=iteration + 1,
                    duration_ms=int((time.perf_counter() - t0) * 1000),
                    prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    error=f"Rate limited at iteration {iteration + 1} after {MAX_RETRIES} retries: {e}",
                )
            except APIStatusError as e:
                if e.status_code in (401, 402, 403):
                    log.error("  auth/billing failed (HTTP %d): %s", e.status_code, e.message)
                    return AgentResult(
                        answer="", trace=trace, iterations=iteration + 1,
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                        total_tokens=prompt_tokens + completion_tokens,
                        error=f"Auth/billing failed (HTTP {e.status_code}): {e.message}",
                    )
                wait = RETRY_BASE_DELAY * (2 ** attempt)
                log.warning("  HTTP %d (attempt %d/%d), waiting %.0fs: %s",
                            e.status_code, attempt + 1, MAX_RETRIES, wait, e.message)
                _emit(on_event, {"type": "retry", "message": f"Erro HTTP {e.status_code}, tentando novamente...", "attempt": attempt + 1})
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)
                    continue
                log.error("  HTTP %d, giving up after %d retries", e.status_code, MAX_RETRIES)
                return AgentResult(
                    answer="", trace=trace, iterations=iteration + 1,
                    duration_ms=int((time.perf_counter() - t0) * 1000),
                    prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    error=f"API error (HTTP {e.status_code}) at iteration {iteration + 1}: {e.message}",
                )
            except Exception as e:
                wait = RETRY_BASE_DELAY * (2 ** attempt)
                log.warning("  error (attempt %d/%d), waiting %.0fs: %s",
                            attempt + 1, MAX_RETRIES, wait, e)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)
                    continue
                log.error("  giving up after %d retries: %s", MAX_RETRIES, e)
                return AgentResult(
                    answer="", trace=trace, iterations=iteration + 1,
                    duration_ms=int((time.perf_counter() - t0) * 1000),
                    prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    error=f"API error at iteration {iteration + 1}: {e}",
                )

        if response is None or not response.choices:
            raw = getattr(response, "model_dump", lambda: None)()
            log.error("  empty response at iter %d: %s", iteration + 1, raw)
            return AgentResult(
                answer="", trace=trace, iterations=iteration + 1,
                duration_ms=int((time.perf_counter() - t0) * 1000),
                prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                error=f"Empty response at iteration {iteration + 1}: {raw}",
            )

        if response.usage:
            prompt_tokens += response.usage.prompt_tokens
            completion_tokens += response.usage.completion_tokens

        choice = response.choices[0]
        log.debug("  finish_reason=%s tool_calls=%d tokens=%d+%d",
                   choice.finish_reason,
                   len(choice.message.tool_calls or []),
                   response.usage.prompt_tokens if response.usage else 0,
                   response.usage.completion_tokens if response.usage else 0)

        if choice.finish_reason == "stop" or not choice.message.tool_calls:
            elapsed = int((time.perf_counter() - t0) * 1000)
            log.debug("  done in %d iterations, %dms, %d tokens",
                       iteration + 1, elapsed, prompt_tokens + completion_tokens)
            result = AgentResult(
                answer=choice.message.content or "",
                trace=trace, iterations=iteration + 1, duration_ms=elapsed,
                prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )
            _emit(on_event, {"type": "done"})
            return result

        # Rebuild assistant message with sanitized tool call arguments
        sanitized_tool_calls = []
        for tc in choice.message.tool_calls:
            sanitized_tool_calls.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": json.dumps(_parse_tool_args(tc.function.arguments)),
                },
            })
        messages.append({
            "role": "assistant",
            "content": choice.message.content or "",
            "tool_calls": sanitized_tool_calls,
        })

        for tc in choice.message.tool_calls:
            func_name = tc.function.name
            func_args = _parse_tool_args(tc.function.arguments)

            _emit(on_event, {
                "type": "tool_start",
                "tool": func_name,
                "args": func_args,
            })

            try:
                result = handlers.dispatch(func_name, func_args)
            except Exception as e:
                log.warning("  tool %s raised: %s", func_name, e)
                result = {"error": f"Tool execution failed: {e}"}

            log.debug("  tool %s(%s) -> %s",
                       func_name,
                       ", ".join(f"{k}={v!r}" for k, v in func_args.items()),
                       json.dumps(result, ensure_ascii=False)[:200])

            trace.append({
                "tool": func_name,
                "args": func_args,
                "result": result,
            })

            _emit(on_event, {
                "type": "tool_result",
                "tool": func_name,
                "args": func_args,
                "result": result,
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    log.warning("  max iterations (%d) reached", MAX_ITERATIONS)
    return AgentResult(
        answer="", trace=trace, iterations=MAX_ITERATIONS,
        duration_ms=int((time.perf_counter() - t0) * 1000),
        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        error="Max iterations reached",
    )
