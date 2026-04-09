"""Tool implementations using real APIs and Shapely/pyproj for geometric operations."""

import gzip
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from . import geo
from .geometry_store import GeometryStore
from .synthetic_data import (
    BORDERS,
    MILITARY_INSTALLATIONS,
    NAMED_REGIONS,
    PRODUCTS,
)

_ATTR_OPS = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "=": lambda a, b: a == b,
    "in": lambda a, b: a in b,
}


def _normalize_refs(value) -> list[str]:
    """Accept a single string or a list of strings, return a list."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _safe_op(op_fn, a, b) -> bool:
    try:
        return op_fn(a, b)
    except (TypeError, ValueError):
        return False


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


_UA = {"User-Agent": "GeoportalBot/1.0"}


def _read_response(resp) -> bytes:
    """Read HTTP response, handling gzip encoding transparently."""
    raw = resp.read()
    if resp.headers.get("Content-Encoding") == "gzip" or raw[:2] == b'\x1f\x8b':
        return gzip.decompress(raw)
    return raw


def _fetch_json(url: str, timeout: int = 10, method: str = "GET",
                data: bytes = None) -> dict | list | None:
    """Fetch JSON from URL with gzip handling. Returns parsed JSON or None."""
    try:
        req = urllib.request.Request(url, data=data, headers=_UA)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(_read_response(resp))
    except Exception:
        return None


# ─── Open-Meteo Elevation API ─────────────────────────────────

def _open_meteo_elevations(points: list[tuple[float, float]]) -> list[float] | None:
    """Batch elevation query. points = [(lat, lon), ...]. Returns list of elevations or None."""
    if not points:
        return None
    lats = ",".join(str(round(p[0], 6)) for p in points)
    lons = ",".join(str(round(p[1], 6)) for p in points)
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lats}&longitude={lons}"
    data = _fetch_json(url, timeout=15)
    if not data:
        return None
    elevs = data.get("elevation", [])
    return [round(e, 1) for e in elevs] if len(elevs) == len(points) else None


def _open_meteo_elevation(lat: float, lon: float) -> float | None:
    """Get elevation for a single point. Delegates to batch API."""
    result = _open_meteo_elevations([(lat, lon)])
    return result[0] if result else None


# ─── Overpass (OSM) API ────────────────────────────────────────

_OSM_TAGS = {
    "ponte": [('way["bridge"="yes"]["highway"]',)],
    "tunel": [('way["tunnel"="yes"]["highway"]',)],
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


def _overpass_post(full_query: str, timeout: int = 25) -> dict | None:
    """Execute raw Overpass query with retry on 429. Returns parsed JSON or None."""
    import time as _time
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": full_query}).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=data, headers=_UA)
            with urllib.request.urlopen(req, timeout=timeout + 10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                _time.sleep(5 * (attempt + 1))
                continue
            return None
        except Exception:
            return None
    return None


def _overpass_query(query: str, timeout: int = 25) -> list[dict] | None:
    """Execute Overpass API query. Returns list of elements or None.

    Uses ``out geom`` so that ways/relations include full coordinate geometry
    instead of just the centroid.
    """
    full_query = f"[out:json][timeout:{timeout}];{query}out geom;"
    result = _overpass_post(full_query, timeout)
    return result.get("elements", []) if result else None


def _parse_overpass_geometry(el: dict) -> dict | None:
    """Extract GeoJSON geometry from an Overpass element.

    - Nodes → Point
    - Ways with ``geometry`` key (from ``out geom``) → LineString or Polygon
    - Falls back to center coordinates if available.
    """
    el_type = el.get("type")
    if el_type == "node":
        lat, lon = el.get("lat"), el.get("lon")
        if lat is not None and lon is not None:
            return {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]}
    elif el_type == "way" and "geometry" in el:
        coords = [[round(pt["lon"], 6), round(pt["lat"], 6)] for pt in el["geometry"]]
        if len(coords) >= 2:
            # Closed way → Polygon, open way → LineString
            if coords[0] == coords[-1] and len(coords) >= 4:
                return {"type": "Polygon", "coordinates": [coords]}
            return {"type": "LineString", "coordinates": coords}
    # Fallback: center (for relations or ways without full geom)
    center = el.get("center", {})
    lat = center.get("lat") or el.get("lat")
    lon = center.get("lon") or el.get("lon")
    if lat is not None and lon is not None:
        return {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]}
    return None


def _overpass_features_in_bbox(tipo: str, bbox: tuple[float, float, float, float],
                                limit: int = 50) -> list[dict] | None:
    """Search OSM features by type within bounding box. Returns feature dicts or None."""
    tags = _OSM_TAGS.get(tipo)
    if not tags:
        return None
    south, west, north, east = bbox[1], bbox[0], bbox[3], bbox[2]
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
        geometry = _parse_overpass_geometry(el)
        if geometry is None:
            continue
        tags_data = el.get("tags", {})
        nome = tags_data.get("name", tags_data.get("ref", f"{tipo}_{el['id']}"))
        feat = {"nome": nome, "geometry": geometry}
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


def _merge_way_segments(segments: list[list[list[float]]]) -> list[list[float]]:
    """Merge ordered way segments into a single coordinate list.

    Overpass returns multiple way elements for a single river/road, but they
    may arrive in arbitrary order. This function chains them by matching
    endpoints (last coord of one segment ≈ first coord of the next) using a
    greedy nearest-endpoint approach.
    """
    if not segments:
        return []
    if len(segments) == 1:
        return segments[0]

    remaining = list(segments)
    merged = remaining.pop(0)

    while remaining:
        head = merged[0]
        tail = merged[-1]
        best_idx = None
        best_dist = float("inf")
        best_flip = False
        best_end = "tail"  # append to tail or prepend to head

        for i, seg in enumerate(remaining):
            if not seg:
                continue
            seg_start = seg[0]
            seg_end = seg[-1]
            # tail → seg_start (natural append)
            d = (tail[0] - seg_start[0]) ** 2 + (tail[1] - seg_start[1]) ** 2
            if d < best_dist:
                best_dist, best_idx, best_flip, best_end = d, i, False, "tail"
            # tail → seg_end (reversed append)
            d = (tail[0] - seg_end[0]) ** 2 + (tail[1] - seg_end[1]) ** 2
            if d < best_dist:
                best_dist, best_idx, best_flip, best_end = d, i, True, "tail"
            # head → seg_end (natural prepend)
            d = (head[0] - seg_end[0]) ** 2 + (head[1] - seg_end[1]) ** 2
            if d < best_dist:
                best_dist, best_idx, best_flip, best_end = d, i, False, "head"
            # head → seg_start (reversed prepend)
            d = (head[0] - seg_start[0]) ** 2 + (head[1] - seg_start[1]) ** 2
            if d < best_dist:
                best_dist, best_idx, best_flip, best_end = d, i, True, "head"

        if best_idx is None:
            break
        seg = remaining.pop(best_idx)
        if best_flip:
            seg = list(reversed(seg))
        if best_end == "tail":
            # skip duplicate junction point
            if merged[-1] == seg[0]:
                merged.extend(seg[1:])
            else:
                merged.extend(seg)
        else:
            if seg[-1] == merged[0]:
                merged = seg[:-1] + merged
            else:
                merged = seg + merged

    return merged


def _overpass_hydrography(nome: str) -> dict | None:
    """Search hydrography by name via Overpass with full geometry. Returns dict or None."""
    escaped = nome.replace('"', '\\"')
    full_query = (
        f'[out:json][timeout:15];'
        f'('
        f'way["waterway"]["name"~"{escaped}",i](-35,-58,-27,-49);'
        f'relation["waterway"]["name"~"{escaped}",i](-35,-58,-27,-49);'
        f'way["natural"="water"]["name"~"{escaped}",i](-35,-58,-27,-49);'
        f');out geom;'
    )
    result = _overpass_post(full_query, timeout=20)
    if not result:
        return None
    elements = result.get("elements", [])
    if not elements:
        return None
    segments = []
    tags = elements[0].get("tags", {})
    for el in elements:
        if el.get("geometry"):
            coords = [[p["lon"], p["lat"]] for p in el["geometry"]]
            if len(coords) >= 2:
                segments.append(coords)
        elif el.get("members"):
            for member in el["members"]:
                if member.get("geometry"):
                    coords = [[p["lon"], p["lat"]] for p in member["geometry"]]
                    if len(coords) >= 2:
                        segments.append(coords)
    tipo_map = {"river": "rio", "stream": "arroio", "canal": "canal", "lake": "lago",
                "reservoir": "reservatorio"}
    ww = tags.get("waterway", tags.get("natural", ""))
    tipo = tipo_map.get(ww, ww)
    merged = _merge_way_segments(segments)
    if not merged:
        return None
    geom = {"type": "LineString", "coordinates": merged}
    return {"nome": tags.get("name", nome), "tipo": tipo, "geometry": geom}


def _overpass_road(identificador: str) -> dict | None:
    """Search road by ref (e.g. BR-290) via Overpass. Returns dict or None."""
    raw = identificador.upper().strip().replace(" ", "").replace("_", "")
    m = re.match(r"(BR|RS|SC|PR|SP|MG|MT|MS|GO|BA|RJ|ES)[-]?(\d+)", raw)
    if m:
        ref_clean = f"{m.group(1)}-{m.group(2)}"
    else:
        ref_clean = identificador.strip()
    escaped = ref_clean.replace('"', '\\"')
    full_query = (
        f'[out:json][timeout:25];'
        f'('
        f'way["highway"~"trunk|primary"]["ref"~"{escaped}"](-34,-58,-27,-49);'
        f');out geom;'
    )
    result = _overpass_post(full_query, timeout=25)
    if not result:
        return None
    elements = result.get("elements", [])
    if not elements:
        return None
    segments = []
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
            if len(coords) >= 2:
                segments.append(coords)
    merged = _merge_way_segments(segments)
    if not merged:
        return None
    nome = f"Rodovia {ref_tag}"
    geom = {"type": "LineString", "coordinates": merged}
    extensao_km = geo.length_km(geom)
    return {
        "nome": nome,
        "ref": ref_tag,
        "descricao": road_name or nome,
        "extensao_km": extensao_km,
        "geometry": geom,
    }


# ─── IBGE APIs ───────────────────────────────────────────────

def _ibge_find_municipality(nome: str, uf: str = None) -> dict | None:
    """Search municipality by name via IBGE API. Returns dict with id, nome, uf or None."""
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
    data = _fetch_json(url, timeout=15)
    if not data:
        return None
    nome_lower = nome.lower().strip()
    for m in data:
        if m["nome"].lower() == nome_lower:
            m_uf = m["microrregiao"]["mesorregiao"]["UF"]["sigla"]
            if uf and m_uf.lower() != uf.lower():
                continue
            return {
                "codigo_ibge": str(m["id"]),
                "nome": m["nome"],
                "uf": m_uf,
            }
    return None


def _ibge_malha(codigo: str, tipo: str = "municipios") -> dict | None:
    """Get GeoJSON geometry from IBGE Malhas API.
    tipo: 'estados' for state (2-digit code), 'municipios' for municipality (7-digit code)."""
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/malhas/{tipo}/{codigo}"
        f"?formato=application/vnd.geo+json&qualidade=intermediaria"
    )
    data = _fetch_json(url, timeout=15)
    if not data:
        return None
    features = data.get("features", [])
    if not features:
        return None
    geom = features[0].get("geometry")
    if not geom:
        return None
    # Simplify large geometries
    if geom.get("type") == "MultiPolygon":
        largest = max(geom["coordinates"], key=lambda p: len(p[0]) if p else 0)
        geom = {"type": "Polygon", "coordinates": largest}
    if geom.get("type") == "Polygon":
        ring = geom["coordinates"][0]
        if len(ring) > 300:
            step = max(1, len(ring) // 300)
            geom["coordinates"] = [ring[::step] + [ring[0]]]
    return geom


def _ibge_state(uf: str) -> dict | None:
    """Get state info + geometry from IBGE APIs. Returns dict or None."""
    uf_codes = {
        "ac": ("12", "Acre"), "al": ("27", "Alagoas"), "ap": ("16", "Amapa"),
        "am": ("13", "Amazonas"), "ba": ("29", "Bahia"), "ce": ("23", "Ceara"),
        "df": ("53", "Distrito Federal"), "es": ("32", "Espirito Santo"),
        "go": ("52", "Goias"), "ma": ("21", "Maranhao"), "mt": ("51", "Mato Grosso"),
        "ms": ("50", "Mato Grosso do Sul"), "mg": ("31", "Minas Gerais"),
        "pa": ("15", "Para"), "pb": ("25", "Paraiba"), "pr": ("41", "Parana"),
        "pe": ("26", "Pernambuco"), "pi": ("22", "Piaui"),
        "rj": ("33", "Rio de Janeiro"), "rn": ("24", "Rio Grande do Norte"),
        "rs": ("43", "Rio Grande do Sul"), "ro": ("11", "Rondonia"),
        "rr": ("14", "Roraima"), "sc": ("42", "Santa Catarina"),
        "sp": ("35", "Sao Paulo"), "se": ("28", "Sergipe"), "to": ("17", "Tocantins"),
    }
    key = uf.lower().strip()
    if key not in uf_codes:
        return None
    codigo, nome = uf_codes[key]
    geom = _ibge_malha(codigo, tipo="estados")
    if not geom:
        return None
    return {"nome": nome, "uf": key.upper(), "geometry": geom}


def _ibge_municipality(nome: str, uf: str = None) -> dict | None:
    """Search municipality via IBGE APIs (localidades + malhas). Returns dict or None."""
    info = _ibge_find_municipality(nome, uf)
    if not info:
        return None
    geom = _ibge_malha(info["codigo_ibge"], tipo="municipios")
    if not geom:
        return None
    return {
        "nome": info["nome"],
        "uf": info["uf"],
        "codigo_ibge": info["codigo_ibge"],
        "geometry": geom,
    }



def _nominatim_geocode(place_name: str) -> dict | None:
    """Call Nominatim API for geocoding. Returns dict with lat, lon, display_name or None."""
    query = urllib.parse.quote(place_name)
    url = (
        f"https://nominatim.openstreetmap.org/search"
        f"?q={query}&format=json&limit=1&countrycodes=br"
    )
    data = _fetch_json(url, timeout=10)
    if not data:
        return None
    hit = data[0]
    return {
        "lat": round(float(hit["lat"]), 6),
        "lon": round(float(hit["lon"]), 6),
        "display_name": hit.get("display_name", place_name),
    }


def _nominatim_reverse(lat: float, lon: float) -> dict | None:
    """Call Nominatim reverse geocoding. Returns dict with municipio, uf, estado or None."""
    url = (
        f"https://nominatim.openstreetmap.org/reverse"
        f"?lat={lat}&lon={lon}&format=json&zoom=10"
    )
    data = _fetch_json(url, timeout=10)
    if not data:
        return None
    addr = data.get("address", {})
    return {
        "municipio": addr.get("city") or addr.get("town") or addr.get("municipality"),
        "uf": addr.get("state"),
        "display_name": data.get("display_name", ""),
    }



def _overpass_border(pais: str) -> dict | None:
    """Search international border via Overpass. Returns dict or None."""
    country_map = {
        "argentina": "Argentina", "uruguai": "Uruguay", "uruguay": "Uruguay",
        "paraguai": "Paraguay", "paraguay": "Paraguay", "bolivia": "Bolivia",
        "peru": "Peru", "colombia": "Colombia", "venezuela": "Venezuela",
        "guiana": "Guyana", "guyana": "Guyana", "suriname": "Suriname",
        "guiana francesa": "French Guiana",
    }
    country_en = country_map.get(pais.lower().strip())
    if not country_en:
        return None
    escaped = country_en.replace('"', '\\"')
    full_query = (
        f'[out:json][timeout:30];'
        f'relation["type"="boundary"]["boundary"="administrative"]'
        f'["admin_level"="2"]["name:en"="{escaped}"];'
        f'out geom;'
    )
    result = _overpass_post(full_query, timeout=30)
    if not result:
        return None
    elements = result.get("elements", [])
    if not elements:
        return None
    all_coords = []
    for el in elements:
        for member in el.get("members", []):
            if member.get("geometry"):
                coords = [[p["lon"], p["lat"]] for p in member["geometry"]]
                all_coords.extend(coords)
    if not all_coords:
        return None
    geom = {"type": "LineString", "coordinates": all_coords}
    return {"pais": country_en, "geometry": geom}


def _osrm_route(
    o_lon: float, o_lat: float, d_lon: float, d_lat: float
) -> tuple[dict, float, int]:
    """Call OSRM for a 2-point route. Delegates to _osrm_route_waypoints."""
    return _osrm_route_waypoints([(o_lon, o_lat), (d_lon, d_lat)])


_WMO_WEATHER_CODES = {
    0: "Céu limpo", 1: "Principalmente limpo", 2: "Parcialmente nublado",
    3: "Nublado", 45: "Nevoeiro", 48: "Nevoeiro com geada",
    51: "Garoa leve", 53: "Garoa moderada", 55: "Garoa intensa",
    61: "Chuva leve", 63: "Chuva moderada", 65: "Chuva forte",
    71: "Neve leve", 73: "Neve moderada", 75: "Neve forte",
    80: "Pancadas leves", 81: "Pancadas moderadas", 82: "Pancadas fortes",
    95: "Trovoada", 96: "Trovoada com granizo leve", 99: "Trovoada com granizo forte",
}


def _open_meteo_weather(lat: float, lon: float) -> dict | None:
    """Get current weather from Open-Meteo API."""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        f"precipitation,rain,wind_speed_10m,wind_direction_10m,weather_code"
        f"&timezone=America/Sao_Paulo"
    )
    data = _fetch_json(url, timeout=10)
    if not data or "current" not in data:
        return None
    c = data["current"]
    return {
        "temperature_c": c.get("temperature_2m"),
        "apparent_temperature_c": c.get("apparent_temperature"),
        "humidity_pct": c.get("relative_humidity_2m"),
        "precipitation_mm": c.get("precipitation"),
        "rain_mm": c.get("rain"),
        "wind_speed_kmh": c.get("wind_speed_10m"),
        "wind_direction_deg": c.get("wind_direction_10m"),
        "weather_code": c.get("weather_code"),
        "conditions": _WMO_WEATHER_CODES.get(c.get("weather_code", -1), "Desconhecido"),
    }


def _osrm_route_waypoints(
    points: list[tuple[float, float]],
) -> tuple[dict, float, int]:
    """OSRM route through multiple waypoints. points = [(lon, lat), ...].
    Returns (geojson_geom, distance_km, duration_min)."""
    coords_str = ";".join(f"{lon},{lat}" for lon, lat in points)
    url = (
        f"http://router.project-osrm.org/route/v1/driving/{coords_str}"
        f"?overview=full&geometries=geojson"
    )
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        route = data["routes"][0]
        geom = route["geometry"]
        distance_km = round(route["distance"] / 1000, 1)
        duration_min = round(route["duration"] / 60)
        return geom, distance_km, duration_min
    except Exception:
        geom = {"type": "LineString", "coordinates": [list(p) for p in points]}
        total_km = sum(
            geo.haversine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
            for i in range(len(points) - 1)
        )
        road_km = round(total_km * 1.3, 1)
        return geom, road_km, round(road_km / 80 * 60)


def _overpass_municipalities_in_bbox(bbox_tuple: tuple[float, float, float, float],
                                      limit: int = 100) -> list[dict] | None:
    """Search municipalities (admin_level=8) in a bounding box via Overpass."""
    min_lon, min_lat, max_lon, max_lat = bbox_tuple
    full_query = (
        f'[out:json][timeout:25];'
        f'('
        f'relation["boundary"="administrative"]["admin_level"="8"]'
        f'({min_lat},{min_lon},{max_lat},{max_lon});'
        f');out tags center;'
    )
    result = _overpass_post(full_query, timeout=25)
    if not result:
        return None
    elements = result.get("elements", [])
    if not elements:
        return None
    municipalities = []
    for el in elements[:limit]:
        tags = el.get("tags", {})
        center = el.get("center", {})
        nome = tags.get("name", "")
        if not nome:
            continue
        municipalities.append({
            "nome": nome,
            "uf": tags.get("ISO3166-2", "").replace("BR-", ""),
            "populacao": int(tags["population"]) if tags.get("population") else 0,
            "lat": center.get("lat"),
            "lon": center.get("lon"),
        })
    municipalities.sort(key=lambda x: x["populacao"], reverse=True)
    return municipalities


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
        hit = _nominatim_geocode(place_name)
        if not hit:
            return {"error": f"Place '{place_name}' not found"}
        ref = self.gs.put(
            {"type": "Point", "coordinates": [hit["lon"], hit["lat"]]},
            label=hit["display_name"],
        )
        return {"lat": hit["lat"], "lon": hit["lon"], "display_name": hit["display_name"],
                "geometry_ref": ref}

    def create_point(self, lat: float, lon: float, label: str = None) -> dict:
        lbl = label or f"point_{lat}_{lon}"
        ref = self.gs.put({"type": "Point", "coordinates": [lon, lat]}, label=lbl)
        return {"lat": lat, "lon": lon, "geometry_ref": ref}

    def reverse_geocode(self, lat: float = None, lon: float = None,
                        geometry_ref: str = None) -> dict:
        if geometry_ref:
            try:
                geom = self.gs.get(geometry_ref)
            except KeyError:
                return {"error": f"Unknown geometry_ref: {geometry_ref}"}
            lon, lat = geo.centroid(geom)
        if lat is None or lon is None:
            return {"error": "Provide lat/lon or geometry_ref"}
        hit = _nominatim_reverse(lat, lon)
        if hit and hit.get("municipio"):
            return {
                "municipio": hit["municipio"], "uf": hit.get("uf", ""),
                "estado": hit.get("uf", ""),
                "lat": lat, "lon": lon,
            }
        return {"municipio": None, "uf": None, "estado": None, "lat": lat, "lon": lon,
                "note": "Could not resolve coordinates"}

    def _municipality_result(self, m: dict) -> dict:
        ref = self.gs.put(m["geometry"], label=f"municipio_{m['nome']}")
        return {"nome": m["nome"], "uf": m["uf"],
                "codigo_ibge": m.get("codigo_ibge", ""),
                "populacao": m.get("populacao", 0),
                "area_km2": geo.area_km2(m["geometry"]),
                "geometry_ref": ref}

    def search_municipality(self, nome: str, uf: str = None) -> dict:
        hit = _ibge_municipality(nome, uf)
        if hit:
            return self._municipality_result(hit)
        return {"error": f"Municipality '{nome}' not found"}

    def search_state(self, uf: str) -> dict:
        hit = _ibge_state(uf)
        if hit:
            ref = self.gs.put(hit["geometry"], label=f"estado_{hit['uf']}")
            return {"uf": hit["uf"], "nome": hit["nome"],
                    "area_km2": geo.area_km2(hit["geometry"]),
                    "geometry_ref": ref}
        return {"error": f"State '{uf}' not found"}

    def search_named_region(self, nome: str) -> dict:
        key = nome.lower().strip()
        # Domain data — named regions are Geoportal-specific
        for k, v in NAMED_REGIONS.items():
            if k in key or key in k:
                ref = self.gs.put(v["geometry"], label=f"regiao_{v['nome']}")
                return {"nome": v["nome"],
                        "area_km2": geo.area_km2(v["geometry"]),
                        "geometry_ref": ref}
        return {"error": f"Region '{nome}' not found"}

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

    def buffer(self, geometry_ref, raio_metros: float) -> dict:
        refs = _normalize_refs(geometry_ref)
        raio_metros = max(1.0, float(raio_metros))
        if len(refs) == 1:
            try:
                geom = self.gs.get(refs[0])
            except KeyError:
                return {"error": f"Unknown geometry_ref: {refs[0]}"}
            buffered = geo.buffer_meters(geom, raio_metros)
            ref = self.gs.put(buffered, label=f"buffer_{raio_metros}m")
            return {"geometry_ref": ref, "type": "Polygon",
                    "area_km2": geo.area_km2(buffered),
                    "description": f"Buffer de {raio_metros}m aplicado"}
        results = []
        for r in refs:
            try:
                geom = self.gs.get(r)
            except KeyError:
                results.append({"input_ref": r, "error": f"Unknown geometry_ref: {r}"})
                continue
            buffered = geo.buffer_meters(geom, raio_metros)
            new_ref = self.gs.put(buffered, label=f"buffer_{raio_metros}m")
            results.append({"input_ref": r, "geometry_ref": new_ref,
                            "area_km2": geo.area_km2(buffered)})
        return {"total": len(results), "results": results,
                "description": f"Buffer de {raio_metros}m aplicado a {len(refs)} geometrias"}

    def intersect(self, geometry_ref_a: str, geometry_ref_b: str) -> dict:
        try:
            geom_a = self.gs.get(geometry_ref_a)
            geom_b = self.gs.get(geometry_ref_b)
        except KeyError:
            ref = self.gs.put({"type": "GeometryCollection", "geometries": []},
                              label="intersect_empty")
            return {"geometry_ref": ref, "area_km2": 0, "is_empty": True}
        result_geojson = geo.intersection(geom_a, geom_b)
        is_empty = geo.to_shape(result_geojson).is_empty
        ref = self.gs.put(result_geojson, label="intersect_result")
        area = geo.area_km2(result_geojson) if not is_empty else 0
        return {"geometry_ref": ref, "area_km2": area, "is_empty": is_empty}

    def compute_route(self, origin_ref: str, dest_ref: str) -> dict:
        try:
            origin = self.gs.get(origin_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {origin_ref}"}
        try:
            dest = self.gs.get(dest_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {dest_ref}"}
        o_lon, o_lat = geo.centroid(origin)
        d_lon, d_lat = geo.centroid(dest)
        route_geom, road_km, duration_min = _osrm_route(o_lon, o_lat, d_lon, d_lat)
        ref = self.gs.put(route_geom, label="route")
        return {"distance_km": road_km, "duration_min": duration_min,
                "length_km": geo.length_km(route_geom),
                "geometry_ref": ref}

    def search_hydrography(self, nome: str, tipo: str = None, uf: str = None) -> dict:
        hit = _overpass_hydrography(nome)
        if hit:
            ref = self.gs.put(hit["geometry"], label=hit["nome"])
            return {"nome": hit["nome"], "tipo": hit["tipo"],
                    "length_km": geo.length_km(hit["geometry"]),
                    "geometry_ref": ref}
        return {"error": f"Hydrography '{nome}' not found"}

    def search_border(self, pais: str, proximidade_ref: str = None,
                      raio_m: float = None) -> dict:
        # Try domain data first (fast)
        key = pais.lower().strip()
        for k, v in BORDERS.items():
            if k in key or key in k:
                ref = self.gs.put(v["geometry"], label=f"fronteira_{v['pais']}")
                return {"pais": v["pais"],
                        "length_km": geo.length_km(v["geometry"]),
                        "geometry_ref": ref}
        # Fallback: Overpass
        hit = _overpass_border(pais)
        if hit:
            ref = self.gs.put(hit["geometry"], label=f"fronteira_{hit['pais']}")
            return {"pais": hit["pais"],
                    "length_km": geo.length_km(hit["geometry"]),
                    "geometry_ref": ref}
        return {"error": f"Border with '{pais}' not found"}

    def _search_features_single(self, key: str, area_geom: dict,
                                atributo=None, operador=None, valor=None) -> list[dict]:
        """Search features in a single area geometry. Returns list of feature entries."""
        bbox_tuple = geo.bbox(area_geom)
        osm_feats = _overpass_features_in_bbox(key, bbox_tuple)
        if not osm_feats:
            return []
        results = []
        for f in osm_feats:
            if geo.intersects(f["geometry"], area_geom):
                results.append(_feature_to_entry(f, self.gs))
        if atributo and operador is not None and valor is not None:
            op_fn = _ATTR_OPS.get(operador)
            if op_fn:
                results = [f for f in results if f.get(atributo) is not None
                           and _safe_op(op_fn, f[atributo], valor)]
        return results

    def search_features(self, tipo: str, geometry_ref=None, atributo: str = None,
                        operador: str = None, valor=None) -> dict:
        key = tipo.lower().strip()
        if key not in _OSM_TAGS:
            return {"total": 0, "features": [],
                    "note": f"Feature type '{tipo}' not supported"}
        refs = _normalize_refs(geometry_ref)
        all_results = []
        seen_names = set()
        for r in refs:
            try:
                area_geom = self.gs.get(r)
            except KeyError:
                continue
            for f in self._search_features_single(key, area_geom, atributo, operador, valor):
                if f["nome"] not in seen_names:
                    seen_names.add(f["nome"])
                    all_results.append(f)
        return {"total": len(all_results), "features": all_results}

    def search_military_installation(self, nome_ou_sigla: str,
                                      cidade: str = None) -> dict:
        # Domain data — military installations are Geoportal-specific
        key = nome_ou_sigla.lower().strip()
        for k, v in MILITARY_INSTALLATIONS.items():
            if (k in key or key in k or key in v["nome_completo"].lower()
                    or key in v["sigla"].lower()):
                ref = self.gs.put(v["geometry"], label=v["sigla"])
                return {
                    "nome_completo": v["nome_completo"],
                    "sigla": v["sigla"],
                    "cidade": v["cidade"],
                    "uf": v["uf"],
                    "geometry_ref": ref,
                }
        # Fallback: Nominatim geocode
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

    def search_road(self, identificador: str, uf: str = None) -> dict:
        hit = _overpass_road(identificador)
        if hit:
            ref = self.gs.put(hit["geometry"], label=hit["nome"])
            return {
                "nome": hit["nome"],
                "descricao": hit["descricao"],
                "extensao_km": hit["extensao_km"],
                "geometry_ref": ref,
            }
        return {"error": f"Road '{identificador}' not found"}

    # ─── Spatial computation & analysis (Shapely/pyproj) ───────

    def compute_distance(self, geometry_ref_a: str, geometry_ref_b=None) -> dict:
        try:
            geom_a = self.gs.get(geometry_ref_a)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref_a}"}
        lon_a, lat_a = geo.centroid(geom_a)
        refs_b = _normalize_refs(geometry_ref_b)
        if len(refs_b) == 1:
            try:
                geom_b = self.gs.get(refs_b[0])
            except KeyError:
                return {"error": f"Unknown geometry_ref: {refs_b[0]}"}
            lon_b, lat_b = geo.centroid(geom_b)
            return {"distance_km": round(geo.haversine(lon_a, lat_a, lon_b, lat_b), 1)}
        results = []
        for rb in refs_b:
            try:
                geom_b = self.gs.get(rb)
            except KeyError:
                results.append({"geometry_ref": rb, "error": f"Unknown geometry_ref: {rb}"})
                continue
            lon_b, lat_b = geo.centroid(geom_b)
            results.append({"geometry_ref": rb,
                            "distance_km": round(geo.haversine(lon_a, lat_a, lon_b, lat_b), 1)})
        return {"from": geometry_ref_a, "total": len(results), "results": results}

    def compute_area(self, geometry_ref=None) -> dict:
        refs = _normalize_refs(geometry_ref)
        if len(refs) == 1:
            try:
                geom = self.gs.get(refs[0])
            except KeyError:
                return {"error": f"Unknown geometry_ref: {refs[0]}"}
            if geom.get("type") not in ("Polygon", "MultiPolygon"):
                return {"error": "Geometry is not a Polygon"}
            return {"area_km2": geo.area_km2(geom)}
        results = []
        for r in refs:
            try:
                geom = self.gs.get(r)
            except KeyError:
                results.append({"geometry_ref": r, "error": f"Unknown"})
                continue
            if geom.get("type") not in ("Polygon", "MultiPolygon"):
                results.append({"geometry_ref": r, "error": "Not a Polygon"})
                continue
            results.append({"geometry_ref": r, "area_km2": geo.area_km2(geom)})
        return {"total": len(results), "results": results}

    def compute_length(self, geometry_ref=None) -> dict:
        refs = _normalize_refs(geometry_ref)
        if len(refs) == 1:
            try:
                geom = self.gs.get(refs[0])
            except KeyError:
                return {"error": f"Unknown geometry_ref: {refs[0]}"}
            if geom.get("type") not in ("LineString", "MultiLineString"):
                return {"error": "Geometry is not a LineString"}
            return {"length_km": geo.length_km(geom)}
        results = []
        for r in refs:
            try:
                geom = self.gs.get(r)
            except KeyError:
                results.append({"geometry_ref": r, "error": f"Unknown"})
                continue
            if geom.get("type") not in ("LineString", "MultiLineString"):
                results.append({"geometry_ref": r, "error": "Not a LineString"})
                continue
            results.append({"geometry_ref": r, "length_km": geo.length_km(geom)})
        return {"total": len(results), "results": results}

    def _find_nearest_single(self, key: str, ref_lon: float, ref_lat: float,
                             limit: int) -> list[dict]:
        """Find nearest features from a single point. Returns list of entries."""
        for radius_deg in (0.3, 0.8, 2.0):
            bbox_tuple = (ref_lon - radius_deg, ref_lat - radius_deg,
                          ref_lon + radius_deg, ref_lat + radius_deg)
            osm_feats = _overpass_features_in_bbox(key, bbox_tuple)
            if osm_feats:
                candidates = []
                for f in osm_feats:
                    f_lon, f_lat = geo.centroid(f["geometry"])
                    dist = geo.haversine(ref_lon, ref_lat, f_lon, f_lat)
                    candidates.append((dist, f))
                candidates.sort(key=lambda x: x[0])
                return [
                    _feature_to_entry(f, self.gs, extra={"distance_km": round(dist, 1)})
                    for dist, f in candidates[:limit]
                ]
        return []

    def find_nearest(self, tipo: str, geometry_ref=None, limit: int = 3) -> dict:
        key = tipo.lower().strip()
        if key not in _OSM_TAGS:
            return {"total": 0, "nearest": [],
                    "note": f"Feature type '{tipo}' not supported"}
        refs = _normalize_refs(geometry_ref)
        if len(refs) == 1:
            try:
                ref_geom = self.gs.get(refs[0])
            except KeyError:
                return {"error": f"Unknown geometry_ref: {refs[0]}"}
            ref_lon, ref_lat = geo.centroid(ref_geom)
            results = self._find_nearest_single(key, ref_lon, ref_lat, limit)
            return {"total": len(results), "nearest": results}
        # Batch: nearest per reference point
        batch_results = []
        for r in refs:
            try:
                ref_geom = self.gs.get(r)
            except KeyError:
                batch_results.append({"input_ref": r, "error": f"Unknown geometry_ref: {r}"})
                continue
            ref_lon, ref_lat = geo.centroid(ref_geom)
            nearest = self._find_nearest_single(key, ref_lon, ref_lat, limit)
            batch_results.append({"input_ref": r, "total": len(nearest), "nearest": nearest})
        return {"total": len(batch_results), "results": batch_results}

    def check_spatial_relation(self, geometry_ref_a: str, geometry_ref_b: str) -> dict:
        try:
            geom_a = self.gs.get(geometry_ref_a)
            geom_b = self.gs.get(geometry_ref_b)
        except KeyError as e:
            return {"error": f"Unknown geometry_ref: {e}"}
        return {
            "intersects": geo.intersects(geom_a, geom_b),
            "a_contains_b": geo.contains(geom_a, geom_b),
            "b_contains_a": geo.contains(geom_b, geom_a),
        }

    def list_municipalities_in(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        # Try Overpass first (has center coordinates for spatial filtering)
        bbox_tuple = geo.bbox(geom)
        munis = _overpass_municipalities_in_bbox(bbox_tuple)
        if munis:
            results = []
            for m in munis:
                if m.get("lat") and m.get("lon"):
                    pt = {"type": "Point", "coordinates": [m["lon"], m["lat"]]}
                    if geo.intersects(pt, geom):
                        results.append({"nome": m["nome"], "uf": m["uf"],
                                        "populacao": m["populacao"]})
            results.sort(key=lambda x: x["populacao"], reverse=True)
            return {"total": len(results), "municipalities": results}
        return {"total": 0, "municipalities": []}

    def get_neighbors(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        min_lon, min_lat, max_lon, max_lat = geo.bbox(geom)
        margin = 0.5
        expanded = (min_lon - margin, min_lat - margin,
                    max_lon + margin, max_lat + margin)
        munis = _overpass_municipalities_in_bbox(expanded)
        if not munis:
            return {"total": 0, "neighbors": []}
        my_shape = geo.to_shape(geom)
        results = []
        for m in munis:
            if m.get("lat") and m.get("lon"):
                pt = geo.to_shape(
                    {"type": "Point", "coordinates": [m["lon"], m["lat"]]})
                # Neighbor = in expanded area but center NOT inside original geometry
                if not my_shape.contains(pt):
                    results.append({"nome": m["nome"], "uf": m["uf"],
                                    "populacao": m["populacao"]})
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

    # ─── Advanced geometry operations ─────────────────────────

    def union(self, geometry_refs) -> dict:
        if isinstance(geometry_refs, str):
            return {"error": "union requires at least 2 geometry_refs"}
        if not isinstance(geometry_refs, list) or len(geometry_refs) < 2:
            return {"error": "union requires at least 2 geometry_refs"}
        geoms = []
        for ref in geometry_refs:
            try:
                geoms.append(self.gs.get(ref))
            except KeyError:
                return {"error": f"Unknown geometry_ref: {ref}"}
        result_geojson = geo.union_all(geoms)
        is_empty = geo.to_shape(result_geojson).is_empty
        new_ref = self.gs.put(result_geojson, label="union_result")
        gtype = result_geojson.get("type", "")
        result = {"geometry_ref": new_ref, "type": gtype, "is_empty": is_empty}
        if gtype in ("Polygon", "MultiPolygon"):
            result["area_km2"] = geo.area_km2(result_geojson)
        if gtype in ("LineString", "MultiLineString"):
            result["length_km"] = geo.length_km(result_geojson)
        return result

    def difference(self, geometry_ref_a: str, geometry_ref_b: str) -> dict:
        try:
            geom_a = self.gs.get(geometry_ref_a)
            geom_b = self.gs.get(geometry_ref_b)
        except KeyError as e:
            return {"error": f"Unknown geometry_ref: {e}"}
        result_geojson = geo.difference(geom_a, geom_b)
        is_empty = geo.to_shape(result_geojson).is_empty
        ref = self.gs.put(result_geojson, label="difference_result")
        result = {"geometry_ref": ref, "type": result_geojson.get("type", ""),
                  "is_empty": is_empty}
        if not is_empty:
            gtype = result_geojson.get("type", "")
            if gtype in ("Polygon", "MultiPolygon"):
                result["area_km2"] = geo.area_km2(result_geojson)
            if gtype in ("LineString", "MultiLineString"):
                result["length_km"] = geo.length_km(result_geojson)
        return result

    def clip(self, geometry_ref_a: str, geometry_ref_b: str) -> dict:
        try:
            geom_a = self.gs.get(geometry_ref_a)
            geom_b = self.gs.get(geometry_ref_b)
        except KeyError as e:
            return {"error": f"Unknown geometry_ref: {e}"}
        result_geojson = geo.intersection(geom_a, geom_b)
        result_shape = geo.to_shape(result_geojson)
        if result_shape.is_empty:
            ref = self.gs.put(result_geojson, label="clip_empty")
            return {"geometry_ref": ref, "is_empty": True}
        ref = self.gs.put(result_geojson, label="clip_result")
        gtype = result_geojson.get("type", "")
        result = {"geometry_ref": ref, "type": gtype, "is_empty": False}
        if gtype in ("LineString", "MultiLineString"):
            result["length_km"] = geo.length_km(result_geojson)
        elif gtype in ("Polygon", "MultiPolygon"):
            result["area_km2"] = geo.area_km2(result_geojson)
        return result

    def compute_centroid(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        lon, lat = geo.centroid(geom)
        point_geojson = {"type": "Point",
                         "coordinates": [round(lon, 6), round(lat, 6)]}
        ref = self.gs.put(point_geojson, label="centroid")
        return {"lat": round(lat, 6), "lon": round(lon, 6), "geometry_ref": ref}

    def compute_route_waypoints(self, geometry_refs) -> dict:
        if isinstance(geometry_refs, str):
            return {"error": "compute_route_waypoints requires at least 2 geometry_refs"}
        if not isinstance(geometry_refs, list) or len(geometry_refs) < 2:
            return {"error": "compute_route_waypoints requires at least 2 geometry_refs"}
        points = []
        for ref in geometry_refs:
            try:
                geom = self.gs.get(ref)
            except KeyError:
                return {"error": f"Unknown geometry_ref: {ref}"}
            lon, lat = geo.centroid(geom)
            points.append((lon, lat))
        route_geom, distance_km, duration_min = _osrm_route_waypoints(points)
        ref = self.gs.put(route_geom, label="route_waypoints")
        return {
            "distance_km": distance_km,
            "duration_min": duration_min,
            "length_km": geo.length_km(route_geom),
            "waypoints": len(geometry_refs),
            "geometry_ref": ref,
        }

    def get_weather(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        lon, lat = geo.centroid(geom)
        weather = _open_meteo_weather(lat, lon)
        if not weather:
            return {"error": "Could not retrieve weather data"}
        weather["lat"] = round(lat, 4)
        weather["lon"] = round(lon, 4)
        return weather

    # ─── Elevation & terrain (Open-Meteo) ─────────────────────

    def get_elevation(self, geometry_ref: str) -> dict:
        try:
            geom = self.gs.get(geometry_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {geometry_ref}"}
        gtype = geom.get("type", "")
        if gtype == "Point":
            lon, lat = geom["coordinates"][0], geom["coordinates"][1]
            elev = _open_meteo_elevation(lat, lon)
            if elev is None:
                return {"error": "Could not retrieve elevation"}
            return {"elevation_m": elev}
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
            elevations = _open_meteo_elevations(points)
            if not elevations:
                return {"error": "Could not retrieve elevations"}
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
        total_len = geo.length_km(geom)
        num_samples = min(20, max(2, len(coords) * 3))
        latlon_samples = []
        distances = []
        for i in range(num_samples):
            t = i / (num_samples - 1) if num_samples > 1 else 0
            target_km = t * total_len
            cum_km = 0.0
            for j in range(len(coords) - 1):
                seg_km = geo.haversine(coords[j][0], coords[j][1],
                                       coords[j + 1][0], coords[j + 1][1])
                if cum_km + seg_km >= target_km or j == len(coords) - 2:
                    frac = (target_km - cum_km) / seg_km if seg_km > 0 else 0
                    frac = max(0, min(1, frac))
                    lon = coords[j][0] + frac * (coords[j + 1][0] - coords[j][0])
                    lat = coords[j][1] + frac * (coords[j + 1][1] - coords[j][1])
                    latlon_samples.append((lat, lon))
                    distances.append(round(target_km, 1))
                    break
                cum_km += seg_km
        real_elevs = _open_meteo_elevations(latlon_samples)
        if not real_elevs:
            return {"error": "Could not retrieve elevation data"}
        sample_points = []
        for i, (lat, lon) in enumerate(latlon_samples):
            sample_points.append({
                "distance_km": distances[i],
                "elevation_m": real_elevs[i],
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
