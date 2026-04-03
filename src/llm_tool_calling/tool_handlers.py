"""Simulated tool implementations backed by synthetic data."""

from .geometry_store import GeometryStore
from .synthetic_data import (
    AUTOCOMPLETE,
    BORDERS,
    FEATURES,
    GEOCODE_RESULTS,
    HYDROGRAPHY,
    MILITARY_INSTALLATIONS,
    MUNICIPALITIES,
    NAMED_REGIONS,
    PRODUCT_TYPE_EXPLANATIONS,
    PRODUCTS,
    STATES,
)


def _fuzzy_find(query: str, data: dict) -> tuple[str, dict] | None:
    key = query.lower().strip()
    for k, v in data.items():
        if k in key or key in k:
            return k, v
    return None


class ToolHandlers:
    def __init__(self, geometry_store: GeometryStore):
        self.gs = geometry_store
        self._last_products: list[dict] = []

    def dispatch(self, name: str, args: dict) -> dict:
        handler = getattr(self, name, None)
        if handler is None:
            return {"error": f"Unknown tool: {name}"}
        return handler(**args)

    def geocode(self, place_name: str) -> dict:
        match = _fuzzy_find(place_name, GEOCODE_RESULTS)
        if not match:
            return {"error": f"Place '{place_name}' not found"}
        _, v = match
        ref = self.gs.put(
            {"type": "Point", "coordinates": [v["lon"], v["lat"]]},
            label=v["display_name"],
        )
        return {"lat": v["lat"], "lon": v["lon"], "display_name": v["display_name"], "geometry_ref": ref}

    def search_municipality(self, nome: str, uf: str = None) -> dict:
        key = (nome.lower().strip(), uf.lower().strip() if uf else None)
        if key[1] and key in MUNICIPALITIES:
            m = MUNICIPALITIES[key]
            ref = self.gs.put(m["geometry"], label=f"municipio_{m['nome']}")
            return {"nome": m["nome"], "uf": m["uf"], "codigo_ibge": m["codigo_ibge"], "populacao": m["populacao"], "geometry_ref": ref}
        matches = [v for k, v in MUNICIPALITIES.items() if k[0] == key[0]]
        if len(matches) == 1:
            m = matches[0]
            ref = self.gs.put(m["geometry"], label=f"municipio_{m['nome']}")
            return {"nome": m["nome"], "uf": m["uf"], "codigo_ibge": m["codigo_ibge"], "populacao": m["populacao"], "geometry_ref": ref}
        if len(matches) > 1:
            return {"ambiguous": True, "candidates": [{"nome": m["nome"], "uf": m["uf"]} for m in matches]}
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
            results.append({
                "id": p["id"],
                "tipo": p["tipo"],
                "escala": f"1:{p['escala']:,}".replace(",", ".") if p.get("escala") else None,
                "data_produto": p["data_produto"],
                "articulacao": p.get("articulacao"),
                "nome": p["nome"],
                "resolucao_m": p.get("resolucao_m"),
            })
        self._last_products = results
        return {"total": len(results), "products": results}

    def buffer(self, geometry_ref: str, raio_metros: float) -> dict:
        ref = self.gs.put(
            {"type": "Polygon", "coordinates": [[]]},
            label=f"buffer_{raio_metros}m",
        )
        return {"geometry_ref": ref, "type": "Polygon", "description": f"Buffer de {raio_metros}m aplicado"}

    def intersect(self, geometry_ref_a: str, geometry_ref_b: str) -> dict:
        ref = self.gs.put(
            {"type": "Polygon", "coordinates": [[]]},
            label="intersect_result",
        )
        return {"geometry_ref": ref, "area_km2": 1234.5}

    def compute_route(self, origin_ref: str, dest_ref: str) -> dict:
        try:
            origin = self.gs.get(origin_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {origin_ref}"}
        try:
            dest = self.gs.get(dest_ref)
        except KeyError:
            return {"error": f"Unknown geometry_ref: {dest_ref}"}
        # Extract coordinates from point geometries
        o_coords = origin.get("coordinates", [0, 0])
        d_coords = dest.get("coordinates", [0, 0])
        ref = self.gs.put(
            {"type": "LineString", "coordinates": [o_coords, d_coords]},
            label="route",
        )
        return {"distance_km": 250.0, "duration_min": 180, "geometry_ref": ref}

    def search_hydrography(self, nome: str, tipo: str = None, uf: str = None) -> dict:
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

    def search_features(self, tipo: str, geometry_ref: str) -> dict:
        key = tipo.lower().strip()
        if key in FEATURES:
            results = []
            for f in FEATURES[key]:
                ref = self.gs.put(f["geometry"], label=f["nome"])
                results.append({"nome": f["nome"], "geometry_ref": ref})
            return {"total": len(results), "features": results}
        return {"total": 0, "features": []}

    def search_military_installation(self, nome_ou_sigla: str, cidade: str = None) -> dict:
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
        return {"error": f"Military installation '{nome_ou_sigla}' not found"}

    def rank_by_scale(self, order: str = "best_first") -> dict:
        products = [p for p in self._last_products if p.get("escala")]
        reverse = order != "best_first"
        products.sort(key=lambda p: int(p["escala"].replace("1:", "").replace(".", "")), reverse=reverse)
        return {"products": products}

    def rank_by_date(self, order: str = "newest_first") -> dict:
        products = list(self._last_products)
        products.sort(key=lambda p: p.get("data_produto", ""), reverse=(order == "newest_first"))
        return {"products": products}

    def autocomplete_placename(self, fragmento: str) -> dict:
        match = _fuzzy_find(fragmento, AUTOCOMPLETE)
        if match:
            _, v = match
            return {"suggestions": v}
        return {"suggestions": []}

    def explain_product_type(self, tipo: str) -> dict:
        key = tipo.lower().strip()
        if key in PRODUCT_TYPE_EXPLANATIONS:
            return {"explanation": PRODUCT_TYPE_EXPLANATIONS[key]}
        return {"error": f"Unknown product type: {tipo}"}
