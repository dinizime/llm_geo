"""Benchmark runner: tests LLM models and evaluates results, not tool paths.

Usage:
    # Auto-detect provider from env vars
    python -m llm_tool_calling.runner --models gemma-4-27b-it

    # Explicit provider
    python -m llm_tool_calling.runner --provider google --models gemma-4-27b-it
    python -m llm_tool_calling.runner --provider openrouter --models google/gemma-4-31b-it

    # Filter queries
    python -m llm_tool_calling.runner --models gemma-4-27b-it --ids A01 C01
    python -m llm_tool_calling.runner --models gemma-4-27b-it --category "Rota"
"""

import argparse
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Force unbuffered UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

from .agent import run_agent
from .benchmark import BENCHMARK_QUERIES, BenchmarkQuery, get_queries
from .db import finish_run, init_db, insert_result, insert_run
from .providers import (
    PROVIDERS,
    create_client,
    detect_provider,
    get_default_model,
    list_providers,
)

log = logging.getLogger(__name__)


def _extract_product_ids(trace: list[dict]) -> set[int]:
    ids = set()
    for step in trace:
        if step["tool"] == "search_products":
            for p in step["result"].get("products", []):
                if "id" in p:
                    ids.add(p["id"])
    return ids


def _extract_feature_names(trace: list[dict]) -> set[str]:
    names = set()
    for step in trace:
        if step["tool"] in ("search_features", "features_along_route", "find_nearest"):
            for f in step["result"].get("features") or step["result"].get("nearest") or []:
                if "nome" in f:
                    names.add(f["nome"])
    return names


def _extract_feature_counts(trace: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for step in trace:
        if step["tool"] in ("search_features", "features_along_route", "find_nearest"):
            tipo = step.get("args", {}).get("tipo", "")
            total = step["result"].get("total", 0)
            counts[tipo] = counts.get(tipo, 0) + total
    return counts


def _extract_numeric(trace: list[dict]) -> dict[str, float]:
    values = {}
    for step in trace:
        result = step.get("result", {})
        for key in ("distance_km", "area_km2", "length_km"):
            if key in result and isinstance(result[key], (int, float)):
                values[key] = result[key]
    return values


def _extract_booleans(trace: list[dict]) -> dict[str, bool]:
    values = {}
    for step in trace:
        result = step.get("result", {})
        for key in ("intersects", "contains"):
            if key in result:
                values[key] = result[key]
    return values


def evaluate_query(bq: BenchmarkQuery, client: OpenAI, model: str, provider_config) -> dict:
    """Run a query and evaluate based on the trace (what the agent DID)."""
    try:
        result = run_agent(bq.query, client=client, model=model, provider_config=provider_config)
    except Exception as e:
        log.error("Agent exception on %s: %s", bq.id, e, exc_info=True)
        return {
            "passed": False, "tools_called": [], "trace": [], "answer": "",
            "checks": {"error": str(e)},
            "iterations": 0, "duration_ms": 0,
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "error": f"Agent error: {e}",
        }

    tools_called = [s["tool"] for s in result.trace]
    called_set = set(tools_called)
    checks = {}

    # 1. Expected tools (with equivalence for valid alternative paths)
    # Each entry: if expected tool X is missing, accept Y as equivalent
    TOOL_EQUIVALENCES = {
        "geocode": ["search_municipality"],
        "search_municipality": ["geocode"],
        "search_features": ["find_nearest", "features_along_route"],
        "find_nearest": ["search_features"],
        "compute_distance": ["compute_route"],
        "search_road": ["compute_route"],
    }
    tools_ok = True
    if bq.expected_tools:
        missing_tools = set()
        for tool in bq.expected_tools:
            if tool in called_set:
                continue
            alternatives = TOOL_EQUIVALENCES.get(tool, [])
            if any(alt in called_set for alt in alternatives):
                continue
            missing_tools.add(tool)
        tools_ok = len(missing_tools) == 0
        if not tools_ok:
            checks["missing_tools"] = sorted(missing_tools)

    # 2. Expected product IDs
    products_ok = True
    if bq.expected_product_ids:
        found_ids = _extract_product_ids(result.trace)
        missing_pids = [pid for pid in bq.expected_product_ids if pid not in found_ids]
        products_ok = len(missing_pids) == 0
        if not products_ok:
            checks["missing_product_ids"] = missing_pids

    # 3. Expected feature names (substring match)
    features_ok = True
    if bq.expected_feature_ids:
        found_names = _extract_feature_names(result.trace)
        found_lower = {n.lower() for n in found_names}
        missing_feats = [f for f in bq.expected_feature_ids if not any(f.lower() in n for n in found_lower)]
        features_ok = len(missing_feats) == 0
        if not features_ok:
            checks["missing_features"] = missing_feats

    # 4. Minimum feature counts
    min_feat_ok = True
    if bq.min_features:
        feat_counts = _extract_feature_counts(result.trace)
        for tipo, minimum in bq.min_features.items():
            actual = feat_counts.get(tipo, 0)
            if actual < minimum:
                min_feat_ok = False
                checks[f"min_{tipo}"] = f"expected>={minimum}, got {actual}"

    # 5. Numeric ranges
    numeric_ok = True
    if bq.expected_numeric:
        trace_nums = _extract_numeric(result.trace)
        for metric, (lo, hi) in bq.expected_numeric.items():
            if metric in trace_nums:
                val = trace_nums[metric]
                if not (lo <= val <= hi):
                    numeric_ok = False
                    checks[f"numeric_{metric}"] = f"expected [{lo},{hi}], got {val}"

    # 6. Boolean predicates
    boolean_ok = True
    if bq.expected_boolean:
        trace_bools = _extract_booleans(result.trace)
        for pred, expected in bq.expected_boolean.items():
            if pred in trace_bools and trace_bools[pred] != expected:
                boolean_ok = False
                checks[f"bool_{pred}"] = f"expected {expected}, got {trace_bools[pred]}"

    # 7. Answer keywords (case-insensitive substring match)
    keywords_ok = True
    if bq.answer_keywords:
        answer_lower = result.answer.lower()
        missing_kw = [kw for kw in bq.answer_keywords if kw.lower() not in answer_lower]
        keywords_ok = len(missing_kw) == 0
        if not keywords_ok:
            checks["missing_keywords"] = missing_kw

    # 8. Reject (out-of-scope / prompt injection): no tools should be called
    reject_ok = True
    if bq.reject:
        if tools_called:
            reject_ok = False
            checks["reject_violated"] = f"expected no tools, got {tools_called}"

    passed = (tools_ok and products_ok and features_ok and min_feat_ok
              and numeric_ok and boolean_ok and keywords_ok and reject_ok
              and result.error is None)

    return {
        "passed": passed,
        "tools_called": tools_called,
        "trace": result.trace,
        "answer": result.answer[:3000],
        "checks": checks,
        "iterations": result.iterations,
        "duration_ms": result.duration_ms,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "total_tokens": result.total_tokens,
        "error": result.error,
    }


def run_benchmark(
    models: list[str],
    queries: list[BenchmarkQuery],
    provider_id: str,
    delay: float = 1.0,
):
    print("Initializing database...", flush=True)
    init_db()

    print(f"Creating {PROVIDERS[provider_id].name} client...", flush=True)
    client, provider_config = create_client(provider_id)
    print("Ready.\n", flush=True)

    for model in models:
        run_id = str(uuid.uuid4())[:8]
        started_at = datetime.now(timezone.utc)
        model_label = f"{provider_id}/{model}"
        insert_run(run_id, model_label, started_at)

        total = len(queries)
        passed_count = 0
        failed_count = 0
        error_count = 0

        print(f"{'='*70}", flush=True)
        print(f"  Provider: {PROVIDERS[provider_id].name}", flush=True)
        print(f"  Model: {model}", flush=True)
        print(f"  Queries: {total}", flush=True)
        print(f"  Run ID: {run_id}", flush=True)
        print(f"{'='*70}\n", flush=True)

        for i, bq in enumerate(queries, 1):
            print(f"  [{i:3d}/{total}] {bq.id} ({bq.difficulty:6s}) {bq.query[:55]:<55s} ", end="", flush=True)

            r = evaluate_query(bq, client, model, provider_config)

            if r["error"] and r["error"].startswith("Agent error"):
                status = "ERROR"
                error_count += 1
            elif r["passed"]:
                status = "PASS"
                passed_count += 1
            else:
                status = "FAIL"
                failed_count += 1

            dur = r["duration_ms"] / 1000
            tok = r["total_tokens"]
            iters = r["iterations"]
            tools = " -> ".join(r["tools_called"]) if r["tools_called"] else "none"
            print(f" {status:5s} ({dur:.1f}s {tok}tok {iters}it) [{tools}]", flush=True)

            if not r["passed"]:
                for check_key, check_val in r.get("checks", {}).items():
                    print(f"         {check_key}: {check_val}", flush=True)
                if r["error"]:
                    print(f"         error: {r['error'][:200]}", flush=True)

            insert_result(
                run_id=run_id,
                query_id=bq.id,
                category=bq.category,
                difficulty=bq.difficulty,
                query_text=bq.query,
                model=model_label,
                passed=r["passed"],
                tools_called=r["tools_called"],
                trace=json.dumps(r["trace"], ensure_ascii=False, default=str),
                answer=r["answer"],
                checks=json.dumps(r.get("checks", {}), ensure_ascii=False),
                expected_product_ids=bq.expected_product_ids,
                iterations=r["iterations"],
                duration_ms=r["duration_ms"],
                prompt_tokens=r["prompt_tokens"],
                completion_tokens=r["completion_tokens"],
                total_tokens=r["total_tokens"],
                error=r["error"],
            )

            if i < total:
                time.sleep(delay)

        finished_at = datetime.now(timezone.utc)
        finish_run(run_id, finished_at, total, passed_count, failed_count, error_count)

        pass_rate = (passed_count / total * 100) if total > 0 else 0
        print(f"\n{'='*70}", flush=True)
        print(f"  RESULTS: {passed_count}/{total} passed ({pass_rate:.1f}%)", flush=True)
        print(f"  Failures: {failed_count}, Errors: {error_count}", flush=True)
        print(f"{'='*70}\n", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Run LLM tool calling benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available providers:\n{list_providers()}",
    )
    parser.add_argument("--provider", type=str, default=None,
                        help="LLM provider (auto-detected from env if omitted)")
    parser.add_argument("--models", nargs="+", default=None,
                        help="Model IDs to test (default: provider's default model)")
    parser.add_argument("--category", type=str, default=None, help="Filter by category")
    parser.add_argument("--difficulty", type=str, default=None, help="Filter: easy/medium/hard")
    parser.add_argument("--ids", nargs="+", default=None, help="Run specific query IDs")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between queries (seconds)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show debug logs from agent")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    # Silence noisy HTTP-level loggers even in verbose mode
    for noisy in ("openai", "httpcore", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Resolve provider
    provider_id = args.provider or detect_provider()
    provider_cfg = PROVIDERS[provider_id]
    print(f"LLM Tool Calling Benchmark", flush=True)
    print(f"Provider: {provider_cfg.name} ({provider_id})", flush=True)

    # Resolve models
    models = args.models or [get_default_model(provider_id)]
    print(f"Models: {', '.join(models)}", flush=True)

    # Resolve queries
    if args.ids:
        queries = [q for q in BENCHMARK_QUERIES if q.id in args.ids]
        if not queries:
            print(f"No queries found for IDs: {args.ids}", flush=True)
            sys.exit(1)
    else:
        queries = get_queries(category=args.category, difficulty=args.difficulty)

    if not queries:
        print("No queries matched the filters.", flush=True)
        sys.exit(1)

    print(f"Queries: {len(queries)}\n", flush=True)

    run_benchmark(models, queries, provider_id, delay=args.delay)
    print(f"Generate report: python -m llm_tool_calling.report", flush=True)


if __name__ == "__main__":
    main()
