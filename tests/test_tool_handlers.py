"""Unit tests for tool handlers (no LLM, no network)."""

from llm_tool_calling.geometry_store import GeometryStore
from llm_tool_calling import tool_handlers
from llm_tool_calling.tool_handlers import ToolHandlers

# Disable external API calls for unit tests
tool_handlers.USE_SYNTHETIC_ONLY = True


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


class TestProductsHaveScaleAndDate:
    """Products include escala and data_produto so the model can sort them."""
    def test_products_have_scale(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "dummy")
        r = h.search_products(geometry_ref=ref, tipo="carta_topografica")
        scaled = [p for p in r["products"] if p.get("escala")]
        assert len(scaled) >= 2

    def test_products_have_date(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "dummy")
        r = h.search_products(geometry_ref=ref, tipo="*")
        dated = [p for p in r["products"] if p.get("data_produto")]
        assert len(dated) >= 2


class TestAmbiguousMunicipality:
    """search_municipality returns candidates for ambiguous names (replaces autocomplete)."""
    def test_ambiguous_returns_candidates(self):
        h = make_handlers()
        r = h.search_municipality("Santa Maria")
        # Should resolve (unique) — not ambiguous in our data
        assert "nome" in r


class TestFeaturesHaveAttributes:
    """Features include attributes so the model can identify superlatives (replaces rank_features)."""
    def test_torre_has_altura(self):
        h = make_handlers()
        state = h.search_state("RS")
        r = h.search_features("torre_comunicacao", state["geometry_ref"])
        assert r["total"] > 0
        assert all("altura_m" in f for f in r["features"])

    def test_ponte_has_comprimento(self):
        h = make_handlers()
        state = h.search_state("RS")
        r = h.search_features("ponte", state["geometry_ref"])
        assert r["total"] > 0
        assert all("comprimento_m" in f for f in r["features"])


# ═══════════════════════════════════════════════════════════════
# NEW TOOL TESTS
# ═══════════════════════════════════════════════════════════════


class TestComputeDistance:
    def test_known_cities(self):
        h = make_handlers()
        a = h.geocode("Porto Alegre")
        b = h.geocode("Santa Maria")
        r = h.compute_distance(a["geometry_ref"], b["geometry_ref"])
        assert "distance_km" in r
        assert 200 < r["distance_km"] < 400

    def test_same_point(self):
        h = make_handlers()
        a = h.geocode("Porto Alegre")
        r = h.compute_distance(a["geometry_ref"], a["geometry_ref"])
        assert r["distance_km"] == 0.0


class TestComputeArea:
    def test_municipality(self):
        h = make_handlers()
        m = h.search_municipality("Porto Alegre", "RS")
        r = h.compute_area(m["geometry_ref"])
        assert "area_km2" in r
        assert r["area_km2"] > 0

    def test_not_polygon(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "pt")
        r = h.compute_area(ref)
        assert "error" in r


class TestComputeLength:
    def test_river(self):
        h = make_handlers()
        r = h.search_hydrography("Rio Jacuí")
        length = h.compute_length(r["geometry_ref"])
        assert "length_km" in length
        assert length["length_km"] > 0

    def test_not_linestring(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "pt")
        r = h.compute_length(ref)
        assert "error" in r


class TestFindNearest:
    def test_hospital(self):
        h = make_handlers()
        a = h.geocode("Alegrete")
        r = h.find_nearest("hospital", a["geometry_ref"], limit=2)
        assert "nearest" in r
        assert len(r["nearest"]) <= 2
        assert r["nearest"][0]["distance_km"] >= 0

    def test_unknown_type(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "pt")
        r = h.find_nearest("tipo_fake", ref)
        assert r["total"] == 0


class TestSearchRoad:
    def test_found(self):
        h = make_handlers()
        r = h.search_road("BR-290")
        assert r["nome"] == "BR-290"
        assert "geometry_ref" in r
        assert r["extensao_km"] > 0

    def test_with_uf(self):
        h = make_handlers()
        r = h.search_road("BR-101", uf="SC")
        assert r["extensao_km"] < 500

    def test_not_found(self):
        h = make_handlers()
        r = h.search_road("BR-999")
        assert "error" in r


class TestFeaturesAlongRoute:
    def test_pontes_on_route(self):
        h = make_handlers()
        a = h.geocode("Santa Maria")
        b = h.geocode("Alegrete")
        route = h.compute_route(a["geometry_ref"], b["geometry_ref"])
        r = h.features_along_route("ponte", route["geometry_ref"], buffer_metros=50000)
        assert "total" in r


class TestCheckIntersection:
    def test_overlapping(self):
        h = make_handlers()
        state = h.search_state("RS")
        mun = h.search_municipality("Porto Alegre", "RS")
        r = h.check_intersection(state["geometry_ref"], mun["geometry_ref"])
        assert r["intersects"] is True

    def test_non_overlapping(self):
        h = make_handlers()
        a = h.gs.put({"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}, "a")
        b = h.gs.put({"type": "Polygon", "coordinates": [[[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]]}, "b")
        r = h.check_intersection(a, b)
        assert r["intersects"] is False


class TestListMunicipalitiesIn:
    def test_state(self):
        h = make_handlers()
        state = h.search_state("RS")
        r = h.list_municipalities_in(state["geometry_ref"])
        assert r["total"] >= 5
        names = [m["nome"] for m in r["municipalities"]]
        assert "Porto Alegre" in names


class TestIntersectImproved:
    def test_returns_is_empty(self):
        h = make_handlers()
        state = h.search_state("RS")
        mun = h.search_municipality("Porto Alegre", "RS")
        r = h.intersect(state["geometry_ref"], mun["geometry_ref"])
        assert "is_empty" in r
        assert r["is_empty"] is False
        assert r["area_km2"] > 0


class TestComputeRouteImproved:
    def test_realistic_distance(self):
        h = make_handlers()
        a = h.geocode("Porto Alegre")
        b = h.geocode("Santa Maria")
        r = h.compute_route(a["geometry_ref"], b["geometry_ref"])
        assert r["distance_km"] > 200
        assert r["distance_km"] < 500


class TestSearchFeaturesWithAttributes:
    def test_hospital_has_leitos(self):
        h = make_handlers()
        mun = h.search_municipality("Santa Maria", "RS")
        r = h.search_features("hospital", mun["geometry_ref"])
        assert r["total"] > 0
        assert "leitos" in r["features"][0]

    def test_terra_indigena(self):
        h = make_handlers()
        state = h.search_state("RS")
        r = h.search_features("terra_indigena", state["geometry_ref"])
        assert r["total"] >= 2
        assert "etnia" in r["features"][0]


# ═══════════════════════════════════════════════════════════════
# NEW TOOLS TESTS
# ═══════════════════════════════════════════════════════════════


class TestCreatePoint:
    def test_basic(self):
        h = make_handlers()
        r = h.create_point(lat=-29.68, lon=-53.81)
        assert "geometry_ref" in r
        assert r["lat"] == -29.68
        assert r["lon"] == -53.81

    def test_with_label(self):
        h = make_handlers()
        r = h.create_point(lat=-29.68, lon=-53.81, label="meu ponto")
        assert "geometry_ref" in r

    def test_usable_in_buffer(self):
        h = make_handlers()
        pt = h.create_point(lat=-29.68, lon=-53.81)
        buf = h.buffer(pt["geometry_ref"], 5000)
        assert "geometry_ref" in buf


class TestReverseGeocode:
    def test_by_coords(self):
        h = make_handlers()
        r = h.reverse_geocode(lat=-29.68, lon=-53.81)
        assert r["municipio"] == "Santa Maria"
        assert r["uf"] == "RS"

    def test_by_geometry_ref(self):
        h = make_handlers()
        pt = h.geocode("Santa Maria")
        r = h.reverse_geocode(geometry_ref=pt["geometry_ref"])
        assert r["municipio"] == "Santa Maria"

    def test_outside(self):
        h = make_handlers()
        r = h.reverse_geocode(lat=0, lon=0)
        assert r["municipio"] is None


class TestCheckContains:
    def test_point_in_municipality(self):
        h = make_handlers()
        pt = h.geocode("Santa Maria")
        mun = h.search_municipality("Santa Maria", "RS")
        r = h.check_contains(mun["geometry_ref"], pt["geometry_ref"])
        assert r["contains"] is True

    def test_point_outside(self):
        h = make_handlers()
        pt = h.geocode("Porto Alegre")
        mun = h.search_municipality("Alegrete", "RS")
        r = h.check_contains(mun["geometry_ref"], pt["geometry_ref"])
        assert r["contains"] is False

    def test_municipality_in_state(self):
        h = make_handlers()
        mun = h.search_municipality("Porto Alegre", "RS")
        state = h.search_state("RS")
        r = h.check_contains(state["geometry_ref"], mun["geometry_ref"])
        assert r["contains"] is True


class TestGetNeighbors:
    def test_has_neighbors(self):
        h = make_handlers()
        mun = h.search_municipality("Santa Maria", "RS")
        r = h.get_neighbors(mun["geometry_ref"])
        assert r["total"] > 0

    def test_excludes_self(self):
        h = make_handlers()
        mun = h.search_municipality("Santa Maria", "RS")
        r = h.get_neighbors(mun["geometry_ref"])
        names = [n["nome"] for n in r["neighbors"]]
        assert "Santa Maria" not in names

    def test_invalid_ref(self):
        h = make_handlers()
        r = h.get_neighbors("invalid_ref")
        assert "error" in r


class TestSearchByArticulation:
    def test_exact(self):
        h = make_handlers()
        r = h.search_by_articulation("SH-22-V-C-IV-1")
        assert r["total"] >= 1
        assert any(p["id"] == 9 for p in r["products"])

    def test_partial(self):
        h = make_handlers()
        r = h.search_by_articulation("SH-21-X-D")
        assert r["total"] >= 2
        ids = [p["id"] for p in r["products"]]
        assert 1 in ids or 2 in ids or 3 in ids

    def test_not_found(self):
        h = make_handlers()
        r = h.search_by_articulation("ZZ-99")
        assert "error" in r


class TestGetElevation:
    def test_point(self):
        h = make_handlers()
        pt = h.geocode("Santa Maria")
        r = h.get_elevation(pt["geometry_ref"])
        assert "elevation_m" in r
        assert 50 < r["elevation_m"] < 500

    def test_polygon(self):
        h = make_handlers()
        mun = h.search_municipality("Caxias do Sul", "RS")
        r = h.get_elevation(mun["geometry_ref"])
        assert "min_elevation_m" in r
        assert "max_elevation_m" in r
        assert r["max_elevation_m"] >= r["min_elevation_m"]

    def test_serra_higher(self):
        h = make_handlers()
        caxias = h.geocode("Caxias do Sul")
        alegrete = h.geocode("Alegrete")
        e_cax = h.get_elevation(caxias["geometry_ref"])
        e_ale = h.get_elevation(alegrete["geometry_ref"])
        assert e_cax["elevation_m"] > e_ale["elevation_m"]


class TestGetTerrainProfile:
    def test_route(self):
        h = make_handlers()
        o = h.geocode("Santa Maria")
        d = h.geocode("Alegrete")
        route = h.compute_route(o["geometry_ref"], d["geometry_ref"])
        r = h.get_terrain_profile(route["geometry_ref"])
        assert "points" in r
        assert len(r["points"]) >= 2
        assert "min_m" in r
        assert "classification" in r

    def test_road(self):
        h = make_handlers()
        road = h.search_road("BR-290")
        r = h.get_terrain_profile(road["geometry_ref"])
        assert r["classification"] in ("plano", "ondulado", "montanhoso")

    def test_not_linestring(self):
        h = make_handlers()
        pt = h.geocode("Santa Maria")
        r = h.get_terrain_profile(pt["geometry_ref"])
        assert "error" in r

    def test_aggregates(self):
        h = make_handlers()
        road = h.search_road("BR-290")
        r = h.get_terrain_profile(road["geometry_ref"])
        assert r["min_m"] <= r["avg_m"] <= r["max_m"]
        assert r["total_ascent_m"] >= 0
        assert r["total_descent_m"] >= 0


class TestSearchFeaturesFiltered:
    def test_filter_gt(self):
        h = make_handlers()
        state = h.search_state("RS")
        r = h.search_features("ponte", state["geometry_ref"], atributo="capacidade_ton", operador=">", valor=50)
        assert r["total"] > 0
        for f in r["features"]:
            assert f["capacidade_ton"] > 50

    def test_filter_in(self):
        h = make_handlers()
        state = h.search_state("RS")
        r = h.search_features("posto_combustivel", state["geometry_ref"], atributo="bandeira", operador="in", valor=["BR", "Shell"])
        assert r["total"] > 0
        for f in r["features"]:
            assert f["bandeira"] in ["BR", "Shell"]

    def test_no_filter(self):
        h = make_handlers()
        state = h.search_state("RS")
        r1 = h.search_features("ponte", state["geometry_ref"])
        r2 = h.search_features("ponte", state["geometry_ref"], atributo=None, operador=None, valor=None)
        assert r1["total"] == r2["total"]

    def test_filter_no_match(self):
        h = make_handlers()
        state = h.search_state("RS")
        r = h.search_features("ponte", state["geometry_ref"], atributo="capacidade_ton", operador=">", valor=9999)
        assert r["total"] == 0
