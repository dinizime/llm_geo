"""Integration tests for tool handlers using real APIs (Nominatim, Overpass, IBGE, Open-Meteo).

These tests make real HTTP requests. They validate response structure and
reasonable value ranges rather than exact synthetic data values.
"""

import pytest

from llm_tool_calling.geometry_store import GeometryStore
from llm_tool_calling.tool_handlers import ToolHandlers


def make_handlers() -> ToolHandlers:
    return ToolHandlers(GeometryStore())


# ═══════════════════════════════════════════════════════════════
# GEOCODING (Nominatim)
# ═══════════════════════════════════════════════════════════════


class TestGeocode:
    def test_known_place(self):
        h = make_handlers()
        r = h.geocode("Porto Alegre, RS")
        assert "geometry_ref" in r
        assert -31 < r["lat"] < -29
        assert -52 < r["lon"] < -50

    def test_unknown_place(self):
        h = make_handlers()
        r = h.geocode("Lugar Completamente Inexistente XYZZY")
        assert "error" in r


class TestReverseGeocode:
    def test_by_coords(self):
        h = make_handlers()
        r = h.reverse_geocode(lat=-29.68, lon=-53.81)
        assert r["municipio"] is not None

    def test_by_geometry_ref(self):
        h = make_handlers()
        pt = h.geocode("Santa Maria, RS")
        r = h.reverse_geocode(geometry_ref=pt["geometry_ref"])
        assert r["municipio"] is not None

    def test_outside(self):
        h = make_handlers()
        r = h.reverse_geocode(lat=0, lon=0)
        # Over the ocean — may return None or some result
        assert "municipio" in r


class TestCreatePoint:
    def test_basic(self):
        h = make_handlers()
        r = h.create_point(lat=-29.68, lon=-53.81)
        assert "geometry_ref" in r
        assert r["lat"] == -29.68
        assert r["lon"] == -53.81

    def test_usable_in_buffer(self):
        h = make_handlers()
        pt = h.create_point(lat=-29.68, lon=-53.81)
        buf = h.buffer(pt["geometry_ref"], 5000)
        assert "geometry_ref" in buf


# ═══════════════════════════════════════════════════════════════
# MUNICIPALITIES & STATES (IBGE)
# ═══════════════════════════════════════════════════════════════


class TestSearchMunicipality:
    def test_with_uf(self):
        h = make_handlers()
        r = h.search_municipality("Porto Alegre", "RS")
        assert r["nome"] == "Porto Alegre"
        assert "geometry_ref" in r
        assert r["codigo_ibge"] != ""

    def test_not_found(self):
        h = make_handlers()
        r = h.search_municipality("Cidade Fantasma XYZZY")
        assert "error" in r


class TestSearchState:
    def test_found(self):
        h = make_handlers()
        r = h.search_state("RS")
        assert r["uf"] == "RS"
        assert "geometry_ref" in r

    def test_not_found(self):
        h = make_handlers()
        r = h.search_state("XX")
        assert "error" in r


# ═══════════════════════════════════════════════════════════════
# DOMAIN DATA (Products, Military, Named Regions, Borders)
# ═══════════════════════════════════════════════════════════════


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

    def test_all_types(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "dummy")
        r = h.search_products(geometry_ref=ref, tipo="*")
        assert r["total"] == len(r["products"])


class TestSearchByArticulation:
    def test_exact(self):
        h = make_handlers()
        r = h.search_by_articulation("SH-22-V-C-IV-1")
        assert r["total"] >= 1

    def test_partial(self):
        h = make_handlers()
        r = h.search_by_articulation("SH-21-X-D")
        assert r["total"] >= 2

    def test_not_found(self):
        h = make_handlers()
        r = h.search_by_articulation("ZZ-99")
        assert "error" in r


class TestSearchBorder:
    def test_found(self):
        h = make_handlers()
        r = h.search_border("Uruguai")
        assert "geometry_ref" in r

    def test_not_found(self):
        h = make_handlers()
        r = h.search_border("Japao XYZZY")
        assert "error" in r


class TestSearchMilitaryInstallation:
    def test_by_abbreviation(self):
        h = make_handlers()
        r = h.search_military_installation("8 bda inf mec")
        assert "8" in r["nome_completo"] or "Brigada" in r["nome_completo"]

    def test_not_found(self):
        h = make_handlers()
        r = h.search_military_installation("99 BI Inexistente XYZZY")
        assert "error" in r


class TestSearchNamedRegion:
    def test_found(self):
        h = make_handlers()
        r = h.search_named_region("Serra Gaúcha")
        assert "geometry_ref" in r

    def test_not_found(self):
        h = make_handlers()
        r = h.search_named_region("Regiao Inexistente XYZZY")
        assert "error" in r


class TestProductsHaveScaleAndDate:
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


# ═══════════════════════════════════════════════════════════════
# SPATIAL OPERATIONS (Shapely/pyproj)
# ═══════════════════════════════════════════════════════════════


class TestBuffer:
    def test_returns_ref(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [-53.8, -29.7]}, "pt")
        r = h.buffer(ref, 5000)
        assert "geometry_ref" in r
        assert r["type"] == "Polygon"

    def test_buffer_produces_polygon(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [-53.8, -29.7]}, "pt")
        r = h.buffer(ref, 10000)
        geom = h.gs.get(r["geometry_ref"])
        assert geom["type"] == "Polygon"
        assert len(geom["coordinates"][0]) > 10


class TestCheckIntersection:
    def test_overlapping(self):
        h = make_handlers()
        a = h.gs.put({"type": "Polygon", "coordinates": [
            [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]}, "a")
        b = h.gs.put({"type": "Polygon", "coordinates": [
            [[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]]]}, "b")
        r = h.check_intersection(a, b)
        assert r["intersects"] is True

    def test_non_overlapping(self):
        h = make_handlers()
        a = h.gs.put({"type": "Polygon", "coordinates": [
            [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}, "a")
        b = h.gs.put({"type": "Polygon", "coordinates": [
            [[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]]}, "b")
        r = h.check_intersection(a, b)
        assert r["intersects"] is False


class TestCheckContains:
    def test_point_in_polygon(self):
        h = make_handlers()
        poly = h.gs.put({"type": "Polygon", "coordinates": [
            [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]}, "poly")
        pt = h.gs.put({"type": "Point", "coordinates": [5, 5]}, "pt")
        r = h.check_contains(poly, pt)
        assert r["contains"] is True

    def test_point_outside(self):
        h = make_handlers()
        poly = h.gs.put({"type": "Polygon", "coordinates": [
            [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}, "poly")
        pt = h.gs.put({"type": "Point", "coordinates": [5, 5]}, "pt")
        r = h.check_contains(poly, pt)
        assert r["contains"] is False


class TestIntersect:
    def test_overlapping(self):
        h = make_handlers()
        a = h.gs.put({"type": "Polygon", "coordinates": [
            [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]}, "a")
        b = h.gs.put({"type": "Polygon", "coordinates": [
            [[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]]]}, "b")
        r = h.intersect(a, b)
        assert r["is_empty"] is False
        assert r["area_km2"] > 0
        assert "geometry_ref" in r

    def test_non_overlapping(self):
        h = make_handlers()
        a = h.gs.put({"type": "Polygon", "coordinates": [
            [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}, "a")
        b = h.gs.put({"type": "Polygon", "coordinates": [
            [[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]]}, "b")
        r = h.intersect(a, b)
        assert r["is_empty"] is True
        assert r["area_km2"] == 0


# ═══════════════════════════════════════════════════════════════
# GEOMETRIC COMPUTATIONS (Shapely/pyproj)
# ═══════════════════════════════════════════════════════════════


class TestComputeDistance:
    def test_known_cities(self):
        h = make_handlers()
        a = h.geocode("Porto Alegre, RS")
        b = h.geocode("Santa Maria, RS")
        r = h.compute_distance(a["geometry_ref"], b["geometry_ref"])
        assert "distance_km" in r
        assert 200 < r["distance_km"] < 400

    def test_same_point(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [-53.8, -29.7]}, "pt")
        r = h.compute_distance(ref, ref)
        assert r["distance_km"] == 0.0


class TestComputeArea:
    def test_known_polygon(self):
        h = make_handlers()
        # ~1 degree square at equator ≈ 12,321 km2
        ref = h.gs.put({"type": "Polygon", "coordinates": [
            [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}, "sq")
        r = h.compute_area(ref)
        assert "area_km2" in r
        assert r["area_km2"] > 10000

    def test_not_polygon(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "pt")
        r = h.compute_area(ref)
        assert "error" in r


class TestComputeLength:
    def test_known_line(self):
        h = make_handlers()
        # ~1 degree of latitude ≈ 111 km
        ref = h.gs.put({"type": "LineString", "coordinates": [
            [-53.8, -30.0], [-53.8, -29.0]]}, "line")
        r = h.compute_length(ref)
        assert "length_km" in r
        assert 100 < r["length_km"] < 120

    def test_not_linestring(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "pt")
        r = h.compute_length(ref)
        assert "error" in r


# ═══════════════════════════════════════════════════════════════
# FEATURES (Overpass / OSM)
# ═══════════════════════════════════════════════════════════════


class TestSearchFeatures:
    def test_hospitals_in_area(self):
        h = make_handlers()
        # Buffer around Porto Alegre center
        pt = h.gs.put({"type": "Point", "coordinates": [-51.17, -30.03]}, "poa")
        buf = h.buffer(pt, 20000)
        r = h.search_features("hospital", buf["geometry_ref"])
        assert "total" in r
        assert "features" in r

    def test_unknown_type(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "pt")
        buf = h.buffer(ref, 1000)
        r = h.search_features("tipo_fake", buf["geometry_ref"])
        assert r["total"] == 0


class TestFindNearest:
    def test_returns_structure(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [-51.17, -30.03]}, "poa")
        r = h.find_nearest("hospital", ref, limit=2)
        assert "nearest" in r
        if r["total"] > 0:
            assert "distance_km" in r["nearest"][0]

    def test_unknown_type(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [0, 0]}, "pt")
        r = h.find_nearest("tipo_fake", ref)
        assert r["total"] == 0


# ═══════════════════════════════════════════════════════════════
# HYDROGRAPHY & ROADS (Overpass)
# ═══════════════════════════════════════════════════════════════


class TestSearchHydrography:
    def test_found(self):
        h = make_handlers()
        r = h.search_hydrography("Rio Jacuí")
        # Overpass may be rate-limited; accept both success and error
        assert "geometry_ref" in r or "error" in r

    def test_not_found(self):
        h = make_handlers()
        r = h.search_hydrography("Rio Inexistente XYZZY")
        assert "error" in r


class TestSearchRoad:
    def test_found(self):
        h = make_handlers()
        r = h.search_road("BR-290")
        assert "geometry_ref" in r
        assert r["extensao_km"] > 0

    def test_not_found(self):
        h = make_handlers()
        r = h.search_road("BR-999")
        assert "error" in r


# ═══════════════════════════════════════════════════════════════
# ROUTE & ALONG ROUTE
# ═══════════════════════════════════════════════════════════════


class TestComputeRoute:
    def test_realistic_distance(self):
        h = make_handlers()
        a = h.geocode("Porto Alegre, RS")
        b = h.geocode("Santa Maria, RS")
        r = h.compute_route(a["geometry_ref"], b["geometry_ref"])
        assert r["distance_km"] > 200
        assert r["distance_km"] < 500
        assert r["duration_min"] > 0


class TestFeaturesAlongRoute:
    def test_structure(self):
        h = make_handlers()
        a = h.geocode("Santa Maria, RS")
        b = h.geocode("Porto Alegre, RS")
        route = h.compute_route(a["geometry_ref"], b["geometry_ref"])
        r = h.features_along_route("hospital", route["geometry_ref"], buffer_metros=10000)
        assert "total" in r
        assert "features" in r


# ═══════════════════════════════════════════════════════════════
# ELEVATION (Open-Meteo)
# ═══════════════════════════════════════════════════════════════


class TestGetElevation:
    def test_point(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [-53.81, -29.68]}, "sm")
        r = h.get_elevation(ref)
        assert "elevation_m" in r
        assert 50 < r["elevation_m"] < 500

    def test_polygon(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Polygon", "coordinates": [
            [[-51.3, -29.3], [-51.0, -29.3], [-51.0, -29.0],
             [-51.3, -29.0], [-51.3, -29.3]]]}, "cxs")
        r = h.get_elevation(ref)
        assert "min_elevation_m" in r
        assert "max_elevation_m" in r
        assert r["max_elevation_m"] >= r["min_elevation_m"]


class TestGetTerrainProfile:
    def test_linestring(self):
        h = make_handlers()
        ref = h.gs.put({"type": "LineString", "coordinates": [
            [-53.81, -29.68], [-51.17, -30.03]]}, "route")
        r = h.get_terrain_profile(ref)
        assert "points" in r
        assert len(r["points"]) >= 2
        assert "classification" in r
        assert r["classification"] in ("plano", "ondulado", "montanhoso")

    def test_not_linestring(self):
        h = make_handlers()
        ref = h.gs.put({"type": "Point", "coordinates": [-53.8, -29.7]}, "pt")
        r = h.get_terrain_profile(ref)
        assert "error" in r

    def test_aggregates(self):
        h = make_handlers()
        ref = h.gs.put({"type": "LineString", "coordinates": [
            [-53.81, -29.68], [-51.17, -30.03]]}, "route")
        r = h.get_terrain_profile(ref)
        if "points" in r:
            assert r["min_m"] <= r["avg_m"] <= r["max_m"]
            assert r["total_ascent_m"] >= 0
            assert r["total_descent_m"] >= 0
