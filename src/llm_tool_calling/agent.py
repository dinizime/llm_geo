"""Simple while-loop agent that calls LLM via OpenRouter and executes tools."""

import json
import os
import time
from dataclasses import dataclass, field

from openai import OpenAI

from .geometry_store import GeometryStore
from .tool_handlers import ToolHandlers
from .tools import TOOLS

SYSTEM_PROMPT = """\
Você é um assistente de busca do Geoportal do Exército Brasileiro.
Seu trabalho é interpretar perguntas em linguagem natural sobre produtos geoespaciais
(cartas topográficas, ortoimagens, MDS, MDT, imagens de drone/satélite) e usar as tools
disponíveis para encontrá-los.

Regras:
- Sempre resolva a geometria de busca ANTES de chamar search_products.
  Use geocode, search_municipality, search_state, search_named_region, etc.
- O LLM nunca vê coordenadas GeoJSON. Trabalhe com geometry_ref.
- Para buscas ao longo de rotas: geocode os pontos, compute_route, buffer, search_products.
- Para "melhor escala": search_products depois rank_by_scale.
- Para "mais recente": search_products depois rank_by_date.
- Para fronteiras: search_border, buffer, intersect com território, search_products.
- Se o topônimo é ambíguo, use autocomplete_placename.
- Para perguntas conceituais (ex: "o que é MDS?"), use explain_product_type.
"""

DEFAULT_MODEL = "google/gemma-4-31b-it"
MAX_ITERATIONS = 10


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


def create_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def _parse_tool_args(raw: str) -> dict:
    """Parse tool arguments, handling malformed JSON from some models."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Some models concatenate multiple JSON objects — extract the first one
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


def run_agent(query: str, client: OpenAI | None = None, model: str | None = None) -> AgentResult:
    if client is None:
        client = create_client()

    model = model or os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
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
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            return AgentResult(
                answer="",
                trace=trace,
                iterations=iteration + 1,
                duration_ms=int((time.perf_counter() - t0) * 1000),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                error=f"API error at iteration {iteration + 1}: {e}",
            )

        if response.usage:
            prompt_tokens += response.usage.prompt_tokens
            completion_tokens += response.usage.completion_tokens

        choice = response.choices[0]

        if choice.finish_reason == "stop" or not choice.message.tool_calls:
            return AgentResult(
                answer=choice.message.content or "",
                trace=trace,
                iterations=iteration + 1,
                duration_ms=int((time.perf_counter() - t0) * 1000),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )

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

            try:
                result = handlers.dispatch(func_name, func_args)
            except Exception as e:
                result = {"error": f"Tool execution failed: {e}"}

            trace.append({
                "tool": func_name,
                "args": func_args,
                "result": result,
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    return AgentResult(
        answer="",
        trace=trace,
        iterations=MAX_ITERATIONS,
        duration_ms=int((time.perf_counter() - t0) * 1000),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        error="Max iterations reached",
    )
