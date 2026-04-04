"""Deterministic synthetic data for testing tool calling without a real database."""

# ═══════════════════════════════════════════════════════════════════
# MUNICIPALITIES — keyed by (nome_lower, uf_lower)
# ═══════════════════════════════════════════════════════════════════

MUNICIPALITIES = {
    # RS
    ("alecrim", "rs"): {
        "nome": "Alecrim", "uf": "RS", "codigo_ibge": "4300406", "populacao": 6685,
        "geometry": {"type": "Polygon", "coordinates": [[[-54.8, -27.7], [-54.7, -27.7], [-54.7, -27.6], [-54.8, -27.6], [-54.8, -27.7]]]},
    },
    ("porto alegre", "rs"): {
        "nome": "Porto Alegre", "uf": "RS", "codigo_ibge": "4314902", "populacao": 1488252,
        "geometry": {"type": "Polygon", "coordinates": [[[-51.3, -30.2], [-51.0, -30.2], [-51.0, -29.9], [-51.3, -29.9], [-51.3, -30.2]]]},
    },
    ("santa maria", "rs"): {
        "nome": "Santa Maria", "uf": "RS", "codigo_ibge": "4316907", "populacao": 283677,
        "geometry": {"type": "Polygon", "coordinates": [[[-53.9, -29.8], [-53.7, -29.8], [-53.7, -29.6], [-53.9, -29.6], [-53.9, -29.8]]]},
    },
    ("alegrete", "rs"): {
        "nome": "Alegrete", "uf": "RS", "codigo_ibge": "4300604", "populacao": 73589,
        "geometry": {"type": "Polygon", "coordinates": [[[-56.1, -29.9], [-55.5, -29.9], [-55.5, -29.6], [-56.1, -29.6], [-56.1, -29.9]]]},
    },
    ("uruguaiana", "rs"): {
        "nome": "Uruguaiana", "uf": "RS", "codigo_ibge": "4322400", "populacao": 126970,
        "geometry": {"type": "Polygon", "coordinates": [[[-57.2, -29.9], [-56.8, -29.9], [-56.8, -29.6], [-57.2, -29.6], [-57.2, -29.9]]]},
    },
    ("pelotas", "rs"): {
        "nome": "Pelotas", "uf": "RS", "codigo_ibge": "4314407", "populacao": 343132,
        "geometry": {"type": "Polygon", "coordinates": [[[-52.5, -31.9], [-52.2, -31.9], [-52.2, -31.6], [-52.5, -31.6], [-52.5, -31.9]]]},
    },
    ("caxias do sul", "rs"): {
        "nome": "Caxias do Sul", "uf": "RS", "codigo_ibge": "4305108", "populacao": 517451,
        "geometry": {"type": "Polygon", "coordinates": [[[-51.3, -29.3], [-51.0, -29.3], [-51.0, -29.0], [-51.3, -29.0], [-51.3, -29.3]]]},
    },
    ("bagé", "rs"): {
        "nome": "Bagé", "uf": "RS", "codigo_ibge": "4301602", "populacao": 121500,
        "geometry": {"type": "Polygon", "coordinates": [[[-54.2, -31.5], [-53.9, -31.5], [-53.9, -31.2], [-54.2, -31.2], [-54.2, -31.5]]]},
    },
    ("são gabriel", "rs"): {
        "nome": "São Gabriel", "uf": "RS", "codigo_ibge": "4318309", "populacao": 62692,
        "geometry": {"type": "Polygon", "coordinates": [[[-54.5, -30.5], [-54.2, -30.5], [-54.2, -30.2], [-54.5, -30.2], [-54.5, -30.5]]]},
    },
    ("jaguarão", "rs"): {
        "nome": "Jaguarão", "uf": "RS", "codigo_ibge": "4311007", "populacao": 28082,
        "geometry": {"type": "Polygon", "coordinates": [[[-53.5, -32.7], [-53.3, -32.7], [-53.3, -32.5], [-53.5, -32.5], [-53.5, -32.7]]]},
    },
    ("rosário do sul", "rs"): {
        "nome": "Rosário do Sul", "uf": "RS", "codigo_ibge": "4316105", "populacao": 39307,
        "geometry": {"type": "Polygon", "coordinates": [[[-55.0, -30.4], [-54.7, -30.4], [-54.7, -30.1], [-55.0, -30.1], [-55.0, -30.4]]]},
    },
    ("são borja", "rs"): {
        "nome": "São Borja", "uf": "RS", "codigo_ibge": "4318002", "populacao": 61671,
        "geometry": {"type": "Polygon", "coordinates": [[[-56.1, -28.8], [-55.8, -28.8], [-55.8, -28.5], [-56.1, -28.5], [-56.1, -28.8]]]},
    },
    ("osório", "rs"): {
        "nome": "Osório", "uf": "RS", "codigo_ibge": "4313409", "populacao": 45158,
        "geometry": {"type": "Polygon", "coordinates": [[[-50.4, -30.0], [-50.1, -30.0], [-50.1, -29.7], [-50.4, -29.7], [-50.4, -30.0]]]},
    },
    ("viamão", "rs"): {
        "nome": "Viamão", "uf": "RS", "codigo_ibge": "4323002", "populacao": 255224,
        "geometry": {"type": "Polygon", "coordinates": [[[-51.1, -30.2], [-50.8, -30.2], [-50.8, -29.9], [-51.1, -29.9], [-51.1, -30.2]]]},
    },
    ("cachoeira do sul", "rs"): {
        "nome": "Cachoeira do Sul", "uf": "RS", "codigo_ibge": "4303103", "populacao": 82547,
        "geometry": {"type": "Polygon", "coordinates": [[[-53.1, -30.2], [-52.7, -30.2], [-52.7, -29.9], [-53.1, -29.9], [-53.1, -30.2]]]},
    },
    ("rio grande", "rs"): {
        "nome": "Rio Grande", "uf": "RS", "codigo_ibge": "4315602", "populacao": 211965,
        "geometry": {"type": "Polygon", "coordinates": [[[-52.3, -32.2], [-52.0, -32.2], [-52.0, -31.9], [-52.3, -31.9], [-52.3, -32.2]]]},
    },
    ("santana do livramento", "rs"): {
        "nome": "Santana do Livramento", "uf": "RS", "codigo_ibge": "4317103", "populacao": 76743,
        "geometry": {"type": "Polygon", "coordinates": [[[-55.7, -31.0], [-55.4, -31.0], [-55.4, -30.7], [-55.7, -30.7], [-55.7, -31.0]]]},
    },
    ("dom pedrito", "rs"): {
        "nome": "Dom Pedrito", "uf": "RS", "codigo_ibge": "4306601", "populacao": 38916,
        "geometry": {"type": "Polygon", "coordinates": [[[-55.0, -31.1], [-54.6, -31.1], [-54.6, -30.8], [-55.0, -30.8], [-55.0, -31.1]]]},
    },
    ("quaraí", "rs"): {
        "nome": "Quaraí", "uf": "RS", "codigo_ibge": "4315206", "populacao": 22948,
        "geometry": {"type": "Polygon", "coordinates": [[[-56.6, -30.5], [-56.3, -30.5], [-56.3, -30.2], [-56.6, -30.2], [-56.6, -30.5]]]},
    },
    ("santo ângelo", "rs"): {
        "nome": "Santo Ângelo", "uf": "RS", "codigo_ibge": "4317400", "populacao": 78194,
        "geometry": {"type": "Polygon", "coordinates": [[[-54.4, -28.4], [-54.1, -28.4], [-54.1, -28.2], [-54.4, -28.2], [-54.4, -28.4]]]},
    },
    ("itaqui", "rs"): {
        "nome": "Itaqui", "uf": "RS", "codigo_ibge": "4310801", "populacao": 37666,
        "geometry": {"type": "Polygon", "coordinates": [[[-56.7, -29.2], [-56.4, -29.2], [-56.4, -29.0], [-56.7, -29.0], [-56.7, -29.2]]]},
    },
    # DF
    ("brasília", "df"): {
        "nome": "Brasília", "uf": "DF", "codigo_ibge": "5300108", "populacao": 3094325,
        "geometry": {"type": "Polygon", "coordinates": [[[-48.0, -15.9], [-47.7, -15.9], [-47.7, -15.6], [-48.0, -15.6], [-48.0, -15.9]]]},
    },
    # AM
    ("manaus", "am"): {
        "nome": "Manaus", "uf": "AM", "codigo_ibge": "1302603", "populacao": 2255903,
        "geometry": {"type": "Polygon", "coordinates": [[[-60.1, -3.2], [-59.8, -3.2], [-59.8, -2.9], [-60.1, -2.9], [-60.1, -3.2]]]},
    },
    # SP
    ("são paulo", "sp"): {
        "nome": "São Paulo", "uf": "SP", "codigo_ibge": "3550308", "populacao": 12396372,
        "geometry": {"type": "Polygon", "coordinates": [[[-46.8, -23.7], [-46.4, -23.7], [-46.4, -23.4], [-46.8, -23.4], [-46.8, -23.7]]]},
    },
    # SC
    ("florianópolis", "sc"): {
        "nome": "Florianópolis", "uf": "SC", "codigo_ibge": "4205407", "populacao": 516524,
        "geometry": {"type": "Polygon", "coordinates": [[[-48.6, -27.7], [-48.4, -27.7], [-48.4, -27.5], [-48.6, -27.5], [-48.6, -27.7]]]},
    },
    ("joinville", "sc"): {
        "nome": "Joinville", "uf": "SC", "codigo_ibge": "4209102", "populacao": 604708,
        "geometry": {"type": "Polygon", "coordinates": [[[-49.0, -26.4], [-48.7, -26.4], [-48.7, -26.2], [-49.0, -26.2], [-49.0, -26.4]]]},
    },
    # PR
    ("curitiba", "pr"): {
        "nome": "Curitiba", "uf": "PR", "codigo_ibge": "4106902", "populacao": 1963726,
        "geometry": {"type": "Polygon", "coordinates": [[[-49.4, -25.5], [-49.2, -25.5], [-49.2, -25.3], [-49.4, -25.3], [-49.4, -25.5]]]},
    },
    ("londrina", "pr"): {
        "nome": "Londrina", "uf": "PR", "codigo_ibge": "4113700", "populacao": 580870,
        "geometry": {"type": "Polygon", "coordinates": [[[-51.3, -23.4], [-51.0, -23.4], [-51.0, -23.2], [-51.3, -23.2], [-51.3, -23.4]]]},
    },
}


# ═══════════════════════════════════════════════════════════════════
# GEOCODE RESULTS — keyed by lowercase query
# ═══════════════════════════════════════════════════════════════════

GEOCODE_RESULTS = {
    "usina hidrelétrica de itaipu": {"lat": -25.41, "lon": -54.59, "display_name": "Usina Hidrelétrica de Itaipu"},
    "itaipu": {"lat": -25.41, "lon": -54.59, "display_name": "Usina Hidrelétrica de Itaipu"},
    "alecrim, rs": {"lat": -27.66, "lon": -54.73, "display_name": "Alecrim, RS"},
    "alecrim": {"lat": -27.66, "lon": -54.73, "display_name": "Alecrim, RS"},
    "santa maria, rs": {"lat": -29.68, "lon": -53.81, "display_name": "Santa Maria, RS"},
    "santa maria": {"lat": -29.68, "lon": -53.81, "display_name": "Santa Maria, RS"},
    "alegrete, rs": {"lat": -29.78, "lon": -55.79, "display_name": "Alegrete, RS"},
    "alegrete": {"lat": -29.78, "lon": -55.79, "display_name": "Alegrete, RS"},
    "florianópolis, sc": {"lat": -27.59, "lon": -48.55, "display_name": "Florianópolis, SC"},
    "florianópolis": {"lat": -27.59, "lon": -48.55, "display_name": "Florianópolis, SC"},
    "porto alegre, rs": {"lat": -30.03, "lon": -51.23, "display_name": "Porto Alegre, RS"},
    "porto alegre": {"lat": -30.03, "lon": -51.23, "display_name": "Porto Alegre, RS"},
    "uruguaiana, rs": {"lat": -29.76, "lon": -57.09, "display_name": "Uruguaiana, RS"},
    "uruguaiana": {"lat": -29.76, "lon": -57.09, "display_name": "Uruguaiana, RS"},
    "pelotas, rs": {"lat": -31.77, "lon": -52.34, "display_name": "Pelotas, RS"},
    "pelotas": {"lat": -31.77, "lon": -52.34, "display_name": "Pelotas, RS"},
    "caxias do sul, rs": {"lat": -29.17, "lon": -51.18, "display_name": "Caxias do Sul, RS"},
    "caxias do sul": {"lat": -29.17, "lon": -51.18, "display_name": "Caxias do Sul, RS"},
    "bagé, rs": {"lat": -31.33, "lon": -54.10, "display_name": "Bagé, RS"},
    "bagé": {"lat": -31.33, "lon": -54.10, "display_name": "Bagé, RS"},
    "são gabriel, rs": {"lat": -30.34, "lon": -54.32, "display_name": "São Gabriel, RS"},
    "são gabriel": {"lat": -30.34, "lon": -54.32, "display_name": "São Gabriel, RS"},
    "jaguarão, rs": {"lat": -32.57, "lon": -53.38, "display_name": "Jaguarão, RS"},
    "jaguarão": {"lat": -32.57, "lon": -53.38, "display_name": "Jaguarão, RS"},
    "rosário do sul, rs": {"lat": -30.25, "lon": -54.91, "display_name": "Rosário do Sul, RS"},
    "rosário do sul": {"lat": -30.25, "lon": -54.91, "display_name": "Rosário do Sul, RS"},
    "são borja, rs": {"lat": -28.66, "lon": -56.00, "display_name": "São Borja, RS"},
    "são borja": {"lat": -28.66, "lon": -56.00, "display_name": "São Borja, RS"},
    "osório, rs": {"lat": -29.89, "lon": -50.27, "display_name": "Osório, RS"},
    "osório": {"lat": -29.89, "lon": -50.27, "display_name": "Osório, RS"},
    "viamão, rs": {"lat": -30.08, "lon": -51.02, "display_name": "Viamão, RS"},
    "viamão": {"lat": -30.08, "lon": -51.02, "display_name": "Viamão, RS"},
    "cachoeira do sul, rs": {"lat": -30.04, "lon": -52.89, "display_name": "Cachoeira do Sul, RS"},
    "cachoeira do sul": {"lat": -30.04, "lon": -52.89, "display_name": "Cachoeira do Sul, RS"},
    "rio grande, rs": {"lat": -32.03, "lon": -52.10, "display_name": "Rio Grande, RS"},
    "rio grande": {"lat": -32.03, "lon": -52.10, "display_name": "Rio Grande, RS"},
    "santana do livramento, rs": {"lat": -30.89, "lon": -55.53, "display_name": "Santana do Livramento, RS"},
    "santana do livramento": {"lat": -30.89, "lon": -55.53, "display_name": "Santana do Livramento, RS"},
    "livramento": {"lat": -30.89, "lon": -55.53, "display_name": "Santana do Livramento, RS"},
    "são paulo, sp": {"lat": -23.55, "lon": -46.63, "display_name": "São Paulo, SP"},
    "manaus, am": {"lat": -3.12, "lon": -60.02, "display_name": "Manaus, AM"},
    "brasília, df": {"lat": -15.79, "lon": -47.88, "display_name": "Brasília, DF"},
    "curitiba, pr": {"lat": -25.43, "lon": -49.27, "display_name": "Curitiba, PR"},
    "joinville, sc": {"lat": -26.30, "lon": -48.85, "display_name": "Joinville, SC"},
    "dom pedrito, rs": {"lat": -30.98, "lon": -54.67, "display_name": "Dom Pedrito, RS"},
    "dom pedrito": {"lat": -30.98, "lon": -54.67, "display_name": "Dom Pedrito, RS"},
    "quaraí, rs": {"lat": -30.39, "lon": -56.45, "display_name": "Quaraí, RS"},
    "quaraí": {"lat": -30.39, "lon": -56.45, "display_name": "Quaraí, RS"},
    "santo ângelo, rs": {"lat": -28.30, "lon": -54.26, "display_name": "Santo Ângelo, RS"},
    "santo ângelo": {"lat": -28.30, "lon": -54.26, "display_name": "Santo Ângelo, RS"},
    "itaqui, rs": {"lat": -29.12, "lon": -56.55, "display_name": "Itaqui, RS"},
    "itaqui": {"lat": -29.12, "lon": -56.55, "display_name": "Itaqui, RS"},
    # Airports by name
    "aeroporto salgado filho": {"lat": -29.99, "lon": -51.17, "display_name": "Aeroporto Salgado Filho, Porto Alegre"},
    "salgado filho": {"lat": -29.99, "lon": -51.17, "display_name": "Aeroporto Salgado Filho, Porto Alegre"},
    "aeroporto de santa maria": {"lat": -29.71, "lon": -53.69, "display_name": "Aeroporto de Santa Maria, RS"},
    "aeroporto de bagé": {"lat": -31.39, "lon": -54.11, "display_name": "Aeroporto de Bagé, RS"},
}


# ═══════════════════════════════════════════════════════════════════
# STATES — keyed by lowercase UF
# ═══════════════════════════════════════════════════════════════════

STATES = {
    "rs": {
        "uf": "RS", "nome": "Rio Grande do Sul",
        "geometry": {"type": "Polygon", "coordinates": [[[-57.6, -33.8], [-49.7, -33.8], [-49.7, -27.1], [-57.6, -27.1], [-57.6, -33.8]]]},
    },
    "sp": {
        "uf": "SP", "nome": "São Paulo",
        "geometry": {"type": "Polygon", "coordinates": [[[-53.1, -25.3], [-44.2, -25.3], [-44.2, -19.8], [-53.1, -19.8], [-53.1, -25.3]]]},
    },
    "sc": {
        "uf": "SC", "nome": "Santa Catarina",
        "geometry": {"type": "Polygon", "coordinates": [[[-53.8, -29.4], [-48.6, -29.4], [-48.6, -26.0], [-53.8, -26.0], [-53.8, -29.4]]]},
    },
    "pr": {
        "uf": "PR", "nome": "Paraná",
        "geometry": {"type": "Polygon", "coordinates": [[[-54.6, -26.7], [-48.0, -26.7], [-48.0, -22.5], [-54.6, -22.5], [-54.6, -26.7]]]},
    },
    "am": {
        "uf": "AM", "nome": "Amazonas",
        "geometry": {"type": "Polygon", "coordinates": [[[-73.8, -9.8], [-56.1, -9.8], [-56.1, 2.2], [-73.8, 2.2], [-73.8, -9.8]]]},
    },
    "df": {
        "uf": "DF", "nome": "Distrito Federal",
        "geometry": {"type": "Polygon", "coordinates": [[[-48.3, -16.1], [-47.3, -16.1], [-47.3, -15.5], [-48.3, -15.5], [-48.3, -16.1]]]},
    },
}


# ═══════════════════════════════════════════════════════════════════
# NAMED REGIONS
# ═══════════════════════════════════════════════════════════════════

NAMED_REGIONS = {
    "serra gaúcha": {
        "nome": "Serra Gaúcha",
        "geometry": {"type": "Polygon", "coordinates": [[[-51.5, -29.3], [-50.8, -29.3], [-50.8, -28.8], [-51.5, -28.8], [-51.5, -29.3]]]},
    },
    "pantanal": {
        "nome": "Pantanal",
        "geometry": {"type": "Polygon", "coordinates": [[[-58.0, -22.0], [-55.0, -22.0], [-55.0, -17.0], [-58.0, -17.0], [-58.0, -22.0]]]},
    },
    "vale do taquari": {
        "nome": "Vale do Taquari",
        "geometry": {"type": "Polygon", "coordinates": [[[-52.2, -29.6], [-51.6, -29.6], [-51.6, -29.0], [-52.2, -29.0], [-52.2, -29.6]]]},
    },
    "litoral norte rs": {
        "nome": "Litoral Norte RS",
        "geometry": {"type": "Polygon", "coordinates": [[[-50.4, -30.0], [-49.7, -30.0], [-49.7, -29.3], [-50.4, -29.3], [-50.4, -30.0]]]},
    },
}


# ═══════════════════════════════════════════════════════════════════
# BORDERS — keyed by lowercase country name
# ═══════════════════════════════════════════════════════════════════

BORDERS = {
    "uruguai": {
        "pais": "Uruguai",
        "geometry": {"type": "LineString", "coordinates": [[-57.6, -33.8], [-53.4, -33.0], [-53.4, -32.0]]},
    },
    "argentina": {
        "pais": "Argentina",
        "geometry": {"type": "LineString", "coordinates": [[-57.6, -33.8], [-57.6, -27.1], [-54.6, -25.6]]},
    },
}


# ═══════════════════════════════════════════════════════════════════
# ROADS — keyed by lowercase identifier
# ═══════════════════════════════════════════════════════════════════

ROADS = {
    "br-101": {
        "nome": "BR-101",
        "descricao": "Rodovia federal litorânea, de Touros (RN) a São José do Norte (RS)",
        "extensao_km": 4772,
        "geometry": {"type": "LineString", "coordinates": [
            [-48.5, -26.3], [-48.6, -27.1], [-48.7, -27.6], [-49.4, -28.7],
            [-49.7, -29.3], [-50.1, -29.9], [-50.3, -30.2], [-51.0, -30.5],
        ]},
        "trechos_uf": {
            "sc": {"geometry": {"type": "LineString", "coordinates": [[-48.5, -26.3], [-48.6, -27.1], [-48.7, -27.6], [-49.4, -28.7]]}, "extensao_km": 465},
            "rs": {"geometry": {"type": "LineString", "coordinates": [[-49.4, -28.7], [-49.7, -29.3], [-50.1, -29.9], [-50.3, -30.2], [-51.0, -30.5]]}, "extensao_km": 355},
        },
    },
    "br-116": {
        "nome": "BR-116",
        "descricao": "Rodovia federal de Fortaleza (CE) a Jaguarão (RS)",
        "extensao_km": 4513,
        "geometry": {"type": "LineString", "coordinates": [
            [-51.2, -29.2], [-51.1, -29.9], [-51.2, -30.0], [-52.1, -31.3],
            [-52.3, -31.8], [-53.4, -32.6],
        ]},
        "trechos_uf": {
            "rs": {"geometry": {"type": "LineString", "coordinates": [[-51.2, -29.2], [-51.1, -29.9], [-51.2, -30.0], [-52.1, -31.3], [-52.3, -31.8], [-53.4, -32.6]]}, "extensao_km": 530},
        },
    },
    "br-290": {
        "nome": "BR-290",
        "descricao": "Rodovia federal de Porto Alegre a Uruguaiana (Freeway + BR-290)",
        "extensao_km": 590,
        "geometry": {"type": "LineString", "coordinates": [
            [-51.2, -30.0], [-52.0, -30.0], [-53.0, -30.1], [-53.8, -29.7],
            [-54.9, -30.3], [-55.8, -29.8], [-57.1, -29.8],
        ]},
        "trechos_uf": {
            "rs": {"geometry": {"type": "LineString", "coordinates": [[-51.2, -30.0], [-52.0, -30.0], [-53.0, -30.1], [-53.8, -29.7], [-54.9, -30.3], [-55.8, -29.8], [-57.1, -29.8]]}, "extensao_km": 590},
        },
    },
    "br-153": {
        "nome": "BR-153",
        "descricao": "Rodovia Transbrasiliana, de Marabá (PA) a Aceguá (RS)",
        "extensao_km": 3566,
        "geometry": {"type": "LineString", "coordinates": [
            [-49.3, -22.3], [-49.8, -23.2], [-50.4, -24.0], [-50.1, -25.1],
            [-51.5, -27.5], [-52.5, -29.2],
        ]},
        "trechos_uf": {},
    },
    "rs-040": {
        "nome": "RS-040",
        "descricao": "Rodovia estadual de Porto Alegre a Capivari do Sul",
        "extensao_km": 98,
        "geometry": {"type": "LineString", "coordinates": [
            [-51.1, -30.1], [-50.9, -30.1], [-50.6, -30.0], [-50.3, -30.0],
        ]},
        "trechos_uf": {
            "rs": {"geometry": {"type": "LineString", "coordinates": [[-51.1, -30.1], [-50.9, -30.1], [-50.6, -30.0], [-50.3, -30.0]]}, "extensao_km": 98},
        },
    },
}


# ═══════════════════════════════════════════════════════════════════
# HYDROGRAPHY — keyed by lowercase name
# ═══════════════════════════════════════════════════════════════════

HYDROGRAPHY = {
    "rio jacuí": {
        "nome": "Rio Jacuí", "tipo": "rio",
        "geometry": {"type": "LineString", "coordinates": [[-53.5, -29.5], [-52.5, -29.8], [-51.5, -30.0]]},
    },
    "rio guaíba": {
        "nome": "Rio Guaíba", "tipo": "rio",
        "geometry": {"type": "LineString", "coordinates": [[-51.25, -30.0], [-51.2, -30.1], [-51.15, -30.25]]},
    },
    "rio ibicuí": {
        "nome": "Rio Ibicuí", "tipo": "rio",
        "geometry": {"type": "LineString", "coordinates": [[-54.0, -29.4], [-54.8, -29.6], [-55.5, -29.5], [-56.3, -29.1]]},
    },
    "rio uruguai": {
        "nome": "Rio Uruguai", "tipo": "rio",
        "geometry": {"type": "LineString", "coordinates": [[-49.7, -27.2], [-51.5, -27.3], [-54.6, -27.5], [-57.6, -30.2]]},
    },
    "rio camaquã": {
        "nome": "Rio Camaquã", "tipo": "rio",
        "geometry": {"type": "LineString", "coordinates": [[-53.5, -30.8], [-52.5, -31.2], [-52.0, -31.3]]},
    },
    "rio santa maria": {
        "nome": "Rio Santa Maria", "tipo": "rio",
        "geometry": {"type": "LineString", "coordinates": [[-54.5, -29.5], [-54.3, -29.8], [-54.0, -30.0]]},
    },
    "rio quaraí": {
        "nome": "Rio Quaraí", "tipo": "rio",
        "geometry": {"type": "LineString", "coordinates": [[-55.5, -30.2], [-56.0, -30.3], [-57.1, -30.4]]},
    },
    "rio ibirapuitã": {
        "nome": "Rio Ibirapuitã", "tipo": "rio",
        "geometry": {"type": "LineString", "coordinates": [[-55.5, -29.2], [-55.7, -29.5], [-55.9, -29.8]]},
    },
}


# ═══════════════════════════════════════════════════════════════════
# PRODUCTS — geospatial products catalog (unchanged)
# ═══════════════════════════════════════════════════════════════════

PRODUCTS = [
    {"id": 1, "tipo": "carta_topografica", "escala": 25000, "data_produto": "2022-06-15", "articulacao": "SH-21-X-D-III-4", "nome": "Alecrim", "resolucao_m": None, "fonte": "fotogrametrico", "bbox": [-54.85, -27.75, -54.65, -27.55]},
    {"id": 2, "tipo": "carta_topografica", "escala": 50000, "data_produto": "2020-03-10", "articulacao": "SH-21-X-D-III", "nome": "Alecrim", "resolucao_m": None, "fonte": "fotogrametrico", "bbox": [-55.0, -28.0, -54.5, -27.5]},
    {"id": 3, "tipo": "carta_topografica", "escala": 100000, "data_produto": "2018-01-20", "articulacao": "SH-21-X-D", "nome": "Santo Ângelo", "resolucao_m": None, "fonte": "fotogrametrico", "bbox": [-55.5, -28.5, -54.0, -27.0]},
    {"id": 4, "tipo": "ortoimagem", "escala": None, "data_produto": "2023-11-01", "articulacao": None, "nome": "Orto POA 2023", "resolucao_m": 0.5, "fonte": "fotogrametrico", "bbox": [-51.35, -30.25, -50.95, -29.85]},
    {"id": 5, "tipo": "imagem_drone", "escala": None, "data_produto": "2023-05-20", "articulacao": None, "nome": "Drone Itaipu 2023", "resolucao_m": 0.05, "fonte": "drone", "bbox": [-54.65, -25.47, -54.53, -25.35]},
    {"id": 6, "tipo": "mds", "escala": None, "data_produto": "2021-08-10", "articulacao": None, "nome": "MDS Serra Gaúcha", "resolucao_m": 1.0, "fonte": "lidar", "bbox": [-51.6, -29.4, -50.7, -28.7]},
    {"id": 7, "tipo": "carta_topografica", "escala": 250000, "data_produto": "2015-06-01", "articulacao": "SH-22", "nome": "Porto Alegre", "resolucao_m": None, "fonte": "fotogrametrico", "bbox": [-54.0, -32.0, -48.0, -28.0]},
    {"id": 8, "tipo": "mdt", "escala": None, "data_produto": "2022-03-15", "articulacao": None, "nome": "MDT Pantanal Norte", "resolucao_m": 5.0, "fonte": "radar", "bbox": [-57.5, -20.0, -55.5, -17.5]},
    {"id": 9, "tipo": "carta_topografica", "escala": 25000, "data_produto": "2024-01-10", "articulacao": "SH-22-V-C-IV-1", "nome": "Santa Maria NE", "resolucao_m": None, "fonte": "fotogrametrico", "bbox": [-53.85, -29.75, -53.7, -29.6]},
    {"id": 10, "tipo": "ortoimagem", "escala": None, "data_produto": "2020-09-15", "articulacao": None, "nome": "Orto POA 2020", "resolucao_m": 1.0, "fonte": "satelite", "bbox": [-51.35, -30.25, -50.95, -29.85]},
    {"id": 11, "tipo": "imagem_satelite", "escala": None, "data_produto": "2024-02-01", "articulacao": None, "nome": "Sentinel-2 Fronteira Sul", "resolucao_m": 10.0, "fonte": "satelite", "bbox": [-57.0, -33.5, -53.0, -32.0]},
]


# ═══════════════════════════════════════════════════════════════════
# FEATURES — keyed by feature type, each with attributes
# ═══════════════════════════════════════════════════════════════════

FEATURES = {
    # ─── Transportation ───────────────────────────────────────
    "ponte": [
        # RS interior — corredores de rota
        {"nome": "Ponte sobre o Rio Vacacaí", "geometry": {"type": "Point", "coordinates": [-53.5, -29.7]}, "comprimento_m": 120, "largura_m": 12, "capacidade_ton": 45},
        {"nome": "Ponte sobre o Rio Ibicuí (BR-290)", "geometry": {"type": "Point", "coordinates": [-55.2, -29.5]}, "comprimento_m": 280, "largura_m": 10, "capacidade_ton": 40},
        {"nome": "Ponte sobre o Rio Jacuí (Cachoeira)", "geometry": {"type": "Point", "coordinates": [-52.9, -30.0]}, "comprimento_m": 210, "largura_m": 11, "capacidade_ton": 45},
        # BR-290 corredor SM→Uruguaiana
        {"nome": "Ponte sobre o Arroio Puitã (BR-290)", "geometry": {"type": "Point", "coordinates": [-54.5, -30.1]}, "comprimento_m": 85, "largura_m": 10, "capacidade_ton": 40},
        {"nome": "Ponte sobre o Rio Santa Maria (BR-290)", "geometry": {"type": "Point", "coordinates": [-54.0, -29.9]}, "comprimento_m": 160, "largura_m": 12, "capacidade_ton": 45},
        {"nome": "Ponte sobre o Rio Ibirapuitã (Alegrete)", "geometry": {"type": "Point", "coordinates": [-55.8, -29.7]}, "comprimento_m": 140, "largura_m": 10, "capacidade_ton": 35},
        # Corredor Alegrete→Rosário do Sul
        {"nome": "Ponte sobre o Arroio Caverá", "geometry": {"type": "Point", "coordinates": [-55.3, -30.0]}, "comprimento_m": 75, "largura_m": 8, "capacidade_ton": 30},
        {"nome": "Ponte sobre o Rio Ibicuí (Rosário)", "geometry": {"type": "Point", "coordinates": [-54.9, -30.2]}, "comprimento_m": 220, "largura_m": 10, "capacidade_ton": 40},
        # Corredor POA→Pelotas (BR-116)
        {"nome": "Ponte sobre o Rio Camaquã (BR-116)", "geometry": {"type": "Point", "coordinates": [-52.0, -31.3]}, "comprimento_m": 170, "largura_m": 12, "capacidade_ton": 50},
        {"nome": "Ponte sobre o Arroio Pelotas (BR-116)", "geometry": {"type": "Point", "coordinates": [-52.3, -31.7]}, "comprimento_m": 95, "largura_m": 10, "capacidade_ton": 40},
        # Corredor Uruguaiana→Bagé
        {"nome": "Ponte sobre o Rio Quaraí", "geometry": {"type": "Point", "coordinates": [-56.4, -30.4]}, "comprimento_m": 190, "largura_m": 10, "capacidade_ton": 38},
        {"nome": "Ponte sobre o Rio Negro", "geometry": {"type": "Point", "coordinates": [-54.8, -31.0]}, "comprimento_m": 130, "largura_m": 9, "capacidade_ton": 35},
        # Corredor POA→Livramento
        {"nome": "Ponte sobre o Rio Jacuí (São Gabriel)", "geometry": {"type": "Point", "coordinates": [-54.3, -30.3]}, "comprimento_m": 180, "largura_m": 11, "capacidade_ton": 45},
        {"nome": "Ponte sobre o Rio Santa Maria (Rosário)", "geometry": {"type": "Point", "coordinates": [-54.9, -30.5]}, "comprimento_m": 150, "largura_m": 10, "capacidade_ton": 40},
        # Corredor POA→Caxias
        {"nome": "Ponte Giuseppe Garibaldi (Caxias)", "geometry": {"type": "Point", "coordinates": [-51.2, -29.2]}, "comprimento_m": 190, "largura_m": 14, "capacidade_ton": 50},
        # Fronteira Argentina
        {"nome": "Ponte Internacional São Borja - Santo Tomé", "geometry": {"type": "Point", "coordinates": [-56.0, -28.7]}, "comprimento_m": 1400, "largura_m": 12, "capacidade_ton": 60},
        {"nome": "Ponte Internacional Uruguaiana - Paso de los Libres", "geometry": {"type": "Point", "coordinates": [-57.1, -29.8]}, "comprimento_m": 1420, "largura_m": 14, "capacidade_ton": 60},
        # Fronteira Uruguai
        {"nome": "Ponte Internacional Barão de Mauá (Jaguarão)", "geometry": {"type": "Point", "coordinates": [-53.38, -32.57]}, "comprimento_m": 300, "largura_m": 12, "capacidade_ton": 60},
        # SC
        {"nome": "Ponte Hercílio Luz (Florianópolis)", "geometry": {"type": "Point", "coordinates": [-48.55, -27.60]}, "comprimento_m": 820, "largura_m": 10, "capacidade_ton": 30},
        {"nome": "Ponte Colombo Salles (Florianópolis)", "geometry": {"type": "Point", "coordinates": [-48.54, -27.59]}, "comprimento_m": 1252, "largura_m": 14, "capacidade_ton": 60},
        {"nome": "Ponte sobre o Rio Itajaí (Blumenau)", "geometry": {"type": "Point", "coordinates": [-49.07, -26.92]}, "comprimento_m": 340, "largura_m": 12, "capacidade_ton": 50},
        # PR
        {"nome": "Ponte sobre o Rio Iguaçu (Curitiba)", "geometry": {"type": "Point", "coordinates": [-49.27, -25.51]}, "comprimento_m": 450, "largura_m": 14, "capacidade_ton": 60},
        # SM area
        {"nome": "Ponte sobre o Arroio Cadena (Santa Maria)", "geometry": {"type": "Point", "coordinates": [-53.82, -29.70]}, "comprimento_m": 45, "largura_m": 10, "capacidade_ton": 30},
        {"nome": "Ponte sobre o Rio Vacacaí-Mirim (Santa Maria)", "geometry": {"type": "Point", "coordinates": [-53.75, -29.65]}, "comprimento_m": 90, "largura_m": 10, "capacidade_ton": 35},
    ],
    "tunel": [
        {"nome": "Túnel Morro do Agudo (BR-101 SC)", "geometry": {"type": "Point", "coordinates": [-49.3, -28.8]}, "comprimento_m": 450, "largura_m": 10},
        {"nome": "Túnel do Morro (Serra do Rio do Rastro SC)", "geometry": {"type": "Point", "coordinates": [-49.5, -28.5]}, "comprimento_m": 320, "largura_m": 8},
        {"nome": "Túnel BR-101 Palhoça", "geometry": {"type": "Point", "coordinates": [-48.68, -27.70]}, "comprimento_m": 600, "largura_m": 12},
    ],
    "estacao_ferroviaria": [
        {"nome": "Estação Ferroviária de Porto Alegre", "geometry": {"type": "Point", "coordinates": [-51.23, -30.03]}, "status": "ativa"},
        {"nome": "Estação Ferroviária de Cachoeira do Sul", "geometry": {"type": "Point", "coordinates": [-52.89, -30.04]}, "status": "desativada"},
        {"nome": "Estação Ferroviária de Santa Maria", "geometry": {"type": "Point", "coordinates": [-53.81, -29.68]}, "status": "ativa"},
        {"nome": "Estação Ferroviária de São Gabriel", "geometry": {"type": "Point", "coordinates": [-54.32, -30.34]}, "status": "desativada"},
        {"nome": "Estação Ferroviária de Rio Grande", "geometry": {"type": "Point", "coordinates": [-52.10, -32.03]}, "status": "desativada"},
        {"nome": "Estação Ferroviária de Pelotas", "geometry": {"type": "Point", "coordinates": [-52.34, -31.77]}, "status": "desativada"},
    ],
    "travessia_balsa": [
        {"nome": "Travessia São Borja - Santo Tomé", "geometry": {"type": "Point", "coordinates": [-56.01, -28.66]}, "capacidade_veiculos": 15},
        {"nome": "Travessia Porto Xavier - San Javier", "geometry": {"type": "Point", "coordinates": [-54.62, -27.91]}, "capacidade_veiculos": 10},
        {"nome": "Travessia Itaqui - Alvear", "geometry": {"type": "Point", "coordinates": [-56.55, -29.12]}, "capacidade_veiculos": 12},
        {"nome": "Travessia Porto Mauá - Alba Posse", "geometry": {"type": "Point", "coordinates": [-54.06, -27.58]}, "capacidade_veiculos": 8},
    ],

    # ─── Vertical Obstacles ───────────────────────────────────
    "torre_comunicacao": [
        {"nome": "Torre Telecom Santa Maria Centro", "geometry": {"type": "Point", "coordinates": [-53.80, -29.69]}, "altura_m": 80},
        {"nome": "Torre Telecom Santa Maria Camobi", "geometry": {"type": "Point", "coordinates": [-53.72, -29.71]}, "altura_m": 60},
        {"nome": "Torre Telecom Porto Alegre Norte", "geometry": {"type": "Point", "coordinates": [-51.15, -29.95]}, "altura_m": 95},
        {"nome": "Torre Telecom Porto Alegre Sul", "geometry": {"type": "Point", "coordinates": [-51.20, -30.15]}, "altura_m": 70},
        {"nome": "Torre Telecom Porto Alegre Centro", "geometry": {"type": "Point", "coordinates": [-51.22, -30.02]}, "altura_m": 88},
        {"nome": "Torre Telecom Uruguaiana Centro", "geometry": {"type": "Point", "coordinates": [-57.05, -29.77]}, "altura_m": 65},
        {"nome": "Torre Telecom Uruguaiana Norte", "geometry": {"type": "Point", "coordinates": [-57.08, -29.73]}, "altura_m": 55},
        {"nome": "Torre Telecom Uruguaiana Leste", "geometry": {"type": "Point", "coordinates": [-57.02, -29.78]}, "altura_m": 60},
        {"nome": "Torre Telecom Caxias do Sul", "geometry": {"type": "Point", "coordinates": [-51.17, -29.17]}, "altura_m": 85},
        {"nome": "Torre Telecom Pelotas", "geometry": {"type": "Point", "coordinates": [-52.35, -31.76]}, "altura_m": 75},
        {"nome": "Torre Telecom Bagé", "geometry": {"type": "Point", "coordinates": [-54.10, -31.33]}, "altura_m": 60},
        {"nome": "Torre Telecom Alegrete", "geometry": {"type": "Point", "coordinates": [-55.79, -29.79]}, "altura_m": 55},
        {"nome": "Torre Telecom Rosário do Sul", "geometry": {"type": "Point", "coordinates": [-54.92, -30.25]}, "altura_m": 50},
        {"nome": "Torre Telecom São Gabriel", "geometry": {"type": "Point", "coordinates": [-54.33, -30.34]}, "altura_m": 58},
        {"nome": "Torre Telecom Livramento", "geometry": {"type": "Point", "coordinates": [-55.53, -30.89]}, "altura_m": 62},
    ],
    "aerogerador": [
        {"nome": "Aerogerador Osório I-01", "geometry": {"type": "Point", "coordinates": [-50.22, -29.85]}, "altura_m": 120, "potencia_mw": 2.0},
        {"nome": "Aerogerador Osório I-02", "geometry": {"type": "Point", "coordinates": [-50.25, -29.87]}, "altura_m": 120, "potencia_mw": 2.0},
        {"nome": "Aerogerador Osório II-01", "geometry": {"type": "Point", "coordinates": [-50.28, -29.83]}, "altura_m": 130, "potencia_mw": 3.0},
        {"nome": "Aerogerador Osório II-02", "geometry": {"type": "Point", "coordinates": [-50.30, -29.86]}, "altura_m": 130, "potencia_mw": 3.0},
        {"nome": "Aerogerador Palmares do Sul 1", "geometry": {"type": "Point", "coordinates": [-50.50, -30.25]}, "altura_m": 110, "potencia_mw": 2.5},
        {"nome": "Aerogerador Palmares do Sul 2", "geometry": {"type": "Point", "coordinates": [-50.52, -30.27]}, "altura_m": 110, "potencia_mw": 2.5},
        {"nome": "Aerogerador Chuí 1", "geometry": {"type": "Point", "coordinates": [-53.37, -33.70]}, "altura_m": 140, "potencia_mw": 3.5},
        {"nome": "Aerogerador Chuí 2", "geometry": {"type": "Point", "coordinates": [-53.35, -33.68]}, "altura_m": 140, "potencia_mw": 3.5},
        {"nome": "Aerogerador Livramento", "geometry": {"type": "Point", "coordinates": [-55.50, -30.95]}, "altura_m": 100, "potencia_mw": 2.0},
    ],
    "linha_transmissao": [
        {"nome": "LT 500kV Itá - Porto Alegre", "geometry": {"type": "LineString", "coordinates": [[-52.3, -27.3], [-51.5, -29.0], [-51.2, -30.0]]}, "altura_m": 45, "tensao_kv": 500},
        {"nome": "LT 230kV Santa Maria - Alegrete", "geometry": {"type": "LineString", "coordinates": [[-53.8, -29.7], [-54.5, -30.0], [-55.8, -29.8]]}, "altura_m": 35, "tensao_kv": 230},
        {"nome": "LT 525kV Caxias - POA", "geometry": {"type": "LineString", "coordinates": [[-51.2, -29.2], [-51.1, -29.6], [-51.2, -30.0]]}, "altura_m": 50, "tensao_kv": 525},
        {"nome": "LT 230kV Rosário do Sul - São Gabriel", "geometry": {"type": "LineString", "coordinates": [[-54.9, -30.3], [-54.5, -30.3], [-54.3, -30.3]]}, "altura_m": 32, "tensao_kv": 230},
        {"nome": "LT 138kV Cachoeira - Santa Maria", "geometry": {"type": "LineString", "coordinates": [[-52.9, -30.0], [-53.3, -29.9], [-53.8, -29.7]]}, "altura_m": 28, "tensao_kv": 138},
        {"nome": "LT 230kV Pelotas - Rio Grande", "geometry": {"type": "LineString", "coordinates": [[-52.3, -31.8], [-52.2, -32.0]]}, "altura_m": 33, "tensao_kv": 230},
    ],
    "chamine_industrial": [
        {"nome": "Chaminé REFAP Canoas", "geometry": {"type": "Point", "coordinates": [-51.18, -29.90]}, "altura_m": 60},
        {"nome": "Chaminé CMPC Guaíba", "geometry": {"type": "Point", "coordinates": [-51.33, -30.12]}, "altura_m": 55},
        {"nome": "Chaminé Polo Petroquímico Triunfo", "geometry": {"type": "Point", "coordinates": [-51.72, -29.87]}, "altura_m": 70},
    ],

    # ─── Aviation ─────────────────────────────────────────────
    "aeroporto": [
        {"nome": "Aeroporto Salgado Filho (Porto Alegre)", "geometry": {"type": "Point", "coordinates": [-51.17, -29.99]}, "pista_m": 3200, "tipo_operacao": "civil"},
        {"nome": "Aeroporto de Santa Maria", "geometry": {"type": "Point", "coordinates": [-53.69, -29.71]}, "pista_m": 2100, "tipo_operacao": "misto"},
        {"nome": "Aeroporto de Bagé", "geometry": {"type": "Point", "coordinates": [-54.11, -31.39]}, "pista_m": 1500, "tipo_operacao": "misto"},
        {"nome": "Aeroporto de Pelotas", "geometry": {"type": "Point", "coordinates": [-52.33, -31.72]}, "pista_m": 1800, "tipo_operacao": "civil"},
        {"nome": "Aeroporto de Uruguaiana", "geometry": {"type": "Point", "coordinates": [-57.04, -29.78]}, "pista_m": 1650, "tipo_operacao": "civil"},
        {"nome": "Aeroporto de Caxias do Sul", "geometry": {"type": "Point", "coordinates": [-51.19, -29.20]}, "pista_m": 1500, "tipo_operacao": "civil"},
        {"nome": "Aeroporto de São Gabriel", "geometry": {"type": "Point", "coordinates": [-54.31, -30.36]}, "pista_m": 1200, "tipo_operacao": "misto"},
        {"nome": "Aeroporto de Florianópolis", "geometry": {"type": "Point", "coordinates": [-48.55, -27.67]}, "pista_m": 2300, "tipo_operacao": "civil"},
        {"nome": "Aeroporto Afonso Pena (Curitiba)", "geometry": {"type": "Point", "coordinates": [-49.17, -25.53]}, "pista_m": 2200, "tipo_operacao": "civil"},
    ],
    "heliporto": [
        {"nome": "Heliporto HCPA Porto Alegre", "geometry": {"type": "Point", "coordinates": [-51.21, -30.04]}, "tipo_operacao": "público"},
        {"nome": "Heliporto Base Aérea Santa Maria", "geometry": {"type": "Point", "coordinates": [-53.70, -29.72]}, "tipo_operacao": "militar"},
        {"nome": "Heliporto Brigada Militar Pelotas", "geometry": {"type": "Point", "coordinates": [-52.35, -31.78]}, "tipo_operacao": "militar"},
        {"nome": "Heliporto Uruguaiana", "geometry": {"type": "Point", "coordinates": [-57.06, -29.77]}, "tipo_operacao": "público"},
    ],
    "campo_pouso": [
        {"nome": "Campo de Pouso São Borja", "geometry": {"type": "Point", "coordinates": [-56.02, -28.67]}, "pista_m": 800, "superficie": "grama"},
        {"nome": "Campo de Pouso Alegrete", "geometry": {"type": "Point", "coordinates": [-55.80, -29.80]}, "pista_m": 900, "superficie": "terra"},
        {"nome": "Campo de Pouso Jaguarão", "geometry": {"type": "Point", "coordinates": [-53.40, -32.58]}, "pista_m": 700, "superficie": "grama"},
        {"nome": "Campo de Pouso Rosário do Sul", "geometry": {"type": "Point", "coordinates": [-54.90, -30.26]}, "pista_m": 600, "superficie": "grama"},
        {"nome": "Campo de Pouso Quaraí", "geometry": {"type": "Point", "coordinates": [-56.45, -30.39]}, "pista_m": 750, "superficie": "terra"},
        {"nome": "Campo de Pouso Livramento", "geometry": {"type": "Point", "coordinates": [-55.55, -30.88]}, "pista_m": 850, "superficie": "grama"},
    ],

    # ─── Social Infrastructure ────────────────────────────────
    "hospital": [
        {"nome": "Hospital de Guarnição de Santa Maria", "geometry": {"type": "Point", "coordinates": [-53.80, -29.69]}, "leitos": 150, "tipo_hospital": "militar"},
        {"nome": "Hospital Universitário de Santa Maria", "geometry": {"type": "Point", "coordinates": [-53.72, -29.72]}, "leitos": 403, "tipo_hospital": "geral"},
        {"nome": "Hospital de Clínicas de Porto Alegre", "geometry": {"type": "Point", "coordinates": [-51.21, -30.04]}, "leitos": 842, "tipo_hospital": "geral"},
        {"nome": "Hospital Moinhos de Vento (Porto Alegre)", "geometry": {"type": "Point", "coordinates": [-51.20, -30.02]}, "leitos": 420, "tipo_hospital": "especializado"},
        {"nome": "Hospital Santa Casa de Alegrete", "geometry": {"type": "Point", "coordinates": [-55.79, -29.78]}, "leitos": 120, "tipo_hospital": "geral"},
        {"nome": "Hospital de Cachoeira do Sul", "geometry": {"type": "Point", "coordinates": [-52.89, -30.04]}, "leitos": 180, "tipo_hospital": "geral"},
        {"nome": "Hospital São Francisco de Paula (Pelotas)", "geometry": {"type": "Point", "coordinates": [-52.34, -31.77]}, "leitos": 250, "tipo_hospital": "geral"},
        {"nome": "Hospital de Uruguaiana", "geometry": {"type": "Point", "coordinates": [-57.08, -29.76]}, "leitos": 160, "tipo_hospital": "geral"},
        {"nome": "Hospital de Jaguarão", "geometry": {"type": "Point", "coordinates": [-53.38, -32.57]}, "leitos": 80, "tipo_hospital": "geral"},
        {"nome": "Hospital de Bagé", "geometry": {"type": "Point", "coordinates": [-54.10, -31.33]}, "leitos": 200, "tipo_hospital": "geral"},
        {"nome": "Hospital de São Gabriel", "geometry": {"type": "Point", "coordinates": [-54.32, -30.34]}, "leitos": 110, "tipo_hospital": "geral"},
        {"nome": "Hospital de Rosário do Sul", "geometry": {"type": "Point", "coordinates": [-54.91, -30.25]}, "leitos": 90, "tipo_hospital": "geral"},
        {"nome": "Hospital de Caxias do Sul", "geometry": {"type": "Point", "coordinates": [-51.18, -29.17]}, "leitos": 350, "tipo_hospital": "geral"},
        {"nome": "Hospital de Livramento", "geometry": {"type": "Point", "coordinates": [-55.53, -30.89]}, "leitos": 130, "tipo_hospital": "geral"},
        {"nome": "Hospital de Rio Grande", "geometry": {"type": "Point", "coordinates": [-52.10, -32.03]}, "leitos": 220, "tipo_hospital": "geral"},
    ],
    "escola": [
        {"nome": "Escola Municipal Alegrete Centro", "geometry": {"type": "Point", "coordinates": [-55.79, -29.78]}, "alunos": 400, "tipo_escola": "pública"},
        {"nome": "Escola Estadual Alegrete Norte", "geometry": {"type": "Point", "coordinates": [-55.78, -29.76]}, "alunos": 320, "tipo_escola": "pública"},
        {"nome": "Escola Estadual Santa Maria", "geometry": {"type": "Point", "coordinates": [-53.81, -29.69]}, "alunos": 600, "tipo_escola": "pública"},
        {"nome": "Escola Municipal Santa Maria Camobi", "geometry": {"type": "Point", "coordinates": [-53.73, -29.72]}, "alunos": 450, "tipo_escola": "pública"},
        {"nome": "Escola Municipal Uruguaiana", "geometry": {"type": "Point", "coordinates": [-57.08, -29.77]}, "alunos": 350, "tipo_escola": "pública"},
        {"nome": "Escola Estadual Uruguaiana Centro", "geometry": {"type": "Point", "coordinates": [-57.06, -29.76]}, "alunos": 500, "tipo_escola": "pública"},
        {"nome": "Escola Estadual Porto Alegre", "geometry": {"type": "Point", "coordinates": [-51.22, -30.03]}, "alunos": 800, "tipo_escola": "pública"},
        {"nome": "Escola Municipal Cachoeira do Sul", "geometry": {"type": "Point", "coordinates": [-52.90, -30.05]}, "alunos": 450, "tipo_escola": "pública"},
        {"nome": "Escola Estadual Pelotas", "geometry": {"type": "Point", "coordinates": [-52.34, -31.76]}, "alunos": 550, "tipo_escola": "pública"},
        {"nome": "Escola Municipal Jaguarão", "geometry": {"type": "Point", "coordinates": [-53.38, -32.56]}, "alunos": 280, "tipo_escola": "pública"},
        {"nome": "Escola Municipal Bagé", "geometry": {"type": "Point", "coordinates": [-54.10, -31.34]}, "alunos": 380, "tipo_escola": "pública"},
    ],
    "posto_combustivel": [
        # Cidades
        {"nome": "Posto BR Alegrete", "geometry": {"type": "Point", "coordinates": [-55.79, -29.77]}, "bandeira": "BR"},
        {"nome": "Posto Shell Santa Maria", "geometry": {"type": "Point", "coordinates": [-53.82, -29.68]}, "bandeira": "Shell"},
        {"nome": "Posto BR Uruguaiana", "geometry": {"type": "Point", "coordinates": [-57.07, -29.76]}, "bandeira": "BR"},
        {"nome": "Posto Ipiranga Cachoeira do Sul", "geometry": {"type": "Point", "coordinates": [-52.90, -30.03]}, "bandeira": "Ipiranga"},
        {"nome": "Posto Shell São Gabriel", "geometry": {"type": "Point", "coordinates": [-54.32, -30.34]}, "bandeira": "Shell"},
        {"nome": "Posto BR Pelotas", "geometry": {"type": "Point", "coordinates": [-52.34, -31.76]}, "bandeira": "BR"},
        {"nome": "Posto Ipiranga Porto Alegre", "geometry": {"type": "Point", "coordinates": [-51.18, -30.01]}, "bandeira": "Ipiranga"},
        {"nome": "Posto Shell Livramento", "geometry": {"type": "Point", "coordinates": [-55.53, -30.89]}, "bandeira": "Shell"},
        {"nome": "Posto BR Bagé", "geometry": {"type": "Point", "coordinates": [-54.10, -31.33]}, "bandeira": "BR"},
        {"nome": "Posto Ipiranga Jaguarão", "geometry": {"type": "Point", "coordinates": [-53.38, -32.56]}, "bandeira": "Ipiranga"},
        # BR-290 corredor
        {"nome": "Posto Ipiranga Rosário do Sul (BR-290)", "geometry": {"type": "Point", "coordinates": [-54.91, -30.25]}, "bandeira": "Ipiranga"},
        {"nome": "Posto BR São Gabriel (BR-290)", "geometry": {"type": "Point", "coordinates": [-54.35, -30.30]}, "bandeira": "BR"},
        {"nome": "Posto Shell Dom Pedrito (BR-290)", "geometry": {"type": "Point", "coordinates": [-54.7, -30.1]}, "bandeira": "Shell"},
    ],

    # ─── Water Infrastructure ─────────────────────────────────
    "barragem": [
        {"nome": "Barragem do DNOS (Santa Maria)", "geometry": {"type": "Point", "coordinates": [-53.8, -29.7]}, "altura_m": 25, "capacidade_hm3": 12.0},
        {"nome": "Barragem do Passo Real (Jacuí)", "geometry": {"type": "Point", "coordinates": [-53.2, -29.0]}, "altura_m": 45, "capacidade_hm3": 3680.0},
        {"nome": "Barragem Dona Francisca (Jacuí)", "geometry": {"type": "Point", "coordinates": [-53.28, -29.45]}, "altura_m": 58, "capacidade_hm3": 840.0},
        {"nome": "Barragem Itaúba (Jacuí)", "geometry": {"type": "Point", "coordinates": [-52.8, -29.35]}, "altura_m": 35, "capacidade_hm3": 520.0},
        {"nome": "Barragem do Arroio Duro (Pelotas)", "geometry": {"type": "Point", "coordinates": [-52.5, -31.6]}, "altura_m": 20, "capacidade_hm3": 90.0},
        {"nome": "Barragem do Lomba do Sabão (Porto Alegre)", "geometry": {"type": "Point", "coordinates": [-51.12, -30.05]}, "altura_m": 18, "capacidade_hm3": 8.0},
    ],
    "reservatorio": [
        {"nome": "Reservatório Lomba do Sabão (POA)", "geometry": {"type": "Point", "coordinates": [-51.12, -30.05]}, "capacidade_hm3": 2.5},
        {"nome": "Reservatório Guaíba (POA)", "geometry": {"type": "Point", "coordinates": [-51.18, -30.10]}, "capacidade_hm3": 5.0},
        {"nome": "Reservatório Santa Maria", "geometry": {"type": "Point", "coordinates": [-53.80, -29.72]}, "capacidade_hm3": 3.0},
    ],
    "estacao_tratamento_agua": [
        {"nome": "ETA Menino Deus (Porto Alegre)", "geometry": {"type": "Point", "coordinates": [-51.22, -30.06]}, "capacidade_ls": 3000},
        {"nome": "ETA São João (Santa Maria)", "geometry": {"type": "Point", "coordinates": [-53.79, -29.70]}, "capacidade_ls": 800},
        {"nome": "ETA Pelotas", "geometry": {"type": "Point", "coordinates": [-52.35, -31.75]}, "capacidade_ls": 1200},
        {"nome": "ETA Guaíba (Porto Alegre)", "geometry": {"type": "Point", "coordinates": [-51.19, -30.08]}, "capacidade_ls": 4500},
    ],

    # ─── Territorial ──────────────────────────────────────────
    "terra_indigena": [
        {"nome": "TI Guarita", "geometry": {"type": "Polygon", "coordinates": [[[-53.6, -27.4], [-53.2, -27.4], [-53.2, -27.1], [-53.6, -27.1], [-53.6, -27.4]]]}, "etnia": "Kaingang", "area_km2": 236, "status": "homologada"},
        {"nome": "TI Nonoai", "geometry": {"type": "Polygon", "coordinates": [[[-53.2, -27.5], [-52.8, -27.5], [-52.8, -27.2], [-53.2, -27.2], [-53.2, -27.5]]]}, "etnia": "Kaingang", "area_km2": 167, "status": "homologada"},
        {"nome": "TI Cacique Doble", "geometry": {"type": "Polygon", "coordinates": [[[-51.7, -28.1], [-51.5, -28.1], [-51.5, -27.9], [-51.7, -27.9], [-51.7, -28.1]]]}, "etnia": "Kaingang", "area_km2": 46, "status": "homologada"},
        {"nome": "TI Iraí", "geometry": {"type": "Polygon", "coordinates": [[[-53.3, -27.2], [-53.1, -27.2], [-53.1, -27.0], [-53.3, -27.0], [-53.3, -27.2]]]}, "etnia": "Kaingang", "area_km2": 280, "status": "em_estudo"},
        {"nome": "TI Ligeiro", "geometry": {"type": "Polygon", "coordinates": [[[-52.6, -28.1], [-52.4, -28.1], [-52.4, -27.9], [-52.6, -27.9], [-52.6, -28.1]]]}, "etnia": "Kaingang", "area_km2": 48, "status": "homologada"},
        {"nome": "TI Votouro", "geometry": {"type": "Polygon", "coordinates": [[[-52.1, -27.7], [-51.9, -27.7], [-51.9, -27.5], [-52.1, -27.5], [-52.1, -27.7]]]}, "etnia": "Kaingang", "area_km2": 30, "status": "homologada"},
    ],
    "edificacao_destaque": [
        {"nome": "Edifício Sulacap (Porto Alegre)", "geometry": {"type": "Point", "coordinates": [-51.23, -30.03]}, "altura_m": 80, "tipo_edificacao": "comercial"},
        {"nome": "Edifício Santa Cruz (Porto Alegre)", "geometry": {"type": "Point", "coordinates": [-51.22, -30.04]}, "altura_m": 95, "tipo_edificacao": "residencial"},
        {"nome": "Torre Panorâmica (Curitiba)", "geometry": {"type": "Point", "coordinates": [-49.27, -25.43]}, "altura_m": 109, "tipo_edificacao": "comercial"},
        {"nome": "Edifício Bourbon Business (Curitiba)", "geometry": {"type": "Point", "coordinates": [-49.28, -25.44]}, "altura_m": 128, "tipo_edificacao": "comercial"},
        {"nome": "Edifício Órion (Londrina)", "geometry": {"type": "Point", "coordinates": [-51.16, -23.31]}, "altura_m": 93, "tipo_edificacao": "residencial"},
        {"nome": "Edifício Barigui (Curitiba)", "geometry": {"type": "Point", "coordinates": [-49.30, -25.42]}, "altura_m": 140, "tipo_edificacao": "residencial"},
    ],

    # ─── Military Training ────────────────────────────────────
    "area_treinamento": [
        {"nome": "Campo de Instrução de Santa Maria", "geometry": {"type": "Polygon", "coordinates": [[[-53.9, -29.8], [-53.6, -29.8], [-53.6, -29.6], [-53.9, -29.6], [-53.9, -29.8]]]}, "tipo_treinamento": "infantaria"},
        {"nome": "Campo de Instrução de Rosário do Sul", "geometry": {"type": "Polygon", "coordinates": [[[-55.0, -30.4], [-54.8, -30.4], [-54.8, -30.2], [-55.0, -30.2], [-55.0, -30.4]]]}, "tipo_treinamento": "cavalaria"},
    ],
}


# ═══════════════════════════════════════════════════════════════════
# MILITARY INSTALLATIONS
# ═══════════════════════════════════════════════════════════════════

MILITARY_INSTALLATIONS = {
    "8 bda inf mec": {
        "nome_completo": "8ª Brigada de Infantaria Mecanizada",
        "sigla": "8ª Bda Inf Mec",
        "cidade": "Pelotas",
        "uf": "RS",
        "geometry": {"type": "Point", "coordinates": [-52.34, -31.77]},
    },
    "3 bec": {
        "nome_completo": "3º Batalhão de Engenharia de Combate",
        "sigla": "3º BECmb",
        "cidade": "Cachoeira do Sul",
        "uf": "RS",
        "geometry": {"type": "Point", "coordinates": [-52.89, -30.04]},
    },
}


# ═══════════════════════════════════════════════════════════════════
# PRODUCT TYPE EXPLANATIONS
# ═══════════════════════════════════════════════════════════════════

PRODUCT_TYPE_EXPLANATIONS = {
    "carta_topografica": "Carta topográfica: representação detalhada do terreno com curvas de nível, hidrografia, vegetação, vias e edificações. Escalas típicas: 1:25.000, 1:50.000, 1:100.000, 1:250.000.",
    "ortoimagem": "Ortoimagem: imagem aérea ou de satélite geometricamente corrigida (ortorretificada). Pode ser usada como base cartográfica.",
    "mds": "MDS (Modelo Digital de Superfície): representa a superfície incluindo construções e vegetação. Diferente do MDT que mostra apenas o terreno nu.",
    "mdt": "MDT (Modelo Digital de Terreno): representa o terreno nu, sem construções ou vegetação. Diferente do MDS.",
    "imagem_drone": "Imagem de drone (VANT/RPA): levantamento aéreo de alta resolução (centimétrica) com cobertura local.",
    "imagem_satelite": "Imagem de satélite: cobertura ampla com resolução variável (0.3m a 30m dependendo do sensor).",
    "obstaculo_vertical": "Obstáculo vertical: qualquer estrutura que se projeta acima do terreno e pode representar risco à navegação aérea. Exemplos: torres de comunicação, aerogeradores, linhas de transmissão, chaminés industriais.",
    "campo_pouso": "Campo de pouso: pista de pouso e decolagem não pavimentada ou de pequeno porte, geralmente em áreas rurais ou militares. Diferente de aeroporto por não ter infraestrutura de terminal.",
    "faixa_fronteira": "Faixa de fronteira: faixa de 150 km de largura ao longo das fronteiras terrestres, considerada indispensável à segurança nacional (Lei 6.634/1979).",
}


# ═══════════════════════════════════════════════════════════════════
# AUTOCOMPLETE — keyed by lowercase fragment
# ═══════════════════════════════════════════════════════════════════

AUTOCOMPLETE = {
    "santa": ["Santa Maria, RS", "Santa Cruz do Sul, RS", "Santa Rosa, RS", "Santana do Livramento, RS", "Santa Cruz, RN"],
    "são j": ["São José, SC", "São José dos Campos, SP", "São José do Rio Preto, SP"],
    "são g": ["São Gabriel, RS", "São Gonçalo, RJ"],
    "uru": ["Uruguaiana, RS"],
    "cach": ["Cachoeira do Sul, RS", "Cachoeirinha, RS"],
}
