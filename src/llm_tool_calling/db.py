"""PostgreSQL storage for benchmark results."""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DSN = "postgresql://postgres:postgres@localhost:5432/postgres"


def get_conn(dsn: str | None = None):
    dsn = dsn or os.environ.get("DATABASE_URL", DEFAULT_DSN)
    return psycopg2.connect(dsn)


@contextmanager
def _cursor(dsn: str | None = None, dict_cursor: bool = False):
    conn = get_conn(dsn)
    try:
        factory = RealDictCursor if dict_cursor else None
        with conn.cursor(cursor_factory=factory) as cur:
            yield cur
        conn.commit()
    finally:
        conn.close()


def _fetch_all(query: str, params=None, dsn: str | None = None) -> list[dict]:
    with _cursor(dsn, dict_cursor=True) as cur:
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def init_db(dsn: str | None = None):
    with _cursor(dsn) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                id SERIAL PRIMARY KEY,
                run_id VARCHAR(36) UNIQUE NOT NULL,
                model VARCHAR(200) NOT NULL,
                started_at TIMESTAMP NOT NULL,
                finished_at TIMESTAMP,
                total_queries INT DEFAULT 0,
                passed INT DEFAULT 0,
                failed INT DEFAULT 0,
                errors INT DEFAULT 0,
                pass_rate FLOAT DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS benchmark_results (
                id SERIAL PRIMARY KEY,
                run_id VARCHAR(36) REFERENCES benchmark_runs(run_id),
                query_id VARCHAR(20) NOT NULL,
                category VARCHAR(100) NOT NULL,
                difficulty VARCHAR(20) NOT NULL,
                query_text TEXT NOT NULL,
                model VARCHAR(200) NOT NULL,
                passed BOOLEAN NOT NULL,

                -- What the agent did (full trace)
                tools_called TEXT[] NOT NULL DEFAULT '{}',
                trace JSONB NOT NULL DEFAULT '[]',
                answer TEXT DEFAULT '',

                -- Validation details
                checks JSONB NOT NULL DEFAULT '{}',
                expected_product_ids INT[] NOT NULL DEFAULT '{}',

                -- Metrics
                iterations INT DEFAULT 0,
                duration_ms INT DEFAULT 0,
                prompt_tokens INT DEFAULT 0,
                completion_tokens INT DEFAULT 0,
                total_tokens INT DEFAULT 0,

                error TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)


def insert_run(run_id: str, model: str, started_at, dsn: str | None = None):
    with _cursor(dsn) as cur:
        cur.execute(
            "INSERT INTO benchmark_runs (run_id, model, started_at) VALUES (%s, %s, %s)",
            (run_id, model, started_at),
        )


def finish_run(run_id: str, finished_at, total: int, passed: int, failed: int,
               errors: int, dsn: str | None = None):
    pass_rate = (passed / total * 100) if total > 0 else 0
    with _cursor(dsn) as cur:
        cur.execute(
            """UPDATE benchmark_runs
               SET finished_at=%s, total_queries=%s, passed=%s, failed=%s,
                   errors=%s, pass_rate=%s
               WHERE run_id=%s""",
            (finished_at, total, passed, failed, errors, pass_rate, run_id),
        )


def insert_result(*, run_id: str, query_id: str, category: str, difficulty: str,
                  query_text: str, model: str, passed: bool,
                  tools_called: list[str], trace: str, answer: str,
                  checks: str, expected_product_ids: list[int],
                  iterations: int, duration_ms: int,
                  prompt_tokens: int, completion_tokens: int, total_tokens: int,
                  error: str | None, dsn: str | None = None):
    with _cursor(dsn) as cur:
        cur.execute(
            """INSERT INTO benchmark_results
               (run_id, query_id, category, difficulty, query_text, model, passed,
                tools_called, trace, answer, checks, expected_product_ids,
                iterations, duration_ms, prompt_tokens, completion_tokens, total_tokens,
                error)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (run_id, query_id, category, difficulty, query_text, model, passed,
             tools_called, trace, answer, checks, expected_product_ids,
             iterations, duration_ms, prompt_tokens, completion_tokens, total_tokens,
             error),
        )


def get_all_runs(dsn: str | None = None) -> list[dict]:
    return _fetch_all("SELECT * FROM benchmark_runs ORDER BY started_at DESC", dsn=dsn)


def get_all_results(dsn: str | None = None) -> list[dict]:
    return _fetch_all(
        "SELECT * FROM benchmark_results ORDER BY model, query_id", dsn=dsn,
    )


def get_comparison_summary(dsn: str | None = None) -> list[dict]:
    return _fetch_all("""
        SELECT
            r.model, r.run_id, r.started_at, r.pass_rate,
            r.total_queries, r.passed, r.failed, r.errors,
            COALESCE(AVG(br.duration_ms), 0) as avg_duration_ms,
            COALESCE(AVG(br.iterations), 0) as avg_iterations,
            COALESCE(SUM(br.total_tokens), 0) as sum_tokens,
            COALESCE(AVG(br.total_tokens), 0) as avg_tokens
        FROM benchmark_runs r
        LEFT JOIN benchmark_results br ON r.run_id = br.run_id
        GROUP BY r.model, r.run_id, r.started_at, r.pass_rate,
                 r.total_queries, r.passed, r.failed, r.errors
        ORDER BY r.started_at DESC
    """, dsn=dsn)


def get_category_breakdown(dsn: str | None = None) -> list[dict]:
    return _fetch_all("""
        SELECT
            model, category,
            COUNT(*) as total,
            SUM(CASE WHEN passed THEN 1 ELSE 0 END) as passed,
            ROUND(100.0 * SUM(CASE WHEN passed THEN 1 ELSE 0 END) / COUNT(*), 1) as pass_rate,
            ROUND(AVG(duration_ms)) as avg_duration_ms,
            ROUND(AVG(total_tokens)) as avg_tokens
        FROM benchmark_results
        GROUP BY model, category
        ORDER BY model, category
    """, dsn=dsn)


def get_difficulty_breakdown(dsn: str | None = None) -> list[dict]:
    return _fetch_all("""
        SELECT
            model, difficulty,
            COUNT(*) as total,
            SUM(CASE WHEN passed THEN 1 ELSE 0 END) as passed,
            ROUND(100.0 * SUM(CASE WHEN passed THEN 1 ELSE 0 END) / COUNT(*), 1) as pass_rate,
            ROUND(AVG(total_tokens)) as avg_tokens
        FROM benchmark_results
        GROUP BY model, difficulty
        ORDER BY model, difficulty
    """, dsn=dsn)
