from uuid import uuid4


class GeometryStore:
    """Stores geometries outside the LLM context. The LLM works with lightweight refs."""

    def __init__(self):
        self._store: dict[str, dict] = {}

    def put(self, geojson: dict, label: str = "") -> str:
        ref = f"geom_{uuid4().hex[:8]}"
        self._store[ref] = {"geojson": geojson, "label": label}
        return ref

    def get(self, ref: str) -> dict:
        if ref not in self._store:
            raise KeyError(f"Geometry '{ref}' not found")
        return self._store[ref]["geojson"]

    def summary(self, ref: str) -> dict:
        entry = self._store[ref]
        geojson = entry["geojson"]
        return {
            "geometry_ref": ref,
            "type": geojson.get("type", "unknown"),
            "label": entry["label"],
        }

    def clear(self):
        self._store.clear()
