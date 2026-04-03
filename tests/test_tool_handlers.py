"""Unit tests for tool handlers (no LLM, no network)."""

from llm_tool_calling.geometry_store import GeometryStore
from llm_tool_calling.tool_handlers import ToolHandlers


def make_handlers() -> ToolHandlers:
    return ToolHandlers(GeometryStore())


class TestGeocode:
    def test_known_place(self):
        h = make_handlers()
        r = h.geocode("Alecrim, RS")
        assert r["lat"] == -27.66
        assert "geometry_ref" in r

    def test_unknown_place(self):
        h = make_handlers()
        r = h.geocode("Lugar Inexistente")
        assert "error" in r

    def test_poi(self):
        h = make_handlers()
        r = h.geocode("Usina Hidrelétrica de Itaipu")
        assert r["display_name"] == "Usina Hidrelétrica de Itaipu"


class TestSearchMunicipality:
    def test_with_uf(self):
        h = make_handlers()
        r = h.search_municipality("Porto Alegre", "RS")
        assert r["nome"] == "Porto Alegre"
        assert "geometry_ref" in r

    def test_without_uf_unique(self):
        h = make_handlers()
        r = h.search_municipality("Manaus")
        assert r["nome"] == "Manaus"

    def test_not_found(self):
        h = make_handlers()
        r = h.search_municipality("Cidade Fantasma")
        assert "error" in r


class TestSearchState:
    def test_found(self):
        h = make_handlers()
        r = h.search_state("RS")
        assert r["nome"] == "Rio Grande do Sul"

    def test_not_found(self):
        h = make_handlers()
        r = h.search_state("XX")
        assert "error" in r


class TestSearchProducts:
    def test_by_type(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "dummy")
        r = h.search_products(geometry_ref=ref, tipo="carta_topografica")
        assert r["total"] > 0
        assert all(p["tipo"] == "carta_topografica" for p in r["products"])

    def test_by_scale(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "dummy")
        r = h.search_products(geometry_ref=ref, tipo="carta_topografica", escala=25000)
        assert r["total"] > 0
        assert all("25.000" in p["escala"] for p in r["products"])

    def test_all_types(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "dummy")
        r = h.search_products(geometry_ref=ref, tipo="*")
        assert r["total"] == len(r["products"])


class TestBuffer:
    def test_returns_ref(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "pt")
        r = h.buffer(ref, 5000)
        assert "geometry_ref" in r
        assert r["type"] == "Polygon"


class TestSearchBorder:
    def test_found(self):
        h = make_handlers()
        r = h.search_border("Uruguai")
        assert r["pais"] == "Uruguai"
        assert "geometry_ref" in r

    def test_not_found(self):
        h = make_handlers()
        r = h.search_border("Japão")
        assert "error" in r


class TestSearchHydrography:
    def test_found(self):
        h = make_handlers()
        r = h.search_hydrography("Rio Jacuí")
        assert r["nome"] == "Rio Jacuí"

    def test_not_found(self):
        h = make_handlers()
        r = h.search_hydrography("Rio Inexistente")
        assert "error" in r


class TestSearchMilitaryInstallation:
    def test_by_abbreviation(self):
        h = make_handlers()
        r = h.search_military_installation("8 bda inf mec")
        assert "8ª Brigada" in r["nome_completo"]

    def test_not_found(self):
        h = make_handlers()
        r = h.search_military_installation("99 BI")
        assert "error" in r


class TestRankByScale:
    def test_ordering(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "dummy")
        h.search_products(geometry_ref=ref, tipo="carta_topografica")
        r = h.rank_by_scale("best_first")
        scales = [p["escala"] for p in r["products"]]
        assert scales[0] == "1:25.000"


class TestExplainProductType:
    def test_known(self):
        h = make_handlers()
        r = h.explain_product_type("mds")
        assert "MDS" in r["explanation"]

    def test_unknown(self):
        h = make_handlers()
        r = h.explain_product_type("tipo_fake")
        assert "error" in r


class TestAutocomplete:
    def test_santa(self):
        h = make_handlers()
        r = h.autocomplete_placename("santa")
        assert len(r["suggestions"]) > 0
        assert any("Santa Maria" in s for s in r["suggestions"])
