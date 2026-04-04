"""Tool definitions (JSON schema) sent to the LLM."""

# ── Closed sets used as enums ──────────────────────────────────
FEATURE_TYPES = [
    "ponte", "tunel", "estacao_ferroviaria", "travessia_balsa",
    "torre_comunicacao", "aerogerador", "linha_transmissao", "chamine_industrial",
    "aeroporto", "heliporto", "campo_pouso",
    "hospital", "escola", "posto_combustivel",
    "barragem", "reservatorio", "estacao_tratamento_agua",
    "terra_indigena", "edificacao_destaque",
    "area_treinamento",
]

PRODUCT_TYPES = [
    "carta_topografica", "ortoimagem", "mds", "mdt",
    "imagem_drone", "imagem_satelite", "modelo_3d", "nuvem_pontos",
]

FILTER_OPERATORS = [">", "<", ">=", "<=", "=", "in"]

TOOLS = [
    # ═══════════════════════════════════════════════════════════════
    # 1. GEOGRAPHIC LOOKUPS — resolve names/coordinates to geometry_ref
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "geocode",
            "description": (
                "Resolve a place name, address, or POI into coordinates and geometry_ref. "
                "Use when the user mentions a specific place (city, landmark, POI). "
                "Do NOT use for municipalities — use search_municipality instead. "
                "Do NOT use when the user gives raw lat/lon — use create_point instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {
                        "type": "string",
                        "description": "Place name. Include state when possible. E.g. 'Usina de Itaipu', 'Alecrim, RS'",
                    }
                },
                "required": ["place_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_point",
            "description": (
                "Creates a point geometry from raw lat/lon coordinates. Returns geometry_ref. "
                "Use ONLY when the user provides explicit numeric coordinates. "
                "Do NOT use when the user gives a place name — use geocode instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude (e.g. -29.78)"},
                    "lon": {"type": "number", "description": "Longitude (e.g. -55.79)"},
                    "label": {"type": "string", "description": "Optional label for this point"},
                },
                "required": ["lat", "lon"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reverse_geocode",
            "description": (
                "Determines which municipality a coordinate falls in. "
                "Returns municipio, uf, estado. "
                "Use when you have coordinates and need to know the municipality name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude"},
                    "lon": {"type": "number", "description": "Longitude"},
                    "geometry_ref": {"type": "string", "description": "Point geometry_ref (alternative to lat/lon)"},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_municipality",
            "description": (
                "Returns the polygon, population, and IBGE code of a Brazilian municipality. "
                "Use for any question about a specific municipality (area, products, features in it). "
                "If the name is ambiguous (e.g. 'Santa Cruz'), returns candidate list with uf — "
                "pick the most likely candidate and call again with uf to get the geometry_ref, "
                "then continue with the next tool in the chain (e.g. search_products)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Municipality name (e.g. 'Alegrete')"},
                    "uf": {"type": "string", "description": "State abbreviation to disambiguate (e.g. 'RS')"},
                },
                "required": ["nome"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_state",
            "description": "Returns the polygon of a Brazilian state. Use for state-level queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "uf": {"type": "string", "description": "State abbreviation (e.g. 'RS', 'SP')"},
                },
                "required": ["uf"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_named_region",
            "description": (
                "Returns geometry of informal/geographic regions that are NOT administrative divisions. "
                "Examples: Serra Gaúcha, Pantanal, Litoral Norte, Vale do Taquari, Amazônia Legal. "
                "Do NOT use for municipalities or states — use search_municipality or search_state."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Region name"},
                },
                "required": ["nome"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hydrography",
            "description": (
                "Search rivers, lakes, lagoons, or basins by name. Returns geometry_ref (LineString or Polygon). "
                "Use for any question involving water bodies."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Waterbody name (e.g. 'Rio Uruguai')"},
                    "tipo": {
                        "type": "string",
                        "enum": ["rio", "lago", "lagoa", "bacia"],
                        "description": "Type of water body (optional)",
                    },
                    "uf": {"type": "string", "description": "Filter by state (optional)"},
                },
                "required": ["nome"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_border",
            "description": (
                "Returns the international border of Brazil with a neighbor country (LineString). "
                "Use for questions about borders, border regions, or faixa de fronteira."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {"type": "string", "description": "Neighbor country name (e.g. 'Argentina', 'Uruguai')"},
                    "proximidade_ref": {"type": "string", "description": "geometry_ref of point to filter nearby segment"},
                    "raio_m": {"type": "number", "description": "Radius in meters for clipping near the point"},
                },
                "required": ["pais"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_road",
            "description": (
                "Search a highway/road by its official code. Returns geometry_ref (LineString) and extensao_km. "
                "Use for questions about highways. Accepts BR or state codes: BR-101, BR-116, BR-290, RS-040."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "identificador": {"type": "string", "description": "Road code (e.g. 'BR-116', 'RS-040')"},
                    "uf": {"type": "string", "description": "State to filter segment (optional)"},
                },
                "required": ["identificador"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_military_installation",
            "description": (
                "Search military installations by name, abbreviation, or variant. "
                "Understands abbreviations: Bda=Brigada, B=Batalhão, Cia=Companhia, "
                "Inf=Infantaria, Mec=Mecanizada, Eng=Engenharia. "
                "Returns nome_completo, sigla, cidade, uf, geometry_ref."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_ou_sigla": {"type": "string", "description": "Name or abbreviation (e.g. '8ª Bda Inf Mec')"},
                    "cidade": {"type": "string", "description": "City for disambiguation (optional)"},
                },
                "required": ["nome_ou_sigla"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 2. FEATURE SEARCH — find geographic features within areas/routes
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "search_features",
            "description": (
                "Search geographic features of a specific type WITHIN an area (polygon or buffer). "
                "Returns list of features with attributes and geometry_ref. "
                "Use for: 'quantas pontes em Alegrete', 'torres de comunicação no RS'. "
                "Do NOT use for 'features along a route/road' — use features_along_route instead. "
                "Do NOT use for 'nearest X from Y' — use find_nearest instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": FEATURE_TYPES,
                        "description": "Feature type to search",
                    },
                    "geometry_ref": {"type": "string", "description": "Search area geometry_ref (polygon from search_municipality, buffer, etc.)"},
                    "atributo": {
                        "type": "string",
                        "description": "Attribute to filter (e.g. 'altura_m', 'comprimento_m', 'leitos', 'pista_m', 'capacidade_ton', 'potencia_mw')",
                    },
                    "operador": {
                        "type": "string",
                        "enum": FILTER_OPERATORS,
                        "description": "Comparison operator for attribute filter",
                    },
                    "valor": {"description": "Value to compare (number for scalar ops, list for 'in')"},
                },
                "required": ["tipo", "geometry_ref"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearest",
            "description": (
                "Finds the N nearest features of a given type from a reference point. "
                "Returns features sorted by distance_km. "
                "Use for: 'hospital mais próximo', 'aeroporto mais perto de X'. "
                "Do NOT use for counting features in an area — use search_features instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": FEATURE_TYPES,
                        "description": "Feature type to search for",
                    },
                    "geometry_ref": {"type": "string", "description": "Reference point geometry_ref"},
                    "limit": {"type": "integer", "description": "Max results (default 3)"},
                },
                "required": ["tipo", "geometry_ref"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "features_along_route",
            "description": (
                "Lists features along a route or road (LineString). "
                "Applies an implicit buffer corridor and returns features ordered by position. "
                "Use for: 'pontes na rota entre A e B', 'postos ao longo da BR-290'. "
                "Requires geometry_ref from compute_route or search_road. "
                "Do NOT use buffer + search_features manually — this tool does it automatically."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": FEATURE_TYPES,
                        "description": "Feature type (e.g. ponte, hospital, posto_combustivel)",
                    },
                    "geometry_ref": {"type": "string", "description": "LineString geometry_ref (from compute_route or search_road)"},
                    "buffer_metros": {"type": "number", "description": "Corridor width in meters (default 500)"},
                },
                "required": ["tipo", "geometry_ref"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 3. SPATIAL OPERATIONS — buffer, intersect, route, predicates
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "buffer",
            "description": (
                "Creates a circular buffer zone (polygon) around any geometry. Returns geometry_ref. "
                "Use to create search areas around points, routes, or borders. "
                "Typical radii: 5000m (local), 20000m (regional), 150000m (faixa de fronteira)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "Center geometry reference"},
                    "raio_metros": {"type": "number", "description": "Buffer radius in meters"},
                },
                "required": ["geometry_ref", "raio_metros"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "intersect",
            "description": (
                "Computes the geometric intersection of two geometries. Returns geometry_ref and area_km2. "
                "Use when you need the overlapping area between two regions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string", "description": "First geometry"},
                    "geometry_ref_b": {"type": "string", "description": "Second geometry"},
                },
                "required": ["geometry_ref_a", "geometry_ref_b"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_route",
            "description": (
                "Computes a road route between two points. Returns distance_km, duration_min, geometry_ref (LineString). "
                "Use for road distance and travel time between places. "
                "Do NOT use for straight-line distance — use compute_distance instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_ref": {"type": "string", "description": "geometry_ref of origin point"},
                    "dest_ref": {"type": "string", "description": "geometry_ref of destination point"},
                },
                "required": ["origin_ref", "dest_ref"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_intersection",
            "description": (
                "Checks whether two geometries intersect (returns boolean). "
                "Use for: 'a rota passa por X?', 'o rio cruza o município?'. "
                "Do NOT use intersect (which computes the overlap geometry) — this just returns true/false."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string", "description": "First geometry"},
                    "geometry_ref_b": {"type": "string", "description": "Second geometry"},
                },
                "required": ["geometry_ref_a", "geometry_ref_b"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_contains",
            "description": (
                "Checks whether geometry A fully contains geometry B (returns boolean). "
                "Use for: 'ponto X está dentro do município Y?', 'estado contém essa região?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string", "description": "Container geometry (the larger one)"},
                    "geometry_ref_b": {"type": "string", "description": "Candidate geometry (must be fully inside A)"},
                },
                "required": ["geometry_ref_a", "geometry_ref_b"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 4. MEASUREMENT — distance, area, length
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "compute_distance",
            "description": (
                "Computes the straight-line (geodesic) distance between two geometries in km. "
                "Use for 'how far is X from Y' in straight-line terms. "
                "Do NOT use for road distance — use compute_route instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string", "description": "First geometry reference"},
                    "geometry_ref_b": {"type": "string", "description": "Second geometry reference"},
                },
                "required": ["geometry_ref_a", "geometry_ref_b"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_area",
            "description": (
                "Computes the area of a polygon in km². "
                "Use for: 'área do município X', 'tamanho da zona de buffer'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "Polygon geometry reference"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_length",
            "description": (
                "Computes the length of a line geometry (route, river, border) in km. "
                "Use for: 'comprimento da rota', 'extensão do rio', 'tamanho da fronteira'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "LineString geometry reference"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 5. PRODUCT CATALOG — search geospatial products
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search geospatial products in the catalog. Main product search tool. "
                "Requires geometry_ref from a previous tool (search_municipality, buffer, etc.). "
                "Returns products with escala, data_produto, articulacao, nome. "
                "Analyze results to find 'melhor escala' or 'mais recente'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "Search area geometry_ref"},
                    "tipo": {
                        "type": "string",
                        "description": "Product type, or '*' for all types",
                        "enum": PRODUCT_TYPES + ["*"],
                    },
                    "escala": {"type": "integer", "description": "Scale denominator filter (e.g. 25000 for 1:25,000)"},
                    "data_inicio": {"type": "string", "description": "Start date filter YYYY-MM-DD"},
                    "data_fim": {"type": "string", "description": "End date filter YYYY-MM-DD"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_articulation",
            "description": (
                "Search geospatial products by map sheet articulation code (MI or INOM). "
                "Use when the user provides an articulation code like 'SH-22-V-C-IV-1'. "
                "Do NOT use for geographic searches — use search_products instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "codigo": {"type": "string", "description": "Articulation code (e.g. 'SH-22-V-C-IV-1')"},
                },
                "required": ["codigo"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 6. SPATIAL QUERIES — municipalities, neighbors
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "list_municipalities_in",
            "description": (
                "Lists all municipalities that intersect a given geometry. "
                "Use for: 'municípios ao longo da rota', 'cidades num raio de 50km'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "Area or line geometry_ref"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_neighbors",
            "description": (
                "Returns municipalities that border a given municipality. "
                "Use for: 'municípios vizinhos de Alegrete', 'quem faz divisa com Santa Maria'. "
                "Requires geometry_ref of a municipality (from search_municipality)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "Municipality polygon geometry_ref"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 7. ELEVATION & TERRAIN
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "get_elevation",
            "description": (
                "Returns elevation of a point (elevation_m) or elevation range of a polygon "
                "(min_elevation_m, max_elevation_m, avg_elevation_m). "
                "Use for: 'altitude de Alegrete', 'elevação na coordenada X'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "Point or Polygon geometry_ref"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_terrain_profile",
            "description": (
                "Returns elevation profile along a LineString (route, road, river). "
                "Samples ~10 points. Returns min_m, max_m, avg_m, max_slope_pct, "
                "total_ascent_m, total_descent_m, classification (plano/ondulado/montanhoso). "
                "Use for: 'perfil de elevação da rota', 'terreno é montanhoso?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "LineString geometry_ref (from compute_route, search_road, or search_hydrography)"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },
]
