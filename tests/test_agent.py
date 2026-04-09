"""Integration tests: send queries to OpenRouter and validate tool call sequences.

These tests require OPENROUTER_API_KEY set in the environment.
Run with: pytest tests/test_agent.py -v

Each test checks which tools the LLM chose to call and whether the sequence
matches the expected pattern. We use flexible matching:
- "required_tools": tools that MUST appear (order-insensitive)
- "required_sequence": ordered subsequence that must appear in order
- "forbidden_tools": tools that must NOT appear
"""

import os

import pytest

from llm_tool_calling.agent import run_agent

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)


def tool_names(result) -> list[str]:
    return [step["tool"] for step in result.trace]


def assert_tools_present(result, required: list[str], label: str = ""):
    names = tool_names(result)
    missing = [t for t in required if t not in names]
    assert not missing, f"[{label}] Missing tools {missing}. Got: {names}"


def assert_tools_absent(result, forbidden: list[str], label: str = ""):
    names = tool_names(result)
    found = [t for t in forbidden if t in names]
    assert not found, f"[{label}] Forbidden tools found {found}. Got: {names}"


def assert_ordered_subsequence(result, sequence: list[str], label: str = ""):
    """Check that the given tools appear in order (not necessarily consecutive)."""
    names = tool_names(result)
    idx = 0
    for tool in sequence:
        try:
            idx = names.index(tool, idx) + 1
        except ValueError:
            pytest.fail(f"[{label}] Expected ordered sequence {sequence}, but '{tool}' not found after position {idx}. Got: {names}")


# ── Category A: Simple location ──


class TestCategoryA:
    def test_p01_cartas_alecrim(self):
        """Cartas topográficas de melhor escala em Alecrim"""
        r = run_agent("Cartas topográficas de melhor escala possível em Alecrim")
        assert r.error is None
        assert_tools_present(r, ["search_products"], "P01")
        names = tool_names(r)
        assert "geocode" in names or "search_municipality" in names, f"P01: needs location resolution. Got: {names}"

    def test_p02_drone_itaipu(self):
        """Imagem de drone de Itaipu"""
        r = run_agent("Imagem de drone de Itaipu")
        assert r.error is None
        assert_tools_present(r, ["search_products"], "P02")
        names = tool_names(r)
        assert "geocode" in names or "search_municipality" in names, f"P02: needs geocode. Got: {names}"

    def test_p03_modelos_3d_brasilia(self):
        """Modelos 3D de Brasília"""
        r = run_agent("Modelos 3D de Brasília")
        assert r.error is None
        assert_tools_present(r, ["search_products"], "P03")
        names = tool_names(r)
        assert "search_municipality" in names or "geocode" in names, f"P03: needs location. Got: {names}"


# ── Category B: Informal region ──


class TestCategoryB:
    def test_p05_mds_serra_gaucha(self):
        """MDS da Serra Gaúcha"""
        r = run_agent("MDS da Serra Gaúcha")
        assert r.error is None
        assert_tools_present(r, ["search_named_region", "search_products"], "P05")

    def test_p06_mdt_pantanal(self):
        """MDT do Pantanal"""
        r = run_agent("MDT do Pantanal")
        assert r.error is None
        assert_tools_present(r, ["search_named_region", "search_products"], "P06")


# ── Category C: Route ──


class TestCategoryC:
    def test_p09_cartas_rota(self):
        """Cartas topográficas ao longo da rota entre Florianópolis e Porto Alegre"""
        r = run_agent("Cartas topográficas ao longo da rota entre Florianópolis e Porto Alegre")
        assert r.error is None
        assert_tools_present(r, ["geocode", "search_products"], "P09")
        names = tool_names(r)
        assert "compute_route" in names or "buffer" in names, f"P09: needs route/buffer. Got: {names}"


# ── Category D: Temporal filter ──


class TestCategoryD:
    def test_p13_mais_recente_manaus(self):
        """Produto mais recente de qualquer tipo sobre Manaus"""
        r = run_agent("Produto mais recente de qualquer tipo sobre Manaus")
        assert r.error is None
        assert_tools_present(r, ["search_products"], "P13")
        names = tool_names(r)
        assert "search_municipality" in names or "geocode" in names, f"P13: needs location. Got: {names}"


# ── Category E: Military installation ──


class TestCategoryE:
    def test_p14_carta_8bda(self):
        """Carta 50k que pegue a 8ª Bda Inf Mec"""
        r = run_agent("Carta 50k que pegue a 8ª Bda Inf Mec")
        assert r.error is None
        assert_tools_present(r, ["search_military_installation", "search_products"], "P14")


# ── Category F: Border ──


class TestCategoryF:
    def test_p17_fronteira_uruguai(self):
        """Imagem de satélite da fronteira com Uruguai"""
        r = run_agent("Imagem de satélite da fronteira com Uruguai")
        assert r.error is None
        assert_tools_present(r, ["search_border", "search_products"], "P17")


# ── Category R: Conceptual question ──


class TestCategoryR:
    def test_p47_diferenca_mds_mdt(self):
        """Qual a diferença entre MDS e MDT?"""
        r = run_agent("Qual a diferença entre MDS e MDT?")
        assert r.error is None
        names = tool_names(r)
        assert "explain_product_type" in names, f"P47: should use explain_product_type. Got: {names}"
        assert_tools_absent(r, ["search_products", "geocode", "search_municipality"], "P47")
