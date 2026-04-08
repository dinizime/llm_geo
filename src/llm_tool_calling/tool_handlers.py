"""Simulated tool implementations backed by synthetic data."""

import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request

from .geometry_store import GeometryStore
from .synthetic_data import (
    BORDERS,
    FEATURES,
    GEOCODE_RESULTS,
    HYDROGRAPHY,
    MILITARY_INSTALLATIONS,
    MUNICIPALITIES,
    NAMED_REGIONS,
    PRODUCTS,
    ROADS,
    STATES,
    compute_elevation,
)

_ATTR_OPS = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "=": lambda a, b: a == b,
    "in": lambda a, b: a in b,
}


def _safe_op(op_fn, a, b) -> bool:
    try:
        return op_fn(a, b)
    except (TypeError, ValueError):
        return False


def _fuzzy_find(query: str, data: dict) -> tuple[str, dict] | None:
    key = query.lower().strip()
    if key in data:
        return key, data[key]
    for k, v in data.items():
        if k in key or key in k:
            return k, v
    return None


def _feature_to_entry(f: dict, gs, extra: dict | None = None) -> dict:
    """Build a result entry from a raw feature dict, storing geometry and copying attributes."""
    ref = gs.put(f["geometry"], label=f["nome"])
    entry = {"nome": f["nome"], "geometry_ref": ref}
    if extra:
        entry.update(extra)
    for k, v in f.items():
        if k not in ("nome", "geometry"):
            entry[k] = v
    return entry


def _format_product(p: dict) -> dict:
    """Build a result entry from a raw product dict."""
    result = {
        "id": p["id"],
        "tipo": p["tipo"],
        "escala": f"1:{p['escala']:,}".replace(",", ".") if p.get("escala") else None,
        "data_produto": p["data_produto"],
        "articulacao": p.get("articulacao"),
        "nome": p["nome"],
        "resolucao_m": p.get("resolucao_m"),
    }
    if p.get("bbox"):
        result["bbox"] = p["bbox"]
    return result


def _haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Haversine distance in km between two (lon, lat) points."""
    R = 6371.0
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


_UA = {"User-Agent": "GeoportalBot/1.0"}

# Set to True to disable external API calls (for unit tests)
USE_SYNTHETIC_ONLY = False


# ─── Open-Meteo Elevation API ─────────────────────────────────

def _open_meteo_elevation(lat: float, lon: float) -> float | None:
    """Get real elevation from Open-Meteo API. Returns meters or None."""
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        elevs = data.get("elevation", [])
        return round(elevs[0], 1) if elevs else None
    except Exception:
        return None


def _open_meteo_elevations(points: list[tuple[float, float]]) -> list[float] | None:
    """Batch elevation query. points = [(lat, lon), ...]. Returns list of elevations or None."""
    if not points:
        return None
    lats = ",".join(str(round(p[0], 6)) for p in points)
    lons = ",".join(str(round(p[1], 6)) for p in points)
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lats}&longitude={lons}"
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        elevs = data.get("elevation", [])
        return [round(e, 1) for e in elevs] if len(elevs) == len(points) else None
    except Exception:
        return None


# ─── Overpass (OSM) API ────────────────────────────────────────

_OSM_TAGS = {
    "ponte": [('way["man_made"="bridge"]', 'node["man_made"="bridge"]')],
    "tunel": [('way["tunnel"="yes"]',)],
    "estacao_ferroviaria": [('node["railway"="station"]', 'way["railway"="station"]')],
    "travessia_balsa": [('node["amenity"="ferry_terminal"]', 'way["amenity"="ferry_terminal"]')],
    "torre_comunicacao": [('node["man_made"="tower"]["tower:type"="communication"]',
                           'way["man_made"="tower"]["tower:type"="communication"]')],
    "aerogerador": [('node["generator:source"="wind"]', 'way["generator:source"="wind"]')],
    "linha_transmissao": [('way["power"="line"]',)],
    "chamine_industrial": [('node["man_made"="chimney"]', 'way["man_made"="chimney"]')],
    "aeroporto": [('node["aeroway"="aerodrome"]', 'way["aeroway"="aerodrome"]')],
    "heliporto": [('node["aeroway"="helipad"]', 'way["aeroway"="helipad"]')],
    "campo_pouso": [('node["aeroway"="airstrip"]', 'way["aeroway"="airstrip"]')],
    "hospital": [('node["amenity"="hospital"]', 'way["amenity"="hospital"]')],
    "escola": [('node["amenity"="school"]', 'way["amenity"="school"]')],
    "posto_combustivel": [('node["amenity"="fuel"]', 'way["amenity"="fuel"]')],
    "barragem": [('way["waterway"="dam"]', 'node["waterway"="dam"]')],
    "reservatorio": [('way["water"="reservoir"]', 'node["natural"="water"]["water"="reservoir"]')],
    "estacao_tratamento_agua": [('node["man_made"="water_works"]', 'way["man_made"="water_works"]')],
    "terra_indigena": [('way["boundary"="aboriginal_lands"]', 'relation["boundary"="aboriginal_lands"]')],
    "edificacao_destaque": [('node["historic"]', 'way["historic"]')],
    "area_treinamento": [('way["military"="training_area"]', 'node["military"="training_area"]')],
}


def _overpass_query(query: str) -> list[dict] | None:
    """Execute Overpass API query. Returns list of elements or None."""
    url = "https://overpass-api.de/api/interpreter"
    full_query = f"[out:json][timeout:15];{query}out center;"
    try:
        data = urllib.parse.urlencode({"data": full_query}).encode()
        req = urllib.request.Request(url, data=data, headers=_UA)
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
        return result.get("elements", [])
    except Exception:
        return None


def _overpass_features_in_bbox(tipo: str, bbox: tuple[float, float, float, float],
                                limit: int = 50) -> list[dict] | None:
    """Search OSM features by type within bounding box. Returns feature dicts or None."""
    tags = _OSM_TAGS.get(tipo)
    if not tags:
        return None
    south, west, north, east = bbox[1], bbox[0], bbox[3], bbox[2]  # bbox is (min_lon, min_lat, max_lon, max_lat)
    parts = []
    for tag_group in tags:
        for tag in tag_group:
            parts.append(f"{tag}({south},{west},{north},{east});")
    query = "(" + "".join(parts) + ");"
    elements = _overpass_query(query)
    if elements is None:
        return None
    features = []
    for el in elements[:limit]:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        tags_data = el.get("tags", {})
        nome = tags_data.get("name", tags_data.get("ref", f"{tipo}_{el['id']}"))
        feat = {
            "nome": nome,
            "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
        }
        # Extract useful attributes from OSM tags
        if tags_data.get("height"):
            try:
                feat["altura_m"] = float(tags_data["height"].replace("m", "").strip())
            except ValueError:
                pass
        if tags_data.get("length"):
            try:
                feat["comprimento_m"] = float(tags_data["length"].replace("m", "").strip())
            except ValueError:
                pass
        if tags_data.get("ele"):
            try:
                feat["elevacao_m"] = float(tags_data["ele"])
            except ValueError:
                pass
        if tags_data.get("beds"):
            try:
                feat["leitos"] = int(tags_data["beds"])
            except ValueError:
                pass
        if tags_data.get("capacity"):
            try:
                feat["capacidade"] = int(tags_data["capacity"])
            except ValueError:
                pass
        features.append(feat)
    return features


def _overpass_hydrography(nome: str) -> dict | None:
    """Search hydrography by name via Overpass with full geometry. Returns dict or None."""
    escaped = nome.replace('"', '\\"')
    # Use out geom to get full coordinates
    url = "https://overpass-api.de/api/interpreter"
    full_query = (
        f'[out:json][timeout:15];'
        f'('
        f'way["waterway"]["name"~"{escaped}",i](-35,-58,-27,-49);'
        f'relation["waterway"]["name"~"{escaped}",i](-35,-58,-27,-49);'
        f'way["natural"="water"]["name"~"{escaped}",i](-35,-58,-27,-49);'
        f');out geom;'
    )
    try:
        data = urllib.parse.urlencode({"data": full_query}).encode()
        req = urllib.request.Request(url, data=data, headers=_UA)
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
        elements = result.get("elements", [])
        if not elements:
            return None
    except Exception:
        return None
    # Combine all segments into one geometry
    all_coords = []
    tags = elements[0].get("tags", {})
    for el in elements:
        if el.get("geometry"):
            coords = [[p["lon"], p["lat"]] for p in el["geometry"]]
            all_coords.extend(coords)
        elif el.get("members"):
            for member in el["members"]:
                if member.get("geometry"):
                    coords = [[p["lon"], p["lat"]] for p in member["geometry"]]
                    all_coords.extend(coords)
    tipo_map = {"river": "rio", "stream": "arroio", "canal": "canal", "lake": "lago",
                "reservoir": "reservatório"}
    ww = tags.get("waterway", tags.get("natural", ""))
    tipo = tipo_map.get(ww, ww)
    if all_coords:
        geom = {"type": "LineString", "coordinates": all_coords}
    else:
        return None
    return {"nome": tags.get("name", nome), "tipo": tipo, "geometry": geom}


def _overpass_road(identificador: str) -> dict | None:
    """Search road by ref (e.g. BR-290) via Overpass. Returns dict or None."""
    # Normalize: "BR290" → "BR-290", "br 290" → "BR-290"
    raw = identificador.upper().strip().replace(" ", "").replace("_", "")
    m = re.match(r"(BR|RS|SC|PR|SP|MG|MT|MS|GO|BA|RJ|ES)[-]?(\d+)", raw)
    if m:
        ref_clean = f"{m.group(1)}-{m.group(2)}"
    else:
        ref_clean = identificador.strip()
    escaped = ref_clean.replace('"', '\\"')
    url = "https://overpass-api.de/api/interpreter"
    # Filter to trunk/primary to keep query fast; bbox covers RS
    full_query = (
        f'[out:json][timeout:25];'
        f'('
        f'way["highway"~"trunk|primary"]["ref"~"{escaped}"](-34,-58,-27,-49);'
        f');out geom;'
    )
    try:
        data = urllib.parse.urlencode({"data": full_query}).encode()
        req = urllib.request.Request(url, data=data, headers=_UA)
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
        elements = result.get("elements", [])
        if not elements:
            return None
        # Combine all way segments, computing length per segment
        all_coords = []
        total_km = 0.0
        ref_tag = ref_clean
        road_name = None
        for el in elements:
            el_tags = el.get("tags", {})
            if not road_name and el_tags.get("name"):
                road_name = el_tags["name"]
            if el_tags.get("ref"):
                ref_tag = el_tags["ref"]
            if el.get("geometry"):
                coords = [[p["lon"], p["lat"]] for p in el["geometry"]]
                # Length of this segment only
                for i in range(len(coords) - 1):
                    total_km += _haversine(coords[i][0], coords[i][1],
                                           coords[i + 1][0], coords[i + 1][1])
                all_coords.extend(coords)
        if not all_coords:
            return None
        nome = f"Rodovia {ref_tag}"
        geom = {"type": "LineString", "coordinates": all_coords}
        return {
            "nome": nome,
            "ref": ref_tag,
            "descricao": road_name or nome,
            "extensao_km": round(total_km, 1),
            "geometry": geom,
        }
    except Exception:
        return None


# ─── IBGE + Nominatim for municipalities ──────────────────────

def _nominatim_municipality(nome: str, uf: str = None) -> dict | None:
    """Search municipality via Nominatim with polygon. Returns dict or None."""
    q = f"{nome}, {uf}, Brazil" if uf else f"{nome}, Brazil"
    query = urllib.parse.quote(q)
    url = (
        f"https://nominatim.openstreetmap.org/search"
        f"?q={query}&format=json&limit=1&countrycodes=br"
        f"&featuretype=city&polygon_geojson=1&addressdetails=1"
    )
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if not data:
            return None
        hit = data[0]
        addr = hit.get("address", {})
        osm_class = hit.get("class", "")
        osm_type = hit.get("type", "")
        # Only accept place/boundary results (not roads etc)
        if osm_class not in ("place", "boundary"):
            return None
        geom = hit.get("geojson")
        if not geom:
            geom = {"type": "Point", "coordinates": [float(hit["lon"]), float(hit["lat"])]}
        # Simplify large polygons (keep only outer ring, limit points)
        if geom.get("type") == "MultiPolygon":
            # Take largest polygon
            largest = max(geom["coordinates"], key=lambda p: len(p[0]) if p else 0)
            geom = {"type": "Polygon", "coordinates": largest}
        if geom.get("type") == "Polygon":
            ring = geom["coordinates"][0]
            if len(ring) > 200:
                step = max(1, len(ring) // 200)
                geom["coordinates"] = [ring[::step] + [ring[0]]]
        state_abbr = addr.get("ISO3166-2-lvl4", "").replace("BR-", "")
        return {
            "nome": addr.get("city") or addr.get("town") or addr.get("municipality") or nome,
            "uf": state_abbr or addr.get("state", ""),
            "geometry": geom,
        }
    except Exception:
        return None


def _ibge_population(nome: str, uf: str = None) -> dict | None:
    """Get municipality population/code from IBGE API. Returns dict or None."""
    query = urllib.parse.quote(nome)
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        nome_lower = nome.lower().strip()
        for m in data:
            if m["nome"].lower() == nome_lower:
                if uf and m["microrregiao"]["mesorregiao"]["UF"]["sigla"].lower() != uf.lower():
                    continue
                return {
                    "codigo_ibge": m["id"],
                    "nome": m["nome"],
                    "uf": m["microrregiao"]["mesorregiao"]["UF"]["sigla"],
                }
        return None
    except Exception:
        return None


# ─── Nominatim ────────────────────────────────────────────────

def _nominatim_geocode(place_name: str) -> dict | None:
    """Call Nominatim API for geocoding. Returns dict with lat, lon, display_name or None."""
    query = urllib.parse.quote(place_name)
    url = (
        f"https://nominatim.openstreetmap.org/search"
        f"?q={query}&format=json&limit=1&countrycodes=br"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GeoportalBot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if not data:
            return None
        hit = data[0]
        return {
            "lat": round(float(hit["lat"]), 6),
            "lon": round(float(hit["lon"]), 6),
            "display_name": hit.get("display_name", place_name),
        }
    except Exception:
        return None


def _nominatim_reverse(lat: float, lon: float) -> dict | None:
    """Call Nominatim reverse geocoding. Returns dict with municipio, uf, estado or None."""
    url = (
        f"https://nominatim.openstreetmap.org/reverse"
        f"?lat={lat}&lon={lon}&format=json&zoom=10"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GeoportalBot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        addr = data.get("address", {})
        return {
            "municipio": addr.get("city") or addr.get("town") or addr.get("municipality"),
            "uf": addr.get("state"),
            "display_name": data.get("display_name", ""),
        }
    except Exception:
        return None


def _osrm_route(
    o_lon: float, o_lat: float, d_lon: float, d_lat: float
) -> tuple[dict, float, int]:
    """Call OSRM public demo server. Returns (geojson_geom, distance_km, duration_min).
    Falls back to straight-line estimate if the request fails."""
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{o_lon},{o_lat};{d_lon},{d_lat}"
        f"?overview=full&geometries=geojson"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GeoportalBot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        route = data["routes"][0]
        geom = route["geometry"]  # GeoJSON LineString
        distance_km = round(route["distance"] / 1000, 1)
        duration_min = round(route["duration"] / 60)
        return geom, distance_km, duration_min
    except Exception:
        # Fallback: straight line with estimate
        straight_km = _haversine(o_lon, o_lat, d_lon, d_lat)
        road_km = round(straight_km * 1.3, 1)
        geom = {"type": "LineString", "coordinates": [[o_lon, o_lat], [d_lon, d_lat]]}
        return geom, road_km, round(road_km / 80 * 60)


def _centroid(geom: dict) -> tuple[float, float]:
    """Return (lon, lat) centroid of a geometry."""
    gtype = geom.get("type", "")
    coords = geom.get("coordinates", [])
    if gtype == "Point":
        return coords[0], coords[1]
    if gtype == "LineString":
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return sum(lons) / len(lons), sum(lats) / len(lats)
    if gtype == "Polygon" and coords:
        ring = coords[0]
        lons = [c[0] for c in ring]
        lats = [c[1] for c in ring]
        return sum(lons) / len(lons), sum(lats) / len(lats)
    return 0.0, 0.0


def _bbox(geom: dict) -> tuple[float, float, float, float]:
    """Return (min_lon, min_lat, max_lon, max_lat) bounding box."""
    gtype = geom.get("type", "")
    coords = geom.get("coordinates", [])
    points = []
    if gtype == "Point":
        points = [coords]
    elif gtype == "LineString":
        points = coords
    elif gtype == "Polygon" and coords:
        points = coords[0]
    if not points:
        return (0, 0, 0, 0)
    lons = [p[0] for p in points]
    lats = [p[1] for p in points]
    return min(lons), min(lats), max(lons), max(lats)


def _bboxes_intersect(a: dict, b: dict) -> bool:
    """Check if bounding boxes of two geometries overlap."""
    a_min_lon, a_min_lat, a_max_lon, a_max_lat = _bbox(a)
    b_min_lon, b_min_lat, b_max_lon, b_max_lat = _bbox(b)
    # Expand by small margin for point-in-polygon approximate checks
    margin = 0.05  # ~5km
    return not (
        a_max_lon + margin < b_min_lon
        or b_max_lon + margin < a_min_lon
        or a_max_lat + margin < b_min_lat
        or b_max_lat + margin < a_min_lat
    )


def _line_length_km(geom: dict) -> float:
    """Compute total length of a LineString in km."""
    coords = geom.get("coordinates", [])
    total = 0.0
    for i in range(len(coords) - 1):
        total += _haversine(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
    return round(total, 1)


def _polygon_area_km2(geom: dict) -> float:
    """Approximate area of a polygon using the shoelace formula on lat/lon (rough)."""
    coords = geom.get("coordinates", [[]])
    ring = coords[0] if coords else []
    if len(ring) < 3:
        return 0.0
    # Convert to approximate km using latitude
    center_lat = sum(c[1] for c in ring) / len(ring)
    km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))
    km_per_deg_lat = 110.574
    # Shoelace
    n = len(ring)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        xi = ring[i][0] * km_per_deg_lon
        yi = ring[i][1] * km_per_deg_lat
        xj = ring[j][0] * km_per_deg_lon
        yj = ring[j][1] * km_per_deg_lat
        area += xi * yj - xj * yi
    return round(abs(area) / 2.0, 1)


class ToolHandlers:
    def __init__(self, geometry_store: GeometryStore):
        self.gs = geometry_store

    def dispatch(self, name: str, args: dict) -> dict:
        handler = getattr(self, name, None)
        if handler is None:
            return {"error": f"Unknown tool: {name}"}
        return handler(**args)

    # ─── Geographic lookups ─────────────────────────────────────

    def geocode(self, place_name: str) -> dict:
        # Try real geocoding via Nominatim first
        hit = None if USE_SYNTHETIC_ONLY else _nominatim_geocode(place_name)
        if hit:
            ref = self.gs.put(
                {"type": "Point", "coordinates": [hit["lon"], hit["lat"]]},
                label=hit["display_name"],
            )
            return {"lat": hit["lat"], "lon": hit["lon"], "display_name": hit["display_name"], "geometry_ref": ref}
        # Fallback to synthetic data
        match = _fuzzy_find(place_name, GEOCODE_RESULTS)
        if not match:
            return {"error": f"Place '{place_name}' not found"}
        _, v = match
        ref = self.gs.put(
            {"type": "Point", "coordinates": [v["lon"], v["lat"]]},
            label=v["display_name"],
        )
        return {"lat": v["lat"], "lon": v["lon"], "display_name": v["display_name"], "geometry_ref": ref}

    def create_point(self, lat: float, lon: float, label: str = None) -> dict:
        lbl = label or f"point_{lat}_{lon}"
        ref = self.gs.put({"type": "Point", "coordinates": [lon, lat]}, label=lbl)
        return {"lat": lat, "lon": lon, "geometry_ref": ref}

    def reverse_geocode(self, lat: float = None, lon: float = None, geometry_ref: str = None) -> dict:
        if geometry_ref:
            try:
                geom = self.gs.get(geometry_ref)
            except KeyError:
                return {"error": f"Unknown geometry_ref: {geometry_ref}"}
            lon, lat = _centroid(geom)
        if lat is None or lon is None:
            return {"error": "Provide lat/lon or geometry_ref"}
        # Try real reverse geocoding via Nominatim first
        hit = None if USE_SYNTHETIC_ONLY else _nominatim_reverse(lat, lon)
        if hit and hit.get("municipio"):
            return {
                "municipio": hit["municipio"], "uf": hit.get("uf", ""),
                "estado": hit.get("uf", ""),
                "lat": lat, "lon": lon,
            }
        # Fallback to synthetic data
        for (_nome, _uf), m in MUNICIPALITIES.items():
            m_bbox = _bbox(m["geometry"])
            margin = 0.05
            if (m_bbox[0] - margin <= lon <= m_bbox[2] + margin and
                    m_bbox[1] - margin <= lat <= m_bbox[3] + margin):
                return {
                    "municipio": m["nome"], "uf": m["uf"],
                    "estado": STATES.get(m["uf"].lower(), {}).get("nome", m["uf"]),
                    "lat": lat, "lon": lon,
                }
        return {"municipio": None, "uf": None, "estado": None, "lat": lat, "lon": lon,
                "note": "Coordinates outside known municipalities"}

    def _municipality_result(self, m: dict) -> dict:
        ref = self.gs.put(m["geometry"], label=f"municipio_{m['nome']}")
        return {"nome": m["nome"], "uf": m["uf"], "codigo_ibge": m.get("codigo_ibge", ""), "populacao": m.get("populacao", 0), "geometry_ref": ref}

    def search_municipality(self, nome: str, uf: str = None) -> dict:
        # Try synthetic data first (fast, has population)
        key = (nome.lower().strip(), uf.lower().strip() if uf else None)
        if key[1] and key in MUNICIPALITIES:
            return self._municipality_result(MUNICIPALITIES[key])
        matches = [v for k, v in MUNICIPALITIES.items() if k[0] == key[0]]
        if len(matches) == 1:
            return self._municipality_result(matches[0])
        if len(matches) > 1:
            return {"ambiguous": True, "candidates": [{"nome": m["nome"], "uf": m["uf"]} for m in matches]}
        # Fallback: try Nominatim for real municipality boundary
        hit = None if USE_SYNTHETIC_ONLY else _nominatim_municipality(nome, uf)
        if hit:
            ibge = _ibge_population(nome, uf)
            m = {
                "nome": hit["nome"],
                "uf": hit["uf"],
                "geometry": hit["geometry"],
                "codigo_ibge": ibge["codigo_ibge"] if ibge else "",
                "populacao": 0,
            }
            return self._municipality_result(m)
        return {"error": f"Municipality '{nome}' not found"}

    def search_state(self, uf: str) -> dict:
        key = uf.lower().strip()
        if key in STATES:
            s = STATES[key]
            ref = self.gs.put(s["geometry"], label=f"estado_{s['uf']}")
            return {"uf": s["uf"], "nome": s["nome"], "geometry_ref": ref}
        return {"error": f"State '{uf}' not found"}

    def search_named_region(self, nome: str) -> dict:
        match = _fuzzy_find(nome, NAMED_REGIONS)
        if not match:
            return {"error": f"Region '{nome}' not found"}
        _, v = match
        ref = self.gs.put(v["geometry"], label=f"regiao_{v['nome']}")
        return {"nome": v["nome"], "geometry_ref": ref}

    def search_products(self, geometry_ref: str, tipo: str = None, escala: int = None,
                        data_inicio: str = None, data_fim: str = None, **kwargs) -> dict:
        results = []
        for p in PRODUCTS:
            if tipo and tipo != "*" and p["tipo"] != tipo:
                continue
            if escala and p.get("escala") != escala:
                continue
            if data_inicio and p["data_produto"] < data_inicio:
                continue
            if data_fim and p["data_produto"] > data_fim:
                continue
            results.append(_format_product(p))
        return {"total": len(results), "products": results}

    def buffer(self, geometry_ref: str, raio_metros: float) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        raio_metros = max(1.0, float(raio_metros))
        cx, cy = _centroid(geom)
        delta_lat = raio_metros / 110574.0
        delta_lon = raio_metros / (111320.0 * max(0.01, abs(math.cos(math.radians(cy)))))
        # Approximate circle with 64 vertices
        n_pts = 64
        ring = []
        for i in range(n_pts + 1):
            angle = 2 * math.pi * (i % n_pts) / n_pts
            ring.append([cx + delta_lon * math.cos(angle), cy + delta_lat * math.sin(angle)])
        buffered = {"type": "Polygon", "coordinates": [ring]}
        ref = self.gs.put(buffered, label=f"buffer_{raio_metros}m")
        return {"geometry_ref": ref, "type": "Polygon", "description": f"Buffer de {raio_metros}m aplicado"}

    def intersect(self, geometry_ref_a: str, geometry_ref_b: str) -> dict:
        try:
            geom_a = self.gs.get(geometry_ref_a)
            geom_b = self.gs.get(geometry_ref_b)
        except KeyError:
            ref = self.gs.put({"type": "Polygon", "coordinates": [[]]}, label="intersect_result")
            return {"geometry_ref": ref, "area_km2": 0, "is_empty": True}
        if _bboxes_intersect(geom_a, geom_b):
            ref = self.gs.put({"type": "Polygon", "coordinates": [[]]}, label="intersect_result")
            # Approximate intersection area as overlap of bboxes
            a = _bbox(geom_a)
            b = _bbox(geom_b)
            overlap_lon = max(0, min(a[2], b[2]) - max(a[0], b[0]))
            overlap_lat = max(0, min(a[3], b[3]) - max(a[1], b[1]))
            clat = (max(a[1], b[1]) + min(a[3], b[3])) / 2
            area = overlap_lon * 111.32 * math.cos(math.radians(clat)) * overlap_lat * 110.574
            return {"geometry_ref": ref, "area_km2": round(area, 1), "is_empty": False}
        ref = self.gs.put({"type": "Polygon", "coordinates": [[]]}, label="intersect_empty")
        return {"geometry_ref": ref, "area_km2": 0, "is_empty": True}

    def compute_route(self, origin_ref: str, dest_ref: str) -> dict:
        try:
            origin = self.gs.get(origin_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {origin_ref}"}
        try:
            dest = self.gs.get(dest_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {dest_ref}"}
        o_lon, o_lat = _centroid(origin)
        d_lon, d_lat = _centroid(dest)

        if USE_SYNTHETIC_ONLY:
            straight_km = _haversine(o_lon, o_lat, d_lon, d_lat)
            road_km = round(straight_km * 1.3, 1)
            route_geom = {"type": "LineString", "coordinates": [[o_lon, o_lat], [d_lon, d_lat]]}
            duration_min = round(road_km / 80 * 60)
        else:
            route_geom, road_km, duration_min = _osrm_route(o_lon, o_lat, d_lon, d_lat)

        ref = self.gs.put(route_geom, label="route")
        return {"distance_km": road_km, "duration_min": duration_min, "geometry_ref": ref}

    def search_hydrography(self, nome: str, tipo: str = None, uf: str = None) -> dict:
        # Try Overpass first
        hit = None if USE_SYNTHETIC_ONLY else _overpass_hydrography(nome)
        if hit:
            ref = self.gs.put(hit["geometry"], label=hit["nome"])
            return {"nome": hit["nome"], "tipo": hit["tipo"], "geometry_ref": ref}
        # Fallback to synthetic
        match = _fuzzy_find(nome, HYDROGRAPHY)
        if not match:
            return {"error": f"Hydrography '{nome}' not found"}
        _, v = match
        ref = self.gs.put(v["geometry"], label=v["nome"])
        return {"nome": v["nome"], "tipo": v["tipo"], "geometry_ref": ref}

    def search_border(self, pais: str, proximidade_ref: str = None, raio_m: float = None) -> dict:
        match = _fuzzy_find(pais, BORDERS)
        if not match:
            return {"error": f"Border with '{pais}' not found"}
        _, v = match
        ref = self.gs.put(v["geometry"], label=f"fronteira_{v['pais']}")
        return {"pais": v["pais"], "geometry_ref": ref}

    def search_features(self, tipo: str, geometry_ref: str, atributo: str = None,
                        operador: str = None, valor=None) -> dict:
        key = tipo.lower().strip()
        try:
            area_geom = self.gs.get(geometry_ref)
        except KeyError:
            area_geom = None
        # Try real Overpass search first
        if not USE_SYNTHETIC_ONLY and area_geom and key in _OSM_TAGS:
            bbox = _bbox(area_geom)
            osm_feats = _overpass_features_in_bbox(key, bbox)
            if osm_feats:
                results = []
                for f in osm_feats:
                    results.append(_feature_to_entry(f, self.gs))
                # Attribute filter
                if atributo and operador is not None and valor is not None:
                    op_fn = _ATTR_OPS.get(operador)
                    if op_fn:
                        results = [f for f in results if f.get(atributo) is not None
                                   and _safe_op(op_fn, f[atributo], valor)]
                return {"total": len(results), "features": results}
        # Fallback to synthetic data
        if key in FEATURES:
            results = []
            for f in FEATURES[key]:
                if area_geom and not _bboxes_intersect(f["geometry"], area_geom):
                    continue
                results.append(_feature_to_entry(f, self.gs))
            if atributo and operador is not None and valor is not None:
                op_fn = _ATTR_OPS.get(operador)
                if op_fn:
                    results = [f for f in results if f.get(atributo) is not None
                               and _safe_op(op_fn, f[atributo], valor)]
            return {"total": len(results), "features": results}
        return {"total": 0, "features": []}

    def search_military_installation(self, nome_ou_sigla: str, cidade: str = None) -> dict:
        # Try synthetic data first
        key = nome_ou_sigla.lower().strip()
        for k, v in MILITARY_INSTALLATIONS.items():
            if k in key or key in k or key in v["nome_completo"].lower() or key in v["sigla"].lower():
                ref = self.gs.put(v["geometry"], label=v["sigla"])
                return {
                    "nome_completo": v["nome_completo"],
                    "sigla": v["sigla"],
                    "cidade": v["cidade"],
                    "uf": v["uf"],
                    "geometry_ref": ref,
                }
        # Fallback: try Nominatim geocode
        if USE_SYNTHETIC_ONLY:
            return {"error": f"Military installation '{nome_ou_sigla}' not found"}
        search_term = f"{nome_ou_sigla} {cidade}" if cidade else nome_ou_sigla
        hit = _nominatim_geocode(search_term)
        if hit:
            ref = self.gs.put(
                {"type": "Point", "coordinates": [hit["lon"], hit["lat"]]},
                label=nome_ou_sigla,
            )
            return {
                "nome_completo": nome_ou_sigla,
                "sigla": nome_ou_sigla,
                "cidade": cidade or "",
                "uf": "",
                "geometry_ref": ref,
            }
        return {"error": f"Military installation '{nome_ou_sigla}' not found"}

    # ─── Spatial computation & analysis ─────────────────────────

    def compute_distance(self, geometry_ref_a: str, geometry_ref_b: str) -> dict:
        try:
            geom_a = self.gs.get(geometry_ref_a)
            geom_b = self.gs.get(geometry_ref_b)
        except KeyError as e:
            return {"error": f"Unknown geometry_ref: {e}"}
        lon_a, lat_a = _centroid(geom_a)
        lon_b, lat_b = _centroid(geom_b)
        dist = _haversine(lon_a, lat_a, lon_b, lat_b)
        return {"distance_km": round(dist, 1)}

    def compute_area(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        if geom.get("type") != "Polygon":
            return {"error": "Geometry is not a Polygon"}
        area = _polygon_area_km2(geom)
        return {"area_km2": area}

    def compute_length(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        if geom.get("type") != "LineString":
            return {"error": "Geometry is not a LineString"}
        length = _line_length_km(geom)
        return {"length_km": length}

    def find_nearest(self, tipo: str, geometry_ref: str, limit: int = 3) -> dict:
        try:
            ref_geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        ref_lon, ref_lat = _centroid(ref_geom)
        key = tipo.lower().strip()
        # Try Overpass: search in expanding radius around point
        if not USE_SYNTHETIC_ONLY and key in _OSM_TAGS:
            for radius_deg in (0.3, 0.8, 2.0):
                bbox = (ref_lon - radius_deg, ref_lat - radius_deg,
                        ref_lon + radius_deg, ref_lat + radius_deg)
                osm_feats = _overpass_features_in_bbox(key, bbox)
                if osm_feats:
                    candidates = []
                    for f in osm_feats:
                        f_lon, f_lat = _centroid(f["geometry"])
                        dist = _haversine(ref_lon, ref_lat, f_lon, f_lat)
                        candidates.append((dist, f))
                    candidates.sort(key=lambda x: x[0])
                    results = []
                    for dist, f in candidates[:limit]:
                        results.append(_feature_to_entry(f, self.gs, extra={"distance_km": round(dist, 1)}))
                    return {"total": len(results), "nearest": results}
        # Fallback to synthetic data
        if key not in FEATURES:
            return {"total": 0, "nearest": []}
        candidates = []
        for f in FEATURES[key]:
            f_lon, f_lat = _centroid(f["geometry"])
            dist = _haversine(ref_lon, ref_lat, f_lon, f_lat)
            candidates.append((dist, f))
        candidates.sort(key=lambda x: x[0])
        results = []
        for dist, f in candidates[:limit]:
            results.append(_feature_to_entry(f, self.gs, extra={"distance_km": round(dist, 1)}))
        return {"total": len(results), "nearest": results}

    def features_along_route(self, tipo: str, geometry_ref: str, buffer_metros: float = 500) -> dict:
        try:
            route_geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        # Create buffer around route and search features
        buf_result = self.buffer(geometry_ref, buffer_metros)
        return self.search_features(tipo=tipo, geometry_ref=buf_result["geometry_ref"])

    def check_intersection(self, geometry_ref_a: str, geometry_ref_b: str) -> dict:
        try:
            geom_a = self.gs.get(geometry_ref_a)
            geom_b = self.gs.get(geometry_ref_b)
        except KeyError as e:
            return {"error": f"Unknown geometry_ref: {e}"}
        intersects = _bboxes_intersect(geom_a, geom_b)
        return {"intersects": intersects}

    def check_contains(self, geometry_ref_a: str, geometry_ref_b: str) -> dict:
        try:
            geom_a = self.gs.get(geometry_ref_a)
            geom_b = self.gs.get(geometry_ref_b)
        except KeyError as e:
            return {"error": f"Unknown geometry_ref: {e}"}
        a_bbox = _bbox(geom_a)
        b_bbox = _bbox(geom_b)
        margin = 0.05
        contains = (
            a_bbox[0] - margin <= b_bbox[0]
            and a_bbox[1] - margin <= b_bbox[1]
            and a_bbox[2] + margin >= b_bbox[2]
            and a_bbox[3] + margin >= b_bbox[3]
        )
        return {"contains": contains}

    def search_road(self, identificador: str, uf: str = None) -> dict:
        # Try Overpass first
        hit = None if USE_SYNTHETIC_ONLY else _overpass_road(identificador)
        if hit:
            ref = self.gs.put(hit["geometry"], label=hit["nome"])
            return {
                "nome": hit["nome"],
                "descricao": hit["descricao"],
                "extensao_km": hit["extensao_km"],
                "geometry_ref": ref,
            }
        # Fallback to synthetic
        key = identificador.lower().strip()
        match = _fuzzy_find(key, ROADS)
        if not match:
            return {"error": f"Road '{identificador}' not found"}
        _, road = match
        if uf:
            uf_key = uf.lower().strip()
            if uf_key in road.get("trechos_uf", {}):
                trecho = road["trechos_uf"][uf_key]
                ref = self.gs.put(trecho["geometry"], label=f"{road['nome']}_{uf.upper()}")
                return {
                    "nome": road["nome"],
                    "descricao": road["descricao"],
                    "extensao_km": trecho["extensao_km"],
                    "geometry_ref": ref,
                }
        ref = self.gs.put(road["geometry"], label=road["nome"])
        return {
            "nome": road["nome"],
            "descricao": road["descricao"],
            "extensao_km": road["extensao_km"],
            "geometry_ref": ref,
        }

    def list_municipalities_in(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        geom_bbox = _bbox(geom)
        margin = 0.05
        results = []
        for (_nome, _uf), m in MUNICIPALITIES.items():
            m_bbox = _bbox(m["geometry"])
            if (geom_bbox[2] + margin < m_bbox[0] or m_bbox[2] + margin < geom_bbox[0]
                    or geom_bbox[3] + margin < m_bbox[1] or m_bbox[3] + margin < geom_bbox[1]):
                continue
            results.append({"nome": m["nome"], "uf": m["uf"], "populacao": m["populacao"]})
        results.sort(key=lambda x: x["populacao"], reverse=True)
        return {"total": len(results), "municipalities": results}

    def get_neighbors(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        my_bbox = _bbox(geom)
        margin = 0.5
        results = []
        for (_nome, _uf), m in MUNICIPALITIES.items():
            if m["geometry"] is geom:
                continue
            m_bbox = _bbox(m["geometry"])
            if (my_bbox[2] + margin < m_bbox[0] or m_bbox[2] + margin < my_bbox[0]
                    or my_bbox[3] + margin < m_bbox[1] or m_bbox[3] + margin < my_bbox[1]):
                continue
            results.append({"nome": m["nome"], "uf": m["uf"], "populacao": m["populacao"]})
        results.sort(key=lambda x: x["nome"])
        return {"total": len(results), "neighbors": results}

    def search_by_articulation(self, codigo: str) -> dict:
        code = codigo.upper().strip()
        results = []
        for p in PRODUCTS:
            art = p.get("articulacao")
            if art and code in art.upper():
                results.append(_format_product(p))
        if not results:
            return {"error": f"No products found for articulation '{codigo}'"}
        return {"total": len(results), "products": results}

    # ─── Elevation & terrain ───────────────────────────────────

    def get_elevation(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        gtype = geom.get("type", "")
        if gtype == "Point":
            lon, lat = geom["coordinates"][0], geom["coordinates"][1]
            elev = None if USE_SYNTHETIC_ONLY else _open_meteo_elevation(lat, lon)
            return {"elevation_m": elev if elev is not None else compute_elevation(lat, lon)}
        elif gtype == "Polygon":
            ring = geom.get("coordinates", [[]])[0]
            if not ring:
                return {"error": "Empty polygon"}
            lons = [c[0] for c in ring]
            lats = [c[1] for c in ring]
            points = []
            for i in range(5):
                for j in range(5):
                    slat = min(lats) + (max(lats) - min(lats)) * i / 4
                    slon = min(lons) + (max(lons) - min(lons)) * j / 4
                    points.append((slat, slon))
            elevations = None if USE_SYNTHETIC_ONLY else _open_meteo_elevations(points)
            if not elevations:
                elevations = [compute_elevation(lat, lon) for lat, lon in points]
            return {
                "min_elevation_m": min(elevations),
                "max_elevation_m": max(elevations),
                "avg_elevation_m": round(sum(elevations) / len(elevations), 1),
            }
        return {"error": f"Unsupported geometry type: {gtype}"}

    def get_terrain_profile(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        if geom.get("type") != "LineString":
            return {"error": "Geometry is not a LineString"}
        coords = geom.get("coordinates", [])
        if len(coords) < 2:
            return {"error": "LineString must have at least 2 points"}
        total_len = _line_length_km(geom)
        num_samples = min(20, max(2, len(coords) * 3))
        # Sample points along the line
        latlon_samples = []
        distances = []
        for i in range(num_samples):
            t = i / (num_samples - 1) if num_samples > 1 else 0
            target_km = t * total_len
            cum_km = 0.0
            for j in range(len(coords) - 1):
                seg_km = _haversine(coords[j][0], coords[j][1], coords[j + 1][0], coords[j + 1][1])
                if cum_km + seg_km >= target_km or j == len(coords) - 2:
                    frac = (target_km - cum_km) / seg_km if seg_km > 0 else 0
                    frac = max(0, min(1, frac))
                    lon = coords[j][0] + frac * (coords[j + 1][0] - coords[j][0])
                    lat = coords[j][1] + frac * (coords[j + 1][1] - coords[j][1])
                    latlon_samples.append((lat, lon))
                    distances.append(round(target_km, 1))
                    break
                cum_km += seg_km
        # Batch elevation query
        real_elevs = None if USE_SYNTHETIC_ONLY else _open_meteo_elevations(latlon_samples)
        sample_points = []
        for i, (lat, lon) in enumerate(latlon_samples):
            elev = real_elevs[i] if real_elevs else compute_elevation(lat, lon)
            sample_points.append({
                "distance_km": distances[i],
                "elevation_m": elev,
                "lat": round(lat, 4), "lon": round(lon, 4),
            })
        elevs = [p["elevation_m"] for p in sample_points]
        total_ascent = sum(max(0, elevs[i + 1] - elevs[i]) for i in range(len(elevs) - 1))
        total_descent = sum(max(0, elevs[i] - elevs[i + 1]) for i in range(len(elevs) - 1))
        max_slope = 0.0
        for i in range(len(sample_points) - 1):
            d = sample_points[i + 1]["distance_km"] - sample_points[i]["distance_km"]
            if d > 0:
                slope = abs(elevs[i + 1] - elevs[i]) / (d * 1000) * 100
                max_slope = max(max_slope, slope)
        if max_slope > 10:
            classification = "montanhoso"
        elif max_slope > 4:
            classification = "ondulado"
        else:
            classification = "plano"
        return {
            "points": sample_points,
            "min_m": min(elevs), "max_m": max(elevs),
            "avg_m": round(sum(elevs) / len(elevs), 1),
            "max_slope_pct": round(max_slope, 1),
            "total_ascent_m": round(total_ascent, 1),
            "total_descent_m": round(total_descent, 1),
            "classification": classification,
        }
