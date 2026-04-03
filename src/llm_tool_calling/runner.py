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


def _extract_product_ids(trace: list[dict]) -> list[int]:
    """Extract all product IDs found across all search_products calls in the trace."""
    ids = set()
    for step in trace:
        if step["tool"] == "search_products":
            for p in step["result"].get("products", []):
                if "id" in p:
                    ids.add(p["id"])
    return sorted(ids)


def evaluate_query(bq: BenchmarkQuery, client: OpenAI, model: str, provider_config) -> dict:
    """Run a query and evaluate the RESULT, not the tool path."""
    try:
        result = run_agent(bq.query, client=client, model=model, provider_config=provider_config)
    except Exception as e:
        log.error("Agent exception on %s: %s", bq.id, e, exc_info=True)
        return {
            "passed": False,
            "tools_called": [],
            "trace": [],
            "answer": "",
            "keywords_found": [],
            "keywords_missing": list(bq.answer_keywords),
            "found_product_ids": [],
            "missing_product_ids": list(bq.expected_product_ids),
            "iterations": 0,
            "duration_ms": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "error": f"Agent error: {e}",
        }

    answer_lower = result.answer.lower()

    # Check keywords in answer
    keywords_found = [k for k in bq.answer_keywords if k.lower() in answer_lower]
    keywords_missing = [k for k in bq.answer_keywords if k.lower() not in answer_lower]

    # Check expected products in trace
    found_ids = _extract_product_ids(result.trace)
    missing_product_ids = [pid for pid in bq.expected_product_ids if pid not in found_ids]

    keywords_ok = len(keywords_missing) == 0
    products_ok = len(missing_product_ids) == 0
    passed = keywords_ok and products_ok and result.error is None

    return {
        "passed": passed,
        "tools_called": [s["tool"] for s in result.trace],
        "trace": result.trace,
        "answer": result.answer[:3000],
        "keywords_found": keywords_found,
        "keywords_missing": keywords_missing,
        "found_product_ids": found_ids,
        "missing_product_ids": missing_product_ids,
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
                if r["keywords_missing"]:
                    print(f"         keywords missing: {r['keywords_missing']}", flush=True)
                if r["missing_product_ids"]:
                    print(f"         products missing: {r['missing_product_ids']}", flush=True)
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
                answer_keywords=bq.answer_keywords,
                keywords_found=r["keywords_found"],
                keywords_missing=r["keywords_missing"],
                expected_product_ids=bq.expected_product_ids,
                found_product_ids=r["found_product_ids"],
                missing_product_ids=r["missing_product_ids"],
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
