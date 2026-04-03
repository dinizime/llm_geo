"""Deterministic synthetic data for testing tool calling without a real database."""

MUNICIPALITIES = {
    ("alecrim", "rs"): {
        "nome": "Alecrim",
        "uf": "RS",
        "codigo_ibge": "4300406",
        "populacao": 6685,
        "geometry": {"type": "Polygon", "coordinates": [[[-54.8, -27.7], [-54.7, -27.7], [-54.7, -27.6], [-54.8, -27.6], [-54.8, -27.7]]]},
    },
    ("porto alegre", "rs"): {
        "nome": "Porto Alegre",
        "uf": "RS",
        "codigo_ibge": "4314902",
        "populacao": 1488252,
        "geometry": {"type": "Polygon", "coordinates": [[[-51.3, -30.2], [-51.0, -30.2], [-51.0, -29.9], [-51.3, -29.9], [-51.3, -30.2]]]},
    },
    ("santa maria", "rs"): {
        "nome": "Santa Maria",
        "uf": "RS",
        "codigo_ibge": "4316907",
        "populacao": 283677,
        "geometry": {"type": "Polygon", "coordinates": [[[-53.9, -29.8], [-53.7, -29.8], [-53.7, -29.6], [-53.9, -29.6], [-53.9, -29.8]]]},
    },
    ("brasília", "df"): {
        "nome": "Brasília",
        "uf": "DF",
        "codigo_ibge": "5300108",
        "populacao": 3094325,
        "geometry": {"type": "Polygon", "coordinates": [[[-48.0, -15.9], [-47.7, -15.9], [-47.7, -15.6], [-48.0, -15.6], [-48.0, -15.9]]]},
    },
    ("manaus", "am"): {
        "nome": "Manaus",
        "uf": "AM",
        "codigo_ibge": "1302603",
        "populacao": 2255903,
        "geometry": {"type": "Polygon", "coordinates": [[[-60.1, -3.2], [-59.8, -3.2], [-59.8, -2.9], [-60.1, -2.9], [-60.1, -3.2]]]},
    },
}

GEOCODE_RESULTS = {
    "usina hidrelétrica de itaipu": {"lat": -25.41, "lon": -54.59, "display_name": "Usina Hidrelétrica de Itaipu"},
    "itaipu": {"lat": -25.41, "lon": -54.59, "display_name": "Usina Hidrelétrica de Itaipu"},
    "alecrim, rs": {"lat": -27.66, "lon": -54.73, "display_name": "Alecrim, RS"},
    "santa maria, rs": {"lat": -29.68, "lon": -53.81, "display_name": "Santa Maria, RS"},
    "alegrete, rs": {"lat": -29.78, "lon": -55.79, "display_name": "Alegrete, RS"},
    "florianópolis, sc": {"lat": -27.59, "lon": -48.55, "display_name": "Florianópolis, SC"},
    "porto alegre, rs": {"lat": -30.03, "lon": -51.23, "display_name": "Porto Alegre, RS"},
}

STATES = {
    "rs": {
        "uf": "RS",
        "nome": "Rio Grande do Sul",
        "geometry": {"type": "Polygon", "coordinates": [[[-57.6, -33.8], [-49.7, -33.8], [-49.7, -27.1], [-57.6, -27.1], [-57.6, -33.8]]]},
    },
    "sp": {
        "uf": "SP",
        "nome": "São Paulo",
        "geometry": {"type": "Polygon", "coordinates": [[[-53.1, -25.3], [-44.2, -25.3], [-44.2, -19.8], [-53.1, -19.8], [-53.1, -25.3]]]},
    },
}

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
}

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

FEATURES = {
    "ponte": [
        {"nome": "Ponte sobre o Rio Vacacaí", "geometry": {"type": "Point", "coordinates": [-53.5, -29.7]}},
        {"nome": "Ponte sobre o Rio Ibicuí", "geometry": {"type": "Point", "coordinates": [-55.2, -29.5]}},
    ],
    "barragem": [
        {"nome": "Barragem do DNOS", "geometry": {"type": "Point", "coordinates": [-53.8, -29.7]}},
    ],
    "aeroporto": [
        {"nome": "Aeroporto Salgado Filho", "geometry": {"type": "Point", "coordinates": [-51.17, -29.99]}},
    ],
}

HYDROGRAPHY = {
    "rio jacuí": {
        "nome": "Rio Jacuí",
        "tipo": "rio",
        "geometry": {"type": "LineString", "coordinates": [[-53.5, -29.5], [-52.5, -29.8], [-51.5, -30.0]]},
    },
    "rio guaíba": {
        "nome": "Rio Guaíba",
        "tipo": "rio",
        "geometry": {"type": "LineString", "coordinates": [[-51.25, -30.0], [-51.2, -30.1], [-51.15, -30.25]]},
    },
}

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

PRODUCT_TYPE_EXPLANATIONS = {
    "carta_topografica": "Carta topográfica: representação detalhada do terreno com curvas de nível, hidrografia, vegetação, vias e edificações. Escalas típicas: 1:25.000, 1:50.000, 1:100.000, 1:250.000.",
    "ortoimagem": "Ortoimagem: imagem aérea ou de satélite geometricamente corrigida (ortorretificada). Pode ser usada como base cartográfica.",
    "mds": "MDS (Modelo Digital de Superfície): representa a superfície incluindo construções e vegetação. Diferente do MDT que mostra apenas o terreno nu.",
    "mdt": "MDT (Modelo Digital de Terreno): representa o terreno nu, sem construções ou vegetação. Diferente do MDS.",
    "imagem_drone": "Imagem de drone (VANT/RPA): levantamento aéreo de alta resolução (centimétrica) com cobertura local.",
    "imagem_satelite": "Imagem de satélite: cobertura ampla com resolução variável (0.3m a 30m dependendo do sensor).",
}

AUTOCOMPLETE = {
    "santa": ["Santa Maria, RS", "Santa Cruz do Sul, RS", "Santa Rosa, RS", "Santana do Livramento, RS", "Santa Cruz, RN"],
    "são j": ["São José, SC", "São José dos Campos, SP", "São José do Rio Preto, SP"],
}
