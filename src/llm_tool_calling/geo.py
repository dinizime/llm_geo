"""Real geometric operations using Shapely and pyproj."""

import math

from pyproj import Geod
from shapely.geometry import mapping, shape
from shapely.ops import transform

_GEOD = Geod(ellps="WGS84")


# ─── Conversions ──────────────────────────────────────────────

def to_shape(geojson: dict):
    """Convert GeoJSON dict to Shapely geometry."""
    return shape(geojson)


def to_geojson(geom) -> dict:
    """Convert Shapely geometry to GeoJSON dict."""
    return mapping(geom)


# ─── Basic properties ────────────────────────────────────────

def centroid(geojson: dict) -> tuple[float, float]:
    """Return (lon, lat) centroid of a GeoJSON geometry."""
    s = to_shape(geojson)
    c = s.centroid
    return c.x, c.y


def bbox(geojson: dict) -> tuple[float, float, float, float]:
    """Return (min_lon, min_lat, max_lon, max_lat) bounding box."""
    s = to_shape(geojson)
    return s.bounds  # (minx, miny, maxx, maxy)


# ─── Predicates ──────────────────────────────────────────────

def intersects(a: dict, b: dict) -> bool:
    """Check if two GeoJSON geometries intersect."""
    return to_shape(a).intersects(to_shape(b))


def contains(a: dict, b: dict) -> bool:
    """Check if GeoJSON geometry A contains geometry B."""
    return to_shape(a).contains(to_shape(b))


# ─── Operations ──────────────────────────────────────────────

def intersection(a: dict, b: dict) -> dict:
    """Compute the intersection of two GeoJSON geometries. Returns GeoJSON."""
    result = to_shape(a).intersection(to_shape(b))
    return to_geojson(result)


def buffer_meters(geojson: dict, radius_m: float, n_points: int = 64) -> dict:
    """Create a buffer around a GeoJSON geometry in meters.

    Uses latitude-adjusted degree conversion for the buffer, then returns GeoJSON.
    """
    s = to_shape(geojson)
    cx, cy = s.centroid.x, s.centroid.y
    # Convert meters to approximate degrees at this latitude
    deg_lat = radius_m / 110574.0
    deg_lon = radius_m / (111320.0 * max(0.01, abs(math.cos(math.radians(cy)))))
    # Scale geometry to approximate metric space, buffer, scale back
    def to_metric(x, y, z=None):
        return (x / deg_lon * radius_m, y / deg_lat * radius_m)

    def from_metric(x, y, z=None):
        return (x * deg_lon / radius_m, y * deg_lat / radius_m)

    metric = transform(to_metric, s)
    buffered = metric.buffer(radius_m, resolution=n_points // 4)
    result = transform(from_metric, buffered)
    return to_geojson(result)


# ─── Measurements (geodesic) ─────────────────────────────────

def area_km2(geojson: dict) -> float:
    """Compute geodesic area of a polygon in km2 using pyproj."""
    s = to_shape(geojson)
    if s.is_empty or s.geom_type not in ("Polygon", "MultiPolygon"):
        return 0.0
    area_m2, _ = _GEOD.geometry_area_perimeter(s)
    return round(abs(area_m2) / 1_000_000, 1)


def length_km(geojson: dict) -> float:
    """Compute geodesic length of a LineString in km using pyproj."""
    s = to_shape(geojson)
    if s.is_empty or s.geom_type not in ("LineString", "MultiLineString"):
        return 0.0
    length_m = _GEOD.geometry_length(s)
    return round(abs(length_m) / 1000, 1)


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Haversine distance in km between two (lon, lat) points."""
    R = 6371.0
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
