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

    def available(self, limit: int = 10) -> list[dict]:
        """Lista refs disponíveis (mais recentes primeiro) com label e tipo."""
        items = list(self._store.items())[-limit:][::-1]
        return [{"ref": r, "label": e["label"],
                 "type": e["geojson"].get("type", "?")} for r, e in items]

    def unknown_ref_error(self, ref) -> dict:
        """Erro estruturado para geometry_ref inexistente — inclui refs válidos
        para que o LLM possa recuperar no próximo turno."""
        return {
            "error": f"geometry_ref '{ref}' não existe no store",
            "dica": "Use um dos refs retornados por uma tool anterior (search_*, geocode, buffer, etc.). Se o ref expirou, recrie a geometria.",
            "available_refs": self.available(),
        }

    def summary(self, ref: str) -> dict:
        entry = self._store[ref]
        geojson = entry["geojson"]
        return {
            "geometry_ref": ref,
            "type": geojson.get("type", "unknown"),
            "label": entry["label"],
        }

    def __len__(self):
        return len(self._store)

    def clear(self):
        self._store.clear()
