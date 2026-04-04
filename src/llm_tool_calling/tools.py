"""Tool definitions (JSON schema) sent to the LLM."""

TOOLS = [
    # ═══════════════════════════════════════════════════════════════
    # GEOGRAPHIC LOOKUPS
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "geocode",
            "description": (
                "Resolve a place name, address, or POI into coordinates. "
                "Returns lat, lon, display_name, and geometry_ref (point). "
                "Use when the user mentions a place that is not a municipality."
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
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_municipality",
            "description": (
                "Returns the polygon of a Brazilian municipality (geometry_ref). "
                "Use to delimit a municipality area for product search. "
                "If the name is ambiguous (e.g. 'Santa Cruz'), returns candidate list."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Municipality name"},
                    "uf": {"type": "string", "description": "State abbreviation (2 letters). Helps disambiguate."},
                },
                "required": ["nome"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_state",
            "description": "Returns the polygon of a Brazilian state by abbreviation. Returns geometry_ref.",
            "parameters": {
                "type": "object",
                "properties": {
                    "uf": {"type": "string", "description": "State abbreviation (e.g. 'RS', 'SP')"},
                },
                "required": ["uf"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_named_region",
            "description": (
                "Returns geometry of informal regions that are not administrative divisions. "
                "E.g.: Serra Gaúcha, Pantanal, Litoral Norte, Vale do Taquari, Amazônia Legal."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Region name"},
                },
                "required": ["nome"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search geospatial products in the catalog. Main search tool. "
                "Requires geometry_ref from another tool. "
                "Types: carta_topografica, ortoimagem, mds, mdt, imagem_drone, "
                "imagem_satelite, modelo_3d, nuvem_pontos. Use '*' for all types."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "description": "Product type or '*' for all"},
                    "geometry_ref": {"type": "string", "description": "Geometry reference from another tool"},
                    "escala": {"type": "integer", "description": "Scale denominator. E.g. 25000 for 1:25,000"},
                    "data_inicio": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "data_fim": {"type": "string", "description": "End date YYYY-MM-DD"},
                },
                "required": ["geometry_ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buffer",
            "description": (
                "Creates a buffer zone (polygon) around any geometry. Returns geometry_ref. "
                "Reference radii: 500m narrow corridor, 5000m local area, "
                "20000m regional strip, 150000m legal border strip."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string"},
                    "raio_metros": {"type": "number", "description": "Buffer radius in meters"},
                },
                "required": ["geometry_ref", "raio_metros"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "intersect",
            "description": "Intersection of two geometries. Returns geometry_ref and area_km2.",
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string"},
                    "geometry_ref_b": {"type": "string"},
                },
                "required": ["geometry_ref_a", "geometry_ref_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_route",
            "description": (
                "Road route between two points. Accepts geometry_ref from geocode or other tools. "
                "Returns distance_km, duration_min, geometry_ref (LineString). "
                "Use with buffer to create a search corridor along the road."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_ref": {"type": "string", "description": "geometry_ref of origin point (from geocode)"},
                    "dest_ref": {"type": "string", "description": "geometry_ref of destination point (from geocode)"},
                },
                "required": ["origin_ref", "dest_ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hydrography",
            "description": "Search rivers, lakes, basins by name. Returns geometry_ref.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Waterbody name"},
                    "tipo": {"type": "string", "description": "rio, lago, lagoa, bacia (optional)"},
                    "uf": {"type": "string", "description": "Filter by state (optional)"},
                },
                "required": ["nome"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_border",
            "description": (
                "International border of Brazil with a neighbor country (LineString). "
                "Can filter by proximity to a point."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {"type": "string", "description": "Neighbor country name"},
                    "proximidade_ref": {"type": "string", "description": "geometry_ref of point to filter segment"},
                    "raio_m": {"type": "number", "description": "Radius in meters for clipping"},
                },
                "required": ["pais"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_features",
            "description": (
                "Search geographic features within an area. Returns list with geometry_ref per feature. "
                "Transport: ponte, tunel, estacao_ferroviaria, travessia_balsa. "
                "Vertical obstacles: torre_comunicacao, aerogerador, linha_transmissao, chamine_industrial. "
                "Aviation: aeroporto, heliporto, campo_pouso. "
                "Social: hospital, escola, posto_combustivel. "
                "Water: barragem, reservatorio, estacao_tratamento_agua. "
                "Territorial: terra_indigena, edificacao_destaque. "
                "Military: area_treinamento."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "description": "Feature type"},
                    "geometry_ref": {"type": "string", "description": "Search area geometry_ref"},
                },
                "required": ["tipo", "geometry_ref"],
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
                "Inf=Infantaria, Mec=Mecanizada, Eng=Engenharia. Returns geometry_ref."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_ou_sigla": {"type": "string"},
                    "cidade": {"type": "string", "description": "City for disambiguation (optional)"},
                },
                "required": ["nome_ou_sigla"],
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # SPATIAL COMPUTATION TOOLS
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "compute_distance",
            "description": (
                "Computes the straight-line (geodesic) distance between two geometries in km. "
                "Use when the user asks 'how far is X from Y' in straight-line terms."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string", "description": "First geometry reference"},
                    "geometry_ref_b": {"type": "string", "description": "Second geometry reference"},
                },
                "required": ["geometry_ref_a", "geometry_ref_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_area",
            "description": (
                "Computes the area of a polygon geometry in km². "
                "Use for 'what is the area of municipality X' or 'how big is the buffer zone'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "Polygon geometry reference"},
                },
                "required": ["geometry_ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_length",
            "description": (
                "Computes the length of a line geometry (route, river, border) in km. "
                "Use for 'how long is the route', 'what is the length of the river'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "LineString geometry reference"},
                },
                "required": ["geometry_ref"],
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # FEATURE ANALYSIS TOOLS
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "find_nearest",
            "description": (
                "Finds the nearest feature(s) of a given type from a reference point. "
                "Returns the N nearest features with distance_km to each. "
                "Use for 'closest hospital', 'nearest airport', 'nearest bridge'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "description": "Feature type to search for"},
                    "geometry_ref": {"type": "string", "description": "Reference point/area geometry_ref"},
                    "limit": {"type": "integer", "description": "Max results (default 3)"},
                },
                "required": ["tipo", "geometry_ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "features_along_route",
            "description": (
                "Lists features of a given type along a route or linear geometry. "
                "Applies an implicit buffer (default 500m) and returns features "
                "ordered by position along the route. "
                "Use for 'bridges along the route', 'gas stations on the highway'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "description": "Feature type (e.g. ponte, hospital, posto_combustivel)"},
                    "geometry_ref": {"type": "string", "description": "LineString geometry_ref (from compute_route or search_road)"},
                    "buffer_metros": {"type": "number", "description": "Corridor width in meters (default 500)"},
                },
                "required": ["tipo", "geometry_ref"],
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # SPATIAL PREDICATE & LOOKUP TOOLS
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "check_intersection",
            "description": (
                "Checks whether two geometries intersect (boolean). "
                "Returns intersects=true/false. "
                "Use for 'does route X pass through region Y', "
                "'does the river cross the municipality'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string"},
                    "geometry_ref_b": {"type": "string"},
                },
                "required": ["geometry_ref_a", "geometry_ref_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_road",
            "description": (
                "Search for a road or highway by its identifier. "
                "Returns geometry_ref (LineString) and extensao_km. "
                "Accepts BR/state codes: BR-101, BR-116, BR-290, RS-040."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "identificador": {"type": "string", "description": "Road identifier (e.g. 'BR-116', 'RS-040')"},
                    "uf": {"type": "string", "description": "State to filter segment (optional)"},
                },
                "required": ["identificador"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_municipalities_in",
            "description": (
                "Lists all municipalities that intersect a given geometry. "
                "Use for 'which municipalities does the route pass through', "
                "'what cities are within 50km of the base'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "Area or line geometry_ref"},
                },
                "required": ["geometry_ref"],
            },
        },
    },
]
