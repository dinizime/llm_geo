"""Definições de tools (JSON schema) enviadas ao LLM."""

# ── Conjuntos fechados usados como enums ─────────────────────
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
    # 1. BUSCAS GEOGRÁFICAS — resolver nomes/coordenadas em geometry_ref
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "geocode",
            "description": (
                "Resolve um nome de lugar, endereço ou POI em coordenadas e geometry_ref. "
                "Use quando o usuário menciona um lugar específico (cidade, ponto de interesse). "
                "NÃO use para municípios — use search_municipality. "
                "NÃO use quando o usuário fornece lat/lon — use create_point."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {
                        "type": "string",
                        "description": "Nome do lugar. Inclua o estado quando possível. Ex: 'Usina de Itaipu', 'Alecrim, RS'",
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
                "Cria uma geometria de ponto a partir de coordenadas lat/lon. Retorna geometry_ref. "
                "Use APENAS quando o usuário fornece coordenadas numéricas explícitas. "
                "NÃO use quando o usuário dá um nome de lugar — use geocode."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude (ex: -29.78)"},
                    "lon": {"type": "number", "description": "Longitude (ex: -55.79)"},
                    "label": {"type": "string", "description": "Rótulo opcional para o ponto"},
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
                "Determina em qual município uma coordenada se encontra. "
                "Retorna municipio, uf, estado. "
                "Use quando você tem coordenadas e precisa saber o nome do município."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude"},
                    "lon": {"type": "number", "description": "Longitude"},
                    "geometry_ref": {"type": "string", "description": "geometry_ref de ponto (alternativa a lat/lon)"},
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
                "Retorna o polígono, população, área e código IBGE de um município brasileiro. "
                "Use para qualquer pergunta sobre um município específico (área, produtos, feições). "
                "Se o nome for ambíguo (ex: 'Santa Cruz'), retorna lista de candidatos com uf — "
                "escolha o mais provável e chame novamente com uf para obter o geometry_ref."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome do município (ex: 'Alegrete')"},
                    "uf": {"type": "string", "description": "Sigla do estado para desambiguação (ex: 'RS')"},
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
            "description": "Retorna o polígono e área de um estado brasileiro. Use para consultas em nível estadual.",
            "parameters": {
                "type": "object",
                "properties": {
                    "uf": {"type": "string", "description": "Sigla do estado (ex: 'RS', 'SP')"},
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
                "Retorna a geometria de regiões informais/geográficas que NÃO são divisões administrativas. "
                "Exemplos: Serra Gaúcha, Pantanal, Litoral Norte, Vale do Taquari, Amazônia Legal. "
                "NÃO use para municípios ou estados — use search_municipality ou search_state."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome da região"},
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
                "Busca rios, lagos, lagoas ou bacias por nome. Retorna geometry_ref (LineString ou Polygon) e length_km. "
                "Use para qualquer pergunta envolvendo corpos d'água."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome do corpo d'água (ex: 'Rio Uruguai')"},
                    "tipo": {
                        "type": "string",
                        "enum": ["rio", "lago", "lagoa", "bacia"],
                        "description": "Tipo de corpo d'água (opcional)",
                    },
                    "uf": {"type": "string", "description": "Filtrar por estado (opcional)"},
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
                "Retorna a fronteira internacional do Brasil com um país vizinho (LineString) e length_km. "
                "Use para perguntas sobre fronteiras, regiões fronteiriças ou faixa de fronteira."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {"type": "string", "description": "Nome do país vizinho (ex: 'Argentina', 'Uruguai')"},
                    "proximidade_ref": {"type": "string", "description": "geometry_ref de ponto para filtrar trecho próximo"},
                    "raio_m": {"type": "number", "description": "Raio em metros para recorte próximo ao ponto"},
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
                "Busca uma rodovia pelo código oficial. Retorna geometry_ref (LineString) e extensao_km. "
                "Use para perguntas sobre rodovias. Aceita códigos BR ou estaduais: BR-101, BR-116, BR-290, RS-040."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "identificador": {"type": "string", "description": "Código da rodovia (ex: 'BR-116', 'RS-040')"},
                    "uf": {"type": "string", "description": "Estado para filtrar trecho (opcional)"},
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
                "Busca instalações militares por nome, sigla ou variante. "
                "Entende abreviações: Bda=Brigada, B=Batalhão, Cia=Companhia, "
                "Inf=Infantaria, Mec=Mecanizada, Eng=Engenharia. "
                "Retorna nome_completo, sigla, cidade, uf, geometry_ref."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_ou_sigla": {"type": "string", "description": "Nome ou sigla (ex: '8ª Bda Inf Mec')"},
                    "cidade": {"type": "string", "description": "Cidade para desambiguação (opcional)"},
                },
                "required": ["nome_ou_sigla"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 2. BUSCA DE FEIÇÕES — encontrar feições geográficas em áreas
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "search_features",
            "description": (
                "Busca feições geográficas de um tipo específico DENTRO de uma área (polígono ou buffer). "
                "Retorna lista de feições com atributos e geometry_ref. "
                "Use para: 'quantas pontes em Alegrete', 'torres de comunicação no RS'. "
                "Para feições ao longo de rota/rodovia: primeiro use buffer na rota, depois search_features no buffer. "
                "NÃO use para 'mais próximo de X' — use find_nearest."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": FEATURE_TYPES,
                        "description": "Tipo de feição a buscar",
                    },
                    "geometry_ref": {
                        "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
                        "description": "geometry_ref da área de busca (string ou lista para busca em múltiplas áreas)",
                    },
                    "atributo": {
                        "type": "string",
                        "description": "Atributo para filtrar (ex: 'altura_m', 'comprimento_m', 'leitos', 'pista_m', 'capacidade_ton', 'potencia_mw')",
                    },
                    "operador": {
                        "type": "string",
                        "enum": FILTER_OPERATORS,
                        "description": "Operador de comparação para filtro de atributo",
                    },
                    "valor": {"description": "Valor para comparar (número para operadores escalares, lista para 'in')"},
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
                "Encontra as N feições mais próximas de um tipo a partir de um ponto de referência. "
                "Retorna feições ordenadas por distance_km. "
                "Use para: 'hospital mais próximo', 'aeroporto mais perto de X'. "
                "NÃO use para contar feições em uma área — use search_features."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": FEATURE_TYPES,
                        "description": "Tipo de feição a buscar",
                    },
                    "geometry_ref": {
                        "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
                        "description": "geometry_ref do ponto de referência (string ou lista para lote)",
                    },
                    "limit": {"type": "integer", "description": "Máximo de resultados por ponto (padrão 3)"},
                },
                "required": ["tipo", "geometry_ref"],
                "additionalProperties": False,
            },
        },
    },
    # ═══════════════════════════════════════════════════════════════
    # 3. OPERAÇÕES ESPACIAIS — buffer, interseção, rota, predicados
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "buffer",
            "description": (
                "Cria uma zona de buffer circular (polígono) ao redor de qualquer geometria. Retorna geometry_ref e area_km2. "
                "Use para criar áreas de busca ao redor de pontos, rotas ou fronteiras. "
                "Raios típicos: 10m (rota local), 5000m (local), 20000m (regional), 150000m (faixa de fronteira)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {
                        "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
                        "description": "Referência da geometria central (string ou lista para lote)",
                    },
                    "raio_metros": {"type": "number", "description": "Raio do buffer em metros"},
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
                "Calcula a interseção geométrica de duas geometrias. Retorna geometry_ref e area_km2. "
                "Use quando precisar da área de sobreposição entre duas regiões."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string", "description": "Primeira geometria"},
                    "geometry_ref_b": {"type": "string", "description": "Segunda geometria"},
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
                "Calcula uma rota rodoviária entre dois pontos. Retorna distance_km, duration_min, length_km, geometry_ref (LineString). "
                "Use para distância por estrada e tempo de viagem entre lugares. "
                "NÃO use para distância em linha reta — use compute_distance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_ref": {"type": "string", "description": "geometry_ref do ponto de origem"},
                    "dest_ref": {"type": "string", "description": "geometry_ref do ponto de destino"},
                },
                "required": ["origin_ref", "dest_ref"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_spatial_relation",
            "description": (
                "Verifica relações espaciais entre duas geometrias. Retorna três booleanos: "
                "intersects (qualquer sobreposição), a_contains_b (A contém totalmente B), b_contains_a (B contém totalmente A). "
                "Use para: 'a rota passa por X?', 'o rio cruza o município?', "
                "'ponto X está dentro de Y?', 'o estado contém essa região?'. "
                "NÃO use intersect (que calcula a geometria de sobreposição) — esta tool só retorna booleanos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string", "description": "Primeira geometria"},
                    "geometry_ref_b": {"type": "string", "description": "Segunda geometria"},
                },
                "required": ["geometry_ref_a", "geometry_ref_b"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 4. MEDIÇÕES — distância, área, comprimento
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "compute_distance",
            "description": (
                "Calcula a distância em linha reta (geodésica) entre duas geometrias em km. "
                "Use para 'qual a distância de X a Y' em linha reta. "
                "NÃO use para distância por estrada — use compute_route."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string", "description": "Referência da primeira geometria"},
                    "geometry_ref_b": {
                        "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
                        "description": "Referência da segunda geometria (string ou lista para distância a múltiplos pontos)",
                    },
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
                "Calcula a área de um polígono em km². "
                "Use para: 'área do município X', 'tamanho da zona de buffer'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {
                        "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
                        "description": "Referência da geometria do polígono (string ou lista para lote)",
                    },
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
                "Calcula o comprimento de uma geometria de linha (rota, rio, fronteira) em km. "
                "Use para: 'comprimento da rota', 'extensão do rio', 'tamanho da fronteira'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {
                        "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
                        "description": "Referência da geometria LineString (string ou lista para lote)",
                    },
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 5. CATÁLOGO DE PRODUTOS — buscar produtos geoespaciais
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Busca produtos geoespaciais no catálogo. Ferramenta principal de busca de produtos. "
                "Requer geometry_ref de uma tool anterior (search_municipality, buffer, etc.). "
                "Retorna produtos com escala, data_produto, articulacao, nome. "
                "Analise os resultados para encontrar 'melhor escala' ou 'mais recente'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "geometry_ref da área de busca"},
                    "tipo": {
                        "type": "string",
                        "description": "Tipo de produto, ou '*' para todos",
                        "enum": PRODUCT_TYPES + ["*"],
                    },
                    "escala": {"type": "integer", "description": "Filtro de denominador de escala (ex: 25000 para 1:25.000)"},
                    "data_inicio": {"type": "string", "description": "Filtro de data inicial AAAA-MM-DD"},
                    "data_fim": {"type": "string", "description": "Filtro de data final AAAA-MM-DD"},
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
                "Busca produtos geoespaciais pelo código de articulação da folha (MI ou INOM). "
                "Use quando o usuário fornece um código de articulação como 'SH-22-V-C-IV-1'. "
                "NÃO use para buscas geográficas — use search_products."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "codigo": {"type": "string", "description": "Código de articulação (ex: 'SH-22-V-C-IV-1')"},
                },
                "required": ["codigo"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 6. CONSULTAS ESPACIAIS — municípios, vizinhos
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "list_municipalities_in",
            "description": (
                "Lista todos os municípios que intersectam uma geometria. "
                "Use para: 'municípios ao longo da rota', 'cidades num raio de 50km'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "geometry_ref da área ou linha"},
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
                "Retorna os municípios que fazem divisa com um município. "
                "Use para: 'municípios vizinhos de Alegrete', 'quem faz divisa com Santa Maria'. "
                "Requer geometry_ref de um município (de search_municipality)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "geometry_ref do polígono do município"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 7. ELEVAÇÃO E TERRENO
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "get_elevation",
            "description": (
                "Retorna a elevação de um ponto (elevation_m) ou faixa de elevação de um polígono "
                "(min_elevation_m, max_elevation_m, avg_elevation_m). "
                "Use para: 'altitude de Alegrete', 'elevação na coordenada X'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "geometry_ref de Ponto ou Polígono"},
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
                "Retorna o perfil de elevação ao longo de uma LineString (rota, rodovia, rio). "
                "Amostra ~10 pontos. Retorna min_m, max_m, avg_m, max_slope_pct, "
                "total_ascent_m, total_descent_m, classification (plano/ondulado/montanhoso). "
                "Use para: 'perfil de elevação da rota', 'o terreno é montanhoso?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "geometry_ref de LineString (de compute_route, search_road ou search_hydrography)"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 8. OPERAÇÕES GEOMÉTRICAS AVANÇADAS
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "union",
            "description": (
                "Calcula a união geométrica de duas ou mais geometrias. Retorna geometry_ref + area_km2 ou length_km. "
                "Use para: 'área total de Alegrete + Uruguaiana', 'zona que cobre ambos os municípios'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "description": "Lista de geometry_refs para unir (mínimo 2)",
                    },
                },
                "required": ["geometry_refs"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "difference",
            "description": (
                "Calcula a diferença geométrica: A menos B. Retorna geometry_ref + area_km2 ou length_km. "
                "Use para: 'área do RS fora da faixa de fronteira', 'município excluindo terras indígenas'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string", "description": "Geometria base (da qual será subtraído)"},
                    "geometry_ref_b": {"type": "string", "description": "Geometria a subtrair"},
                },
                "required": ["geometry_ref_a", "geometry_ref_b"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clip",
            "description": (
                "Recorta a geometria A pelos limites de B. Retorna a parte de A que está dentro de B. "
                "Preserva o tipo: linha recortada por polígono retorna linha com length_km. "
                "Use para: 'trecho da BR-290 dentro de Alegrete', 'parte do rio dentro do estado'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref_a": {"type": "string", "description": "Geometria a recortar (linha ou polígono)"},
                    "geometry_ref_b": {"type": "string", "description": "Geometria de recorte (polígono)"},
                },
                "required": ["geometry_ref_a", "geometry_ref_b"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_centroid",
            "description": (
                "Calcula o centroide (ponto central) de uma geometria. Retorna lat, lon, geometry_ref (Point). "
                "Use para: 'centro do município', 'ponto central da rota' — cria um Point reutilizável."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "geometry_ref de qualquer geometria"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_route_waypoints",
            "description": (
                "Calcula uma rota rodoviária passando por múltiplos pontos na ordem fornecida. "
                "Retorna distance_km, duration_min, length_km, geometry_ref (LineString). "
                "Use para: 'rota de A a C passando por B', 'roteiro visitando 5 cidades'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "description": "Lista de geometry_refs dos waypoints na ordem de visita (mínimo 2)",
                    },
                },
                "required": ["geometry_refs"],
                "additionalProperties": False,
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # 9. CLIMA
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Retorna as condições meteorológicas atuais de um local. "
                "Dados: temperatura, sensação térmica, umidade, precipitação, vento, condições. "
                "Use para: 'como está o tempo em Porto Alegre?', 'condições climáticas para operação'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry_ref": {"type": "string", "description": "geometry_ref de ponto ou polígono (usa centroide)"},
                },
                "required": ["geometry_ref"],
                "additionalProperties": False,
            },
        },
    },
]
