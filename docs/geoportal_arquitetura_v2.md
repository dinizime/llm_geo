# Geoportal - Arquitetura de Implementação (v3)

> Atualizado com base no estado da arte de orquestração de agentes LLM em 2026.
> Referências: pesquisa Anthropic "Building Effective Agents", LangChain State of AI Agents,
> paper "GeoJSON Agents" (Taylor & Francis, 2026), GeoBenchX, GeoSQL-Eval,
> Felt/Mundi (PostGIS Day 2025), Mapbox GeoAI Forecast 2026.
> Benchmarks: BFCL v4, τ²-Bench, HumanMCP, MCPVerse, WildToolBench, TELLER-Bench.
> Tool selection: Anthropic Tool Search Tool, OpenAI Deferred Loading,
> ToolLLM (ICLR 2024), Gorilla (NeurIPS 2024), FunctionGemma, ProTIP, Tool2Vec.

## 1. Filosofia: O While-Loop Venceu

O consenso da indústria em 2026 é claro: **agentes de produção são arquiteturalmente simples**.
O padrão que sobreviveu ao hype é um loop `while` com tool calling nativo da API do modelo.
Sem framework pesado, sem grafo de estados, sem multi-agente.

A Anthropic publicou o guia mais influente do setor e a conclusão é direta:
"As implementações mais bem-sucedidas usam padrões simples e composáveis,
não frameworks complexos."

Claude Code (o primeiro agente de código convincente segundo Andrej Karpathy),
o HuggingFace Tiny Agents (~70 linhas), e o agente da O'Reilly (131 linhas)
são todos variações do mesmo padrão:

```
while True:
    resposta = llm.chat(mensagens, tools=definições)
    if não tem tool_calls:
        return resposta.conteúdo  # fim
    for call in tool_calls:
        resultado = executar_tool(call)
        mensagens.append(resultado)
```

Isso resolve ~80% dos casos de uso em produção.
Para o nosso geoportal, onde todas as tools são locais (PostGIS na mesma máquina),
esse padrão é ideal. Não precisamos de MCP (que é para integrar serviços externos),
nem de frameworks de orquestração como LangGraph ou CrewAI.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND                                   │
│   Caixa de busca (texto livre)          WebSocket (progresso)       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SERVIDOR (FastAPI)                               │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    AGENT LOOP                                 │  │
│  │                                                               │  │
│  │  while tool_calls:                                            │  │
│  │      response = llm.chat(messages, tools)                     │  │
│  │      for call in response.tool_calls:                         │  │
│  │          result = execute(call)     ◄──── GEOMETRY STORE      │  │
│  │          messages.append(result)          (refs, não GeoJSON)  │  │
│  │                                                               │  │
│  └──────────────┬────────────────────────────────────────────────┘  │
│                 │                                                    │
│                 ▼                                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    TOOL FUNCTIONS (Python async)               │  │
│  │                                                               │  │
│  │  Todas locais. Sem APIs externas, sem MCP.                    │  │
│  │                                                               │  │
│  │  PostGIS ─── search_products, search_features, buffer,        │  │
│  │              intersect, search_municipality, search_state,     │  │
│  │              search_hydrography, search_border, ...            │  │
│  │                                                               │  │
│  │  OSRM local ── compute_route                                  │  │
│  │                                                               │  │
│  │  In-memory ── rank_by_scale, rank_by_date,                    │  │
│  │               autocomplete_placename, explain_product_type     │  │
│  │                                                               │  │
│  └──────────────┬────────────────────────────────────────────────┘  │
│                 │                                                    │
│                 ▼                                                    │
│  ┌──────────────────────────┐                                       │
│  │       PostgreSQL/PostGIS │                                       │
│  │       (mesma máquina)    │                                       │
│  └──────────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Context Engineering > Prompt Engineering

A mudança de paradigma mais importante de 2025-2026 não foi em frameworks,
foi na compreensão de que **o LLM não experimenta a sua arquitetura, ele vê
uma única janela de contexto**. A disciplina que emergiu se chama "Context Engineering":
gerenciar o que entra na janela de contexto do modelo.

Para o geoportal, isso tem implicações concretas:

### 2.1 Geometry Store: o LLM nunca vê GeoJSON

O erro mais caro num agente geoespacial é passar GeoJSON bruto no contexto.
O polígono de um município pode ter 5.000+ vértices = milhares de tokens desperdiçados.
O LLM não precisa ver coordenadas, ele precisa de referências.

```python
# context/geometry_store.py
from uuid import uuid4

class GeometryStore:
    """
    Armazena geometrias intermediárias fora do contexto do LLM.
    O LLM trabalha com referências leves (ex: "geom_a3f2b1c0").
    A tool resolve a referência internamente.
    """

    def __init__(self):
        self._store: dict[str, dict] = {}

    def put(self, geojson: dict, label: str = "") -> str:
        """Armazena geometria e retorna ref."""
        ref = f"geom_{uuid4().hex[:8]}"
        self._store[ref] = geojson
        return ref

    def get(self, ref: str) -> dict:
        """Recupera GeoJSON pela ref."""
        if ref not in self._store:
            raise KeyError(f"Geometria '{ref}' não encontrada no store")
        return self._store[ref]

    def summary(self, ref: str) -> dict:
        """Retorna metadados leves para o LLM (sem coordenadas)."""
        geojson = self._store[ref]
        geom_type = geojson.get("type", "unknown")
        # Contar vértices sem expor coordenadas
        coords = str(geojson.get("coordinates", []))
        n_points = coords.count(",") // 2
        return {
            "geometry_ref": ref,
            "type": geom_type,
            "approx_vertices": n_points,
        }

# Instância global por sessão
geometry_store = GeometryStore()
```

Toda tool que produz geometria devolve `geometry_ref` em vez do GeoJSON.
Toda tool que consome geometria aceita `geometry_ref` e resolve internamente:

```python
# Exemplo: buffer que recebe ref e devolve ref
async def buffer(geometry_ref: str, raio_metros: float) -> dict:
    geojson = geometry_store.get(geometry_ref)
    geojson_str = json.dumps(geojson)

    query = """
        SELECT ST_AsGeoJSON(
            ST_Transform(
                ST_Buffer(ST_Transform(
                    ST_SetSRID(ST_GeomFromGeoJSON($1), 4326), 3857
                ), $2),
            4326)
        ) as geojson
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, geojson_str, raio_metros)

    result_geojson = json.loads(row["geojson"])
    ref = geometry_store.put(result_geojson, label=f"buffer_{raio_metros}m")

    return {
        "geometry_ref": ref,
        "type": "Polygon",
        "description": f"Buffer de {raio_metros}m aplicado",
    }
```

O que o LLM vê no contexto:
```json
{"geometry_ref": "geom_a3f2b1c0", "type": "Polygon", "description": "Buffer de 500m aplicado"}
```

O que o LLM **não** vê: 5.000 linhas de coordenadas.

### 2.2 Representação Otimizada dos Resultados

Outro princípio do context engineering: devolver só o que o LLM precisa para decidir.

```python
def summarize_products_for_llm(products: list, max_items: int = 10) -> dict:
    """
    Reduz a lista de produtos para o contexto do LLM.
    Remove campos que o LLM não precisa (geometry, urls longas).
    """
    summary = []
    for p in products[:max_items]:
        summary.append({
            "id": p["id"],
            "tipo": p["tipo"],
            "escala": p.get("escala_display"),
            "data": p.get("data_produto"),
            "articulacao": p.get("articulacao"),
            "nome": p.get("nome"),
            "resolucao_m": p.get("resolucao_m"),
            # NÃO inclui: geometry, url_download, url_preview
        })

    return {
        "total": len(products),
        "showing": len(summary),
        "products": summary,
        "has_more": len(products) > max_items,
    }
```

### 2.3 Instruções Just-in-Time

Em vez de colocar tudo no system prompt, injetar instruções relevantes
conforme o contexto evolui:

```python
def build_system_prompt(user_message: str, detected_entities: dict) -> str:
    """
    Monta system prompt dinâmico baseado no que foi detectado na pergunta.
    Evita carregar o contexto com instruções sobre fronteiras se a pergunta
    é sobre um município simples.
    """
    base = SYSTEM_PROMPT_BASE  # regras gerais (curto)

    # Injeta instruções específicas conforme necessidade
    if detected_entities.get("has_abbreviation"):
        base += MILITARY_ABBREVIATIONS_GUIDE
    if detected_entities.get("has_ambiguous_placename"):
        base += DISAMBIGUATION_INSTRUCTIONS
    if detected_entities.get("has_route"):
        base += ROUTE_PLANNING_INSTRUCTIONS
    if detected_entities.get("has_temporal_filter"):
        base += TEMPORAL_FILTER_INSTRUCTIONS

    return base
```

---

## 3. Banco PostGIS: Estrutura

Sem mudanças em relação à v1. O schema funciona bem.
Reproduzido aqui por completude.

```sql
-- Produtos geoespaciais (catálogo principal)
CREATE TABLE produtos (
    id            SERIAL PRIMARY KEY,
    tipo          VARCHAR(50) NOT NULL,
    escala        INTEGER,
    resolucao_m   FLOAT,
    data_produto  DATE,
    fonte         VARCHAR(100),
    articulacao   VARCHAR(50),
    nome          VARCHAR(200),
    url_download  TEXT,
    url_preview   TEXT,
    geometry      GEOMETRY(Polygon, 4326) NOT NULL
);

CREATE INDEX idx_produtos_geom ON produtos USING GIST(geometry);
CREATE INDEX idx_produtos_tipo ON produtos(tipo);
CREATE INDEX idx_produtos_escala ON produtos(escala);
CREATE INDEX idx_produtos_data ON produtos(data_produto);

-- Municípios (IBGE)
CREATE TABLE municipios (
    id            SERIAL PRIMARY KEY,
    codigo_ibge   VARCHAR(7),
    nome          VARCHAR(200),
    uf            VARCHAR(2),
    populacao     INTEGER,
    geometry      GEOMETRY(MultiPolygon, 4326) NOT NULL
);

-- Estados
CREATE TABLE estados (
    id SERIAL PRIMARY KEY,
    uf VARCHAR(2), nome VARCHAR(100),
    geometry GEOMETRY(MultiPolygon, 4326) NOT NULL
);

-- Regiões informais (curadoria manual, ~50-100 registros)
CREATE TABLE regioes_informais (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200), aliases TEXT[],
    geometry GEOMETRY(MultiPolygon, 4326) NOT NULL
);

-- Fronteiras internacionais
CREATE TABLE fronteiras (
    id SERIAL PRIMARY KEY,
    pais VARCHAR(100),
    geometry GEOMETRY(MultiLineString, 4326) NOT NULL
);

-- Feições geográficas
CREATE TABLE feicoes (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50), nome VARCHAR(200),
    geometry GEOMETRY(Geometry, 4326) NOT NULL
);

-- Hidrografia
CREATE TABLE hidrografia (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200), tipo VARCHAR(50),
    geometry GEOMETRY(Geometry, 4326) NOT NULL
);

-- Organizações Militares
CREATE TABLE organizacoes_militares (
    id SERIAL PRIMARY KEY,
    nome_completo VARCHAR(300), sigla VARCHAR(50),
    aliases TEXT[], tipo VARCHAR(50),
    cidade VARCHAR(200), uf VARCHAR(2),
    geometry GEOMETRY(Point, 4326) NOT NULL
);

-- Unidades de Conservação
CREATE TABLE unidades_conservacao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(300), categoria VARCHAR(100),
    geometry GEOMETRY(MultiPolygon, 4326) NOT NULL
);

-- Terras Indígenas
CREATE TABLE terras_indigenas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(300),
    geometry GEOMETRY(MultiPolygon, 4326) NOT NULL
);

-- Infraestrutura linear
CREATE TABLE infraestrutura_linear (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50), identificador VARCHAR(50), nome VARCHAR(200),
    geometry GEOMETRY(MultiLineString, 4326) NOT NULL
);

-- Linha de costa
CREATE TABLE linha_costa (
    id SERIAL PRIMARY KEY,
    uf VARCHAR(2),
    geometry GEOMETRY(MultiLineString, 4326) NOT NULL
);
```

Extensões necessárias:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- para similarity() nas buscas fuzzy
CREATE EXTENSION IF NOT EXISTS unaccent;   -- para normalização de acentos
```

---

## 4. Tool Functions: Todas Locais

Cada tool é uma função async Python que:
1. Recebe parâmetros simples (strings, números, geometry_ref)
2. Resolve geometry_ref via GeometryStore (nunca recebe GeoJSON do LLM)
3. Faz query no PostGIS ou OSRM local
4. Devolve resultado resumido + geometry_ref para geometrias de saída

### 4.1 Padrão de uma Tool

```python
# tools/search_municipality.py

async def search_municipality(nome: str, uf: str = None) -> dict:
    """
    Retorna a geometria de um município.
    """
    query = """
        SELECT nome, uf, codigo_ibge, populacao,
               ST_AsGeoJSON(geometry) as geojson
        FROM municipios
        WHERE unaccent(lower(nome)) = unaccent(lower($1))
    """
    params = [nome]

    if uf:
        query += " AND uf = $2"
        params.append(uf.upper())

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    if not rows:
        return {"error": f"Município '{nome}' não encontrado"}

    if len(rows) > 1 and not uf:
        return {
            "ambiguous": True,
            "candidates": [
                {"nome": r["nome"], "uf": r["uf"], "populacao": r["populacao"]}
                for r in rows
            ]
        }

    row = rows[0]
    geojson = json.loads(row["geojson"])
    ref = geometry_store.put(geojson, label=f"municipio_{row['nome']}")

    return {
        "nome": row["nome"],
        "uf": row["uf"],
        "codigo_ibge": row["codigo_ibge"],
        "populacao": row["populacao"],
        "geometry_ref": ref,  # ref, nunca GeoJSON
    }
```

### 4.2 search_products (a tool principal)

```python
async def search_products(
    tipo: str = None,
    geometry_ref: str = None,
    escala: int = None,
    data_inicio: str = None,
    data_fim: str = None,
    fonte: str = None,
    limit: int = 50,
) -> dict:
    """Busca produtos no catálogo geoespacial."""

    conditions = []
    params = []
    idx = 1

    if tipo and tipo != "*":
        tipos = [t.strip() for t in tipo.split(",")]
        if len(tipos) == 1:
            conditions.append(f"tipo = ${idx}")
            params.append(tipos[0])
        else:
            ph = ", ".join(f"${idx + i}" for i in range(len(tipos)))
            conditions.append(f"tipo IN ({ph})")
            params.extend(tipos)
            idx += len(tipos) - 1
        idx += 1

    if geometry_ref:
        geojson = geometry_store.get(geometry_ref)
        geojson_str = json.dumps(geojson)
        conditions.append(
            f"ST_Intersects(geometry, ST_SetSRID(ST_GeomFromGeoJSON(${idx}), 4326))"
        )
        params.append(geojson_str)
        idx += 1

    if escala:
        conditions.append(f"escala = ${idx}")
        params.append(escala)
        idx += 1

    if data_inicio:
        conditions.append(f"data_produto >= ${idx}::date")
        params.append(data_inicio)
        idx += 1

    if data_fim:
        conditions.append(f"data_produto <= ${idx}::date")
        params.append(data_fim)
        idx += 1

    if fonte:
        conditions.append(f"fonte = ${idx}")
        params.append(fonte)
        idx += 1

    where = " AND ".join(conditions) if conditions else "TRUE"

    query = f"""
        SELECT id, tipo, escala, resolucao_m, data_produto, articulacao,
               nome, fonte, url_download, url_preview
        FROM produtos
        WHERE {where}
        ORDER BY data_produto DESC NULLS LAST
        LIMIT ${idx}
    """
    params.append(limit)

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    products = []
    for r in rows:
        products.append({
            "id": r["id"],
            "tipo": r["tipo"],
            "escala_display": f"1:{r['escala']:,}".replace(",", ".") if r["escala"] else None,
            "data_produto": r["data_produto"].isoformat() if r["data_produto"] else None,
            "articulacao": r["articulacao"],
            "nome": r["nome"],
            "resolucao_m": r["resolucao_m"],
            # NÃO retorna geometry nem urls para o LLM
            # URLs são resolvidas na resposta final pelo servidor
        })

    return {"total": len(products), "products": products}
```

### 4.3 Outras tools (assinatura resumida)

Todas seguem o mesmo padrão: recebem geometry_ref, devolvem geometry_ref.

```python
async def geocode(place_name: str) -> dict:
    """Resolve topônimo em ponto. Devolve lat, lon, display_name, geometry_ref."""

async def search_state(uf: str) -> dict:
    """Retorna nome, uf, geometry_ref do estado."""

async def search_named_region(nome: str) -> dict:
    """Busca região informal (Serra Gaúcha, Pantanal...). Devolve geometry_ref."""

async def search_border(pais: str, proximidade_ref: str = None, raio_m: float = None) -> dict:
    """Retorna fronteira com país vizinho. Devolve geometry_ref (LineString)."""

async def search_coastline(uf: str) -> dict:
    """Retorna linha de costa da UF. Devolve geometry_ref."""

async def buffer(geometry_ref: str, raio_metros: float) -> dict:
    """Buffer ao redor de qualquer geometria. Devolve geometry_ref."""

async def intersect(geometry_ref_a: str, geometry_ref_b: str) -> dict:
    """Interseção de duas geometrias. Devolve geometry_ref + area_km2."""

async def compute_route(origin_lat: float, origin_lon: float,
                         dest_lat: float, dest_lon: float) -> dict:
    """Rota rodoviária via OSRM local. Devolve distance_km, duration_min, geometry_ref."""

async def search_features(tipo: str, geometry_ref: str) -> dict:
    """Busca feições (pontes, barragens, aeroportos) na área. Cada feição tem geometry_ref."""

async def search_hydrography(nome: str, tipo: str = None, uf: str = None) -> dict:
    """Busca rio, lago, bacia por nome. Devolve geometry_ref."""

async def search_military_installation(nome_ou_sigla: str, cidade: str = None) -> dict:
    """Busca OM por nome/sigla fuzzy (pg_trgm). Devolve geometry_ref."""

async def search_conservation_unit(nome: str) -> dict:
    """Busca UC por nome. Devolve geometry_ref."""

async def search_indigenous_land(nome: str) -> dict:
    """Busca TI por nome. Devolve geometry_ref."""

async def search_infrastructure(tipo: str, identificador: str) -> dict:
    """Busca rodovia/ferrovia. Devolve geometry_ref."""

async def rank_by_scale(products: list, order: str = "best_first") -> dict:
    """Ordena produtos por escala. In-memory, sem query."""

async def rank_by_date(products: list, order: str = "newest_first") -> dict:
    """Ordena produtos por data. In-memory, sem query."""

async def autocomplete_placename(fragmento: str, limit: int = 8) -> dict:
    """Sugere municípios a partir de fragmento. Ordenado por população."""

async def explain_product_type(tipo: str, escala: int = None) -> dict:
    """Retorna descrição de um tipo de produto. In-memory, sem query."""
```

---

## 5. Tool Registry (JSON Schema para o LLM)

O registro de tools é o contrato entre o LLM e as funções Python.
Cada tool tem name, description e parameters.

Ponto crítico aprendido com o GeoBenchX:
**tools mais específicas e estreitas melhoram a acurácia do agente**.
Melhor ter 18 tools focadas do que 5 genéricas.

```python
TOOLS = [
    {
        "name": "geocode",
        "description": (
            "Resolve topônimo, endereço ou POI em coordenadas. "
            "Retorna lat, lon, display_name e geometry_ref (ponto). "
            "Use quando o usuário menciona um lugar por nome que não é um município."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "place_name": {
                    "type": "string",
                    "description": "Nome do lugar. Inclua UF quando possível. Ex: 'Usina de Itaipu', 'Alecrim, RS'"
                }
            },
            "required": ["place_name"]
        }
    },
    {
        "name": "search_municipality",
        "description": (
            "Retorna o polígono de um município brasileiro (geometry_ref). "
            "Use quando precisar delimitar a área de um município para buscar produtos dentro dele. "
            "Se o nome for ambíguo (ex: 'Santa Cruz'), retorna lista de candidatos para desambiguação."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nome": {"type": "string", "description": "Nome do município"},
                "uf": {"type": "string", "description": "Sigla da UF (2 letras). Ajuda a desambiguar."}
            },
            "required": ["nome"]
        }
    },
    {
        "name": "search_products",
        "description": (
            "Busca produtos geoespaciais no catálogo. É a tool principal de busca. "
            "Requer geometry_ref (obtido de outras tools). "
            "Tipos: carta_topografica, ortoimagem, mds, mdt, imagem_drone, "
            "imagem_satelite, modelo_3d, nuvem_pontos. Use '*' para todos."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string"},
                "geometry_ref": {"type": "string", "description": "Referência de geometria obtida de outra tool"},
                "escala": {"type": "integer", "description": "Denominador. Ex: 25000 para 1:25.000"},
                "data_inicio": {"type": "string", "description": "YYYY-MM-DD"},
                "data_fim": {"type": "string", "description": "YYYY-MM-DD"},
                "fonte": {"type": "string", "description": "lidar, radar, fotogrametrico, satelite"}
            },
            "required": ["geometry_ref"]
        }
    },
    {
        "name": "buffer",
        "description": (
            "Cria zona de influência (polígono) ao redor de qualquer geometria. "
            "Retorna geometry_ref. Referências de raio: 500m corredor estreito, "
            "5000m área local, 20000m faixa regional, 150000m faixa de fronteira legal."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "geometry_ref": {"type": "string"},
                "raio_metros": {"type": "number"}
            },
            "required": ["geometry_ref", "raio_metros"]
        }
    },
    {
        "name": "intersect",
        "description": "Interseção entre duas geometrias. Retorna geometry_ref + area_km2.",
        "parameters": {
            "type": "object",
            "properties": {
                "geometry_ref_a": {"type": "string"},
                "geometry_ref_b": {"type": "string"}
            },
            "required": ["geometry_ref_a", "geometry_ref_b"]
        }
    },
    {
        "name": "compute_route",
        "description": (
            "Rota rodoviária entre dois pontos (OSRM local). "
            "Retorna distance_km, duration_min, geometry_ref (LineString). "
            "Use com buffer para criar corredor de busca ao longo de estrada."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "origin_lat": {"type": "number"}, "origin_lon": {"type": "number"},
                "dest_lat": {"type": "number"}, "dest_lon": {"type": "number"}
            },
            "required": ["origin_lat", "origin_lon", "dest_lat", "dest_lon"]
        }
    },
    {
        "name": "search_features",
        "description": (
            "Busca feições geográficas dentro de uma área. "
            "Tipos: ponte, barragem, aeroporto, porto, reservatorio. "
            "Cada feição retornada tem seu próprio geometry_ref."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string"},
                "geometry_ref": {"type": "string"}
            },
            "required": ["tipo", "geometry_ref"]
        }
    },
    {
        "name": "search_hydrography",
        "description": "Busca rios, lagos, bacias por nome. Retorna geometry_ref.",
        "parameters": {
            "type": "object",
            "properties": {
                "nome": {"type": "string"},
                "tipo": {"type": "string", "description": "rio, lago, lagoa, bacia (opcional)"},
                "uf": {"type": "string", "description": "Filtrar por UF (opcional)"}
            },
            "required": ["nome"]
        }
    },
    {
        "name": "search_military_installation",
        "description": (
            "Busca OM por nome, sigla ou variação. Entende abreviações: "
            "Bda=Brigada, B=Batalhão, Cia=Companhia, Inf=Infantaria, "
            "Mec=Mecanizada, Eng=Engenharia, Art=Artilharia. Retorna geometry_ref."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nome_ou_sigla": {"type": "string"},
                "cidade": {"type": "string", "description": "Para desambiguar (opcional)"}
            },
            "required": ["nome_ou_sigla"]
        }
    },
    {
        "name": "search_named_region",
        "description": (
            "Retorna geometria de regiões informais que não são divisões administrativas. "
            "Ex: Serra Gaúcha, Pantanal, Litoral Norte, Vale do Taquari, Amazônia Legal."
        ),
        "parameters": {
            "type": "object",
            "properties": {"nome": {"type": "string"}},
            "required": ["nome"]
        }
    },
    {
        "name": "search_state",
        "description": "Retorna polígono de um estado pela sigla. Retorna geometry_ref.",
        "parameters": {
            "type": "object",
            "properties": {"uf": {"type": "string"}},
            "required": ["uf"]
        }
    },
    {
        "name": "search_border",
        "description": (
            "Fronteira internacional do Brasil com país vizinho (LineString). "
            "Pode filtrar trecho por proximidade a um ponto."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pais": {"type": "string"},
                "proximidade_ref": {"type": "string", "description": "geometry_ref de ponto para filtrar trecho"},
                "raio_m": {"type": "number", "description": "Raio em metros para recorte"}
            },
            "required": ["pais"]
        }
    },
    {
        "name": "search_coastline",
        "description": "Linha de costa de uma UF. Retorna geometry_ref.",
        "parameters": {
            "type": "object",
            "properties": {"uf": {"type": "string"}},
            "required": ["uf"]
        }
    },
    {
        "name": "search_conservation_unit",
        "description": "Busca UC (Parque Nacional, APA, REBIO...) por nome. Retorna geometry_ref.",
        "parameters": {
            "type": "object",
            "properties": {"nome": {"type": "string"}},
            "required": ["nome"]
        }
    },
    {
        "name": "search_indigenous_land",
        "description": "Busca Terra Indígena por nome. Retorna geometry_ref.",
        "parameters": {
            "type": "object",
            "properties": {"nome": {"type": "string"}},
            "required": ["nome"]
        }
    },
    {
        "name": "search_infrastructure",
        "description": "Busca rodovia, ferrovia ou dutovia por código ou nome. Retorna geometry_ref (LineString).",
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string", "description": "rodovia, ferrovia, dutovia"},
                "identificador": {"type": "string", "description": "Ex: 'BR-116', 'EF Carajás'"}
            },
            "required": ["tipo", "identificador"]
        }
    },
    {
        "name": "rank_by_scale",
        "description": "Ordena lista de produtos por escala (melhor = mais detalhada primeiro).",
        "parameters": {
            "type": "object",
            "properties": {
                "products": {"type": "array"},
                "order": {"type": "string", "enum": ["best_first", "worst_first"]}
            },
            "required": ["products", "order"]
        }
    },
    {
        "name": "rank_by_date",
        "description": "Ordena lista de produtos por data.",
        "parameters": {
            "type": "object",
            "properties": {
                "products": {"type": "array"},
                "order": {"type": "string", "enum": ["newest_first", "oldest_first"]}
            },
            "required": ["products", "order"]
        }
    },
    {
        "name": "autocomplete_placename",
        "description": (
            "Sugere municípios a partir de fragmento de texto. "
            "Use quando nome é truncado ou ambíguo (ex: 'santa', 'são j'). "
            "Candidatos ordenados por população."
        ),
        "parameters": {
            "type": "object",
            "properties": {"fragmento": {"type": "string"}},
            "required": ["fragmento"]
        }
    },
    {
        "name": "explain_product_type",
        "description": (
            "Explica o que é um tipo de produto. Use para perguntas conceituais "
            "('diferença entre MDS e MDT?') ou desambiguação ('mapa' pode ser vários tipos)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string"},
                "escala": {"type": "integer", "description": "Escala para detalhar (opcional)"}
            },
            "required": ["tipo"]
        }
    },
]
```

---

## 5.1 Estratégia de Tool Loading: Tudo Upfront, Não Dinâmico

Uma pergunta natural: "se temos 19 tools, o LLM precisa ver todas de uma vez?
Não seria melhor buscar dinamicamente só as tools relevantes por query?"

A resposta, baseada em benchmarks e práticas de produção em 2026: **não, para 19 tools
carregue tudo upfront**. Mas a técnica de busca dinâmica é real e vale entender
para quando o sistema crescer.

### Por que carregar tudo funciona com 19 tools

Os números são claros sobre quando a degradação começa:

- Gemini 2.0 Flash: 98.4% com 10 tools, 88.2% com 100, 65% com 2.000
  (benchmark HumanMCP, 2025)
- Claude 3.5 Haiku: queda de apenas 9.2 pontos de 10 a 2.000 tools
- TaskBench (NeurIPS 2024): 96% com 1 tool, 25% com 8 tools em cadeias complexas
  (mas isso é acurácia de chaining, não de seleção)
- OpenAI documenta que <100 tools com ~20 args cada é "in-distribution" para o3/o4-mini

Nossas 19 tools com descrições otimizadas ocupam ~4.000 tokens:
- 2% de um contexto de 200K (GLM-4.7-Flash, Gemma 4)
- 0.4% de um contexto de 1M (Nemotron)
- Custo: ~$0.012 por request a $3/M tokens (prompt caching reduz 90%)

Operações espaciais têm interdependências que o LLM precisa ver.
Saber que `buffer` existe ajuda o modelo a entender quando usar `intersect`.
Agentes geoespaciais de sucesso (Mundi, LLM-Geo, GIS Copilot, Spatial-RAG)
usam todos all-tools-upfront.

### Técnicas de seleção dinâmica (para quando crescer)

Quando o catálogo de tools ultrapassar ~30, existem 3 abordagens de produção:

**A) Retrieval por embedding (RAG de tools)**

Embeda descrições de tools em vetor store e busque por similaridade semântica:

```python
# Preparação offline
from sentence_transformers import SentenceTransformer

model_embed = SentenceTransformer("all-MiniLM-L12-v2")

tool_embeddings = {}
for tool in TOOLS:
    text = f"{tool['name']}: {tool['description']}"
    tool_embeddings[tool['name']] = model_embed.encode(text)

# Em runtime, para cada query:
query_embedding = model_embed.encode(user_message)
similarities = {
    name: cosine_similarity(query_embedding, emb)
    for name, emb in tool_embeddings.items()
}
top_tools = sorted(similarities, key=similarities.get, reverse=True)[:8]
```

Melhorias documentadas sobre embedding puro:
- Embedar *queries de exemplo* em vez de descrições (Red Hat Tool2Vec: +30.5% recall)
- Hybrid retrieval: BM25 lexical + dense vector + re-ranking (+19.4% Recall@5)
- Embedding progressivo condicionado ao histórico de execução (Apple ProTIP)

O ponto fraco é **retrieval miss**: a query "check this area" pode mapear para
buffer, area calculation, ou containment check, e embeddings podem errar.

**B) Deferred loading (Anthropic / OpenAI nativo)**

Anthropic lançou o Tool Search Tool (nov 2025): registra tools com
`defer_loading: true` e o modelo vê apenas um primitivo de busca (~500 tokens).
Quando Claude precisa de uma capability, busca e carrega 3-5 tools sob demanda.

Resultados: 85% redução de tokens (de ~77K para ~8.7K com 50 tools MCP),
e acurácia *melhorou* (Opus 4 de 49% para 74%, Opus 4.5 de 79.5% para 88.1%).
Menos tools irrelevantes no contexto = menos confusão.

OpenAI tem feature paralela com `tool_search` e `defer_loading`, adicionando
namespaces que agrupam tools relacionadas.

**C) Roteamento hierárquico**

Agrupar tools em categorias. O LLM primeiro escolhe a categoria,
depois vê só as tools daquela categoria:

```python
TOOL_GROUPS = {
    "resolucao_geografica": [
        "geocode", "search_municipality", "search_state",
        "search_named_region", "autocomplete_placename"
    ],
    "busca_produtos": [
        "search_products", "rank_by_scale", "rank_by_date",
        "explain_product_type"
    ],
    "operacoes_espaciais": [
        "buffer", "intersect", "compute_route",
        "search_coastline", "search_border"
    ],
    "busca_feicoes": [
        "search_features", "search_hydrography",
        "search_infrastructure", "search_military_installation",
        "search_conservation_unit", "search_indigenous_land"
    ],
}
```

Salesforce Agentforce usa esse padrão com "Topics" em produção ($540M ARR).
O risco: queries que cruzam categorias (a maioria das nossas) precisam de
múltiplos grupos, anulando a economia.

### Decisão para o geoportal

```
Agora (19 tools):
  → Carregar todas upfront. Sem retrieval, sem deferred loading.
  → Investir em qualidade das descrições e few-shot examples.
  → Usar prompt caching para não pagar tokens repetidos.

Quando crescer para 30+ tools:
  → Implementar deferred loading (se usando Claude/OpenAI API)
  → OU retrieval por embedding via pgvector (que já temos no PostGIS)
  → Agrupar tools em namespaces lógicos

Quando crescer para 100+ tools:
  → Retrieval híbrido (BM25 + embedding + re-ranking)
  → FunctionGemma 270M como pre-roteador de categoria
  → Ou Programmatic Tool Calling (Claude escreve código de orquestração
    em sandbox, 37% redução de tokens em tarefas multi-tool complexas)
```

### Otimização de descrições (alto ROI)

A pesquisa mostrou que descrições bem escritas dão mais retorno do que
qualquer infraestrutura de retrieval. Práticas para tools geoespaciais:

```python
# RUIM: descrição vaga
{
    "name": "buffer",
    "description": "Creates a buffer around a geometry."
}

# BOM: descrição com semântica espacial, when-to-use, constraints
{
    "name": "buffer",
    "description": (
        "Cria zona de influência (polígono) ao redor de qualquer geometria. "
        "Retorna geometry_ref do polígono resultante. "
        "USE PARA: expandir ponto em área de busca, criar corredor ao longo "
        "de rota/rio, definir faixa ao longo de fronteira/costa. "
        "NÃO USE PARA: recortar geometria (use intersect). "
        "Referências de raio: 500m corredor estreito (pontes), "
        "5000m área local (município), 20000m faixa regional (litoral), "
        "150000m faixa de fronteira legal."
    ),
}
```

Few-shot examples na descrição melhoram a seleção significativamente.
LangChain documentou que Claude Sonnet foi de 16% zero-shot para 52%
com apenas 3 exemplos semanticamente similares por tool.

---

## 6. O Agent Loop: Implementação

### 6.1 System Prompt (curto e focado)

O system prompt deve ser curto. Instruções detalhadas entram via context engineering
(seção 2.3), não num prompt gigante que polui toda interação.

```python
SYSTEM_PROMPT_BASE = """
Você é o sistema de busca inteligente de um geoportal cartográfico brasileiro.
Interprete perguntas em linguagem natural e resolva usando as tools disponíveis.

REGRAS FUNDAMENTAIS:
- SEMPRE resolva a geometria de busca ANTES de chamar search_products.
- Todas as geometrias são passadas como geometry_ref (referências opacas).
  Nunca tente interpretar ou gerar coordenadas. Use as tools para obtê-las.
- Se um topônimo é ambíguo, use autocomplete_placename e pergunte ao usuário.
- Se a busca retorna vazia, tente expandir raio ou buscar tipos correlatos.
- Ao responder, inclua: tipo, escala/resolução, data, articulação (se carta).

TIPOS DE PRODUTO NO CATÁLOGO:
carta_topografica (escalas 1:25k, 1:50k, 1:100k, 1:250k)
ortoimagem, mds, mdt, imagem_drone, imagem_satelite, modelo_3d, nuvem_pontos
"""
```

### 6.2 O Loop (a parte mais importante, e são ~60 linhas)

```python
# orchestrator.py
import json
import asyncio
from openai import AsyncOpenAI  # SDK compatível OpenAI (funciona com OpenRouter)
from tools import TOOL_FUNCTIONS
from tool_registry import TOOLS
from context.geometry_store import GeometryStore

MAX_ITERATIONS = 12
MAX_TOOL_CALLS_TOTAL = 30


async def run_agent(
    user_message: str,
    model: str = "google/gemma-4-31b-it",
    api_base: str = "https://openrouter.ai/api/v1",
    api_key: str = "...",
    on_progress = None,  # callback para streaming de progresso
):
    """
    O agent loop completo. ~60 linhas que fazem tudo.

    O LLM chama tools, recebe resultados, decide o próximo passo.
    Repete até gerar resposta final (sem tool calls) ou atingir limite.
    """
    client = AsyncOpenAI(base_url=api_base, api_key=api_key)
    store = GeometryStore()  # nova store por requisição

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_BASE},
        {"role": "user", "content": user_message},
    ]

    tool_defs = [{"type": "function", "function": t} for t in TOOLS]
    total_calls = 0

    for iteration in range(MAX_ITERATIONS):
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_defs,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        messages.append(msg.model_dump())

        # Sem tool calls = resposta final
        if not msg.tool_calls:
            return {
                "answer": msg.content,
                "iterations": iteration + 1,
                "total_tool_calls": total_calls,
            }

        # Executa tool calls (paralelo quando possível)
        tasks = []
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)

            if on_progress:
                await on_progress("tool_start", fn_name, fn_args)

            fn = TOOL_FUNCTIONS.get(fn_name)
            if fn:
                tasks.append((tc.id, fn_name, fn(**fn_args)))
            else:
                tasks.append((tc.id, fn_name, None))

        # Execução paralela das tools
        coroutines = [t[2] for t in tasks if t[2] is not None]
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Monta mensagens de resultado
        result_idx = 0
        for tc_id, fn_name, coro in tasks:
            if coro is None:
                result = {"error": f"Tool '{fn_name}' não existe"}
            elif isinstance(results[result_idx], Exception):
                result = {"error": str(results[result_idx])}
                result_idx += 1
            else:
                result = results[result_idx]
                result_idx += 1

            messages.append({
                "role": "tool",
                "tool_call_id": tc_id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
            total_calls += 1

            if on_progress:
                await on_progress("tool_result", fn_name, result)

        if total_calls >= MAX_TOOL_CALLS_TOTAL:
            messages.append({
                "role": "system",
                "content": "ATENÇÃO: limite de tool calls atingido. Responda com os resultados que já tem.",
            })

    return {
        "answer": "Desculpe, a busca ficou muito complexa. Pode reformular?",
        "iterations": MAX_ITERATIONS,
        "total_tool_calls": total_calls,
    }
```

### 6.3 Exemplo de Execução

Pergunta: **"Imagens de drone nas pontes entre Santa Maria e Alegrete"**

```
Iteração 1:
  LLM emite 2 tool calls paralelos:
    geocode("Santa Maria, RS")  →  {lat: -29.68, lon: -53.81, geometry_ref: "geom_01"}
    geocode("Alegrete, RS")     →  {lat: -29.78, lon: -55.79, geometry_ref: "geom_02"}

Iteração 2:
  LLM usa coordenadas para calcular rota:
    compute_route(-29.68, -53.81, -29.78, -55.79)
    → {distance_km: 312, geometry_ref: "geom_03"}

Iteração 3:
  LLM cria corredor e busca pontes:
    buffer(geometry_ref="geom_03", raio_metros=500) → {geometry_ref: "geom_04"}
    search_features(tipo="ponte", geometry_ref="geom_04")
    → {total: 3, features: [{nome: "Ponte Rio Ibicuí", geometry_ref: "geom_05"}, ...]}

Iteração 4:
  LLM cria buffer ao redor de cada ponte e busca produtos:
    buffer("geom_05", 1000) → "geom_08"
    buffer("geom_06", 1000) → "geom_09"
    buffer("geom_07", 1000) → "geom_10"

Iteração 5:
    search_products(tipo="imagem_drone", geometry_ref="geom_08") → 1 resultado
    search_products(tipo="imagem_drone", geometry_ref="geom_09") → 0 resultados
    search_products(tipo="imagem_drone", geometry_ref="geom_10") → 0 resultados

Iteração 6:
  LLM gera resposta final (sem tool calls):
    "Encontrei 3 pontes na rota. A Ponte sobre o Rio Ibicuí possui
     imagem de drone de 15/08/2023 (resolução 5cm). As demais não
     possuem cobertura de drone no momento."
```

Total: 6 iterações, ~12 tool calls, 6 chamadas ao LLM.
O LLM viu apenas geometry_refs, nunca GeoJSON.

---

## 7. Modelo de LLM: Benchmark Real de Tool Calling

A pesquisa de 2026 revelou uma distinção crucial: existem modelos "Thinking"
(otimizados para raciocínio, como DeepSeek R1) e modelos "Acting"
(otimizados para execução confiável de tools).

**Para tool calling, modelos em modo não-thinking são preferíveis.**
Modelos de raciocínio tendem a raciocinar *sobre* tool calls em vez de
executá-las, um modo de falha sutil e difícil de debugar.

### 7.1 Benchmarks que importam para nosso caso

Os benchmarks relevantes para um agente com 19 tools e 5-12 chamadas encadeadas
são o BFCL v3/v4 (multi-turn tool chaining) e o τ²-Bench (multi-turn com API tools
e aderência a regras). Benchmarks single-call como Nexus são irrelevantes.

Achado crítico dos benchmarks: o "abismo agêntico". Modelos que tiram nota
alta em single-call colapsam em multi-turn. O WildToolBench (2025) mostrou
que nenhum modelo atinge >15% em tarefas de tool-use composicionalmente
complexas. O TELLER-Bench (domínio bancário) mostra que mesmo Gemini-3-Pro
atinge apenas 38% em cadeias multi-step, e modelos open-source <32B ficam
abaixo de 11%.

Para geoespacial especificamente, o GeoBenchX (23 tools, até 25 iterações)
encontrou que function-calling atinge 85.7% de acurácia vs 97.1% para
code-generation. Mas function calling dá mais estabilidade para operações
estruturadas e repetíveis como as nossas queries PostGIS.

### 7.2 Ranking de Modelos para o Geoportal

Ordenado pela combinação de score multi-turn + viabilidade de deployment + custo.

**Tier 1: API cloud, alta confiabilidade**

| Modelo | τ²-Bench | BFCL v4 | Contexto | Custo (in/out $/M) | Nota |
|---|---|---|---|---|---|
| GLM-5 (744B/40B MoE) | 89.7% | -- | 200K | $0.72/$2.30 | Teto open-source. Lento (~17 tok/s) |
| DeepSeek V3.2 (671B/37B) | 63-96%* | -- | 164K | $0.25/$0.38 | "Thinking with tools": mantém raciocínio entre calls. Melhor custo-benefício API |
| MiniMax M2.5 (230B/10B) | -- | 76.8% | 196K | $0.12/$1.00 | Líder BFCL multi-turn. Formato XML próprio (OpenRouter normaliza) |

*DeepSeek V3.2: 96.2% em domínio estruturado (telecom), 63.8% em ambíguo (airline).
O "thinking with tools" é relevante para nós: preserva o raciocínio de por que pediu
um buffer quando vai usar o resultado na próxima interseção.

**Tier 2: Rodável localmente em GPU 24GB (Q4)**

| Modelo | τ²-Bench | BFCL v4 | VRAM Q4 | Custo API | Nota |
|---|---|---|---|---|---|
| **GLM-4.7-Flash** (30B/3.6B) | **79.5%** | 74.6% | ~15GB | $0.06/$0.40 | **Melhor local**. Formato OpenAI. Single RTX 4090 |
| Qwen3.5-35B (35B/3B MoE) | 81.2% | 67.3% | ~22GB | $0.16/$1.30 | Bom score, mas **tool calling quebrado no Ollama** (bug de formato). Usar vLLM com `--tool-call-parser qwen3_coder` |
| Qwen3.5-27B (27B denso) | 79.0% | 68.5% | ~16GB | $0.20/$1.56 | Mesmos bugs do 35B no Ollama |
| Gemma 4 31B (31B denso) | -- | -- | ~24GB | $0.14/$0.40 | Lançado 02/04/2026, sem benchmarks de tool calling ainda. Tool calling nativo, Apache 2.0 |
| Gemma 4 26B (25B/3.8B MoE) | -- | -- | ~16GB | TBD | Variante MoE, mais rápida. Precisa validação |
| Devstral-Small-2 (24B denso) | -- | -- | ~15GB | $0.10/$0.30 | Infraestrutura Mistral madura. 256K contexto. Sem benchmarks publicados |

**Tier 3: Ultra-eficientes (limitações)**

| Modelo | VRAM Q4 | Contexto | Nota |
|---|---|---|---|
| Nemotron-Cascade-2 (30B/3B) | ~19GB | 1M | 187 tok/s RTX 3090, mas só 52.9% BFCL. Medíocre para 19 tools |
| Rnj-1 8B | ~5GB | **32K** | 62.2% BFCL. Contexto muito curto para 19 tools |
| LFM2 (24B/2B) | ~14.5GB | **32K** | 293 tok/s em H100, mas 32K não cabe 19 tool schemas + conversa |
| FunctionGemma 270M | ~300MB | 32K | 85% em ação mobile. Viável como pre-roteador, não como agente |

### 7.3 Alertas de Integração

Coisas que os benchmarks não capturam:

**Formato de tool call varia entre modelos.** Existem pelo menos 4 formatos:
OpenAI JSON (GLM, DeepSeek, Kimi), Mistral-style (Devstral), Qwen3-Coder XML,
MiniMax XML. O OpenRouter normaliza para quem usa API, mas quem faz self-hosting
precisa configurar o parser correto no vLLM/SGLang. Usar o parser errado degrada
a acurácia silenciosamente ou causa falha total (caso Qwen 3.5 + Ollama).

**Mistral-Large-3 alerta contra muitas tools.** A documentação diz:
"Mantenha o conjunto de tools bem definido e limite ao mínimo necessário."
Com 19 tools pode ser necessário compressão de descrições ou subsetting dinâmico.

**DeepSeek V3.2 tende a repetir tool calls** em loops longos e apresenta
drift gradual nos argumentos JSON. Necessário bounded iteration loop (já temos).

**OpenRouter `:exacto`** é uma variante otimizada para tool calling que seleciona
dinamicamente providers com melhor qualidade de function calling. Vale usar em produção.

### 7.4 Recomendação Final de Modelo

```
Protótipo (fase 1):
  GLM-4.7-Flash via OpenRouter → $0.06/$0.40, melhor score local, formato OpenAI
  Fallback: Gemma 4 31B via OpenRouter → $0.14/$0.40, Apache 2.0 (aguardar benchmarks)

Produção (fase 2):
  DeepSeek V3.2 via OpenRouter → $0.25/$0.38, "thinking with tools"
  OU GLM-5 via OpenRouter → $0.72/$2.30, se precisar máxima acurácia

Local / air-gapped:
  GLM-4.7-Flash via vLLM/SGLang → single RTX 4090, 15GB VRAM Q4
  Parser: --tool-call-parser glm (nativo OpenAI-compatible)

Modelo roteador (opcional):
  FunctionGemma 270M → 300MB, pode rodar como pre-classifier de complexidade
```

---

## 8. Padrões de Orquestração: Quando o While-Loop Não Basta

O while-loop resolve 80% dos casos. Os 20% restantes:

### 8.1 Quando usar Plan-then-Execute (DAG)

Para consultas complexas com muitas etapas previsíveis (Categoria C e F do catálogo),
o LLM pode gerar um plano estruturado e executar steps independentes em paralelo.

```python
async def run_planned_agent(user_message: str):
    """
    Fase 1: LLM gera plano como JSON (1 chamada ao LLM)
    Fase 2: Executor resolve dependências e roda em paralelo (0 chamadas ao LLM)
    Fase 3: LLM gera resposta final (1 chamada ao LLM)

    Total: 2 chamadas ao LLM em vez de 6-8 no while-loop.
    """

    # Fase 1: planejar
    plan = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PLANNING_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )
    steps = json.loads(plan.choices[0].message.content)["steps"]

    # Fase 2: executar com resolução de dependências
    results = {}
    for batch in topological_batches(steps):
        # steps sem dependências pendentes rodam em paralelo
        resolved = [resolve_refs(s, results) for s in batch]
        batch_results = await asyncio.gather(*[
            TOOL_FUNCTIONS[s["tool"]](**s["args"]) for s in resolved
        ])
        for step, result in zip(batch, batch_results):
            results[step["id"]] = result

            # Se falhou: replanejar (cai de volta pro while-loop)
            if "error" in result or "ambiguous" in result:
                return await run_agent(user_message)  # fallback

    # Fase 3: resposta final
    summary = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Resuma os resultados para o usuário."},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": json.dumps(results, default=str)},
        ],
    )
    return summary.choices[0].message.content


def topological_batches(steps: list) -> list[list]:
    """
    Agrupa steps em batches que podem rodar em paralelo.
    Steps sem dependências pendentes vão no mesmo batch.
    """
    done = set()
    remaining = list(steps)
    batches = []

    while remaining:
        batch = []
        for s in remaining:
            deps = extract_refs(s["args"])  # acha $s1, $s2 etc
            if all(d in done for d in deps):
                batch.append(s)
        if not batch:
            raise ValueError("Dependência circular no plano")
        for s in batch:
            remaining.remove(s)
            done.add(s["id"])
        batches.append(batch)

    return batches
```

### 8.2 Quando usar o que

```
Complexidade da pergunta       →  Padrão recomendado
─────────────────────────────────────────────────────
Simples (1-3 tools)            →  While-loop direto
  "carta 25k de Alecrim"

Média (4-8 tools, previsível)  →  Plan-then-Execute (DAG)
  "ortoimagens do litoral do RS"

Complexa (iteração sobre        →  While-loop (precisa adaptar
feições, ambiguidade)              no meio da execução)
  "drone nas pontes da rota
   entre Santa Maria e Alegrete"

Conceitual (sem busca)          →  Resposta direta, sem tools
  "diferença entre MDS e MDT?"
```

### 8.3 Padrão Anthropic: Classificar + Rotear

A Anthropic recomenda começar classificando a pergunta e roteando
para o padrão adequado:

```python
async def smart_router(user_message: str):
    """
    Classifica a pergunta e escolhe o padrão de execução.
    1 chamada rápida ao LLM para classificar (pode ser modelo menor/mais barato).
    """
    classification = await client.chat.completions.create(
        model="google/gemma-4-31b-it",
        messages=[
            {"role": "system", "content": CLASSIFICATION_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )

    result = json.loads(classification.choices[0].message.content)

    match result["tipo"]:
        case "conceitual":
            return await answer_directly(user_message)
        case "simples":
            return await run_agent(user_message)
        case "planejavel":
            return await run_planned_agent(user_message)
        case "ambiguo":
            return await ask_clarification(user_message, result["ambiguidades"])
```

---

## 9. Observabilidade: Instrumentar Desde o Dia 1

89% das equipes com agentes em produção investem em tracing.
Para o geoportal:

```python
# observability.py
import time
import json
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ToolTrace:
    tool_name: str
    args: dict
    result_summary: str
    duration_ms: float
    error: str = None

@dataclass
class AgentTrace:
    query: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    iterations: int = 0
    tool_traces: list[ToolTrace] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    model: str = ""
    final_answer: str = ""
    success: bool = True

    @property
    def total_duration_ms(self) -> float:
        return sum(t.duration_ms for t in self.tool_traces)

    @property
    def total_tool_calls(self) -> int:
        return len(self.tool_traces)

    def to_log(self) -> dict:
        return {
            "query": self.query,
            "model": self.model,
            "iterations": self.iterations,
            "tool_calls": self.total_tool_calls,
            "duration_ms": self.total_duration_ms,
            "tokens_in": self.total_input_tokens,
            "tokens_out": self.total_output_tokens,
            "success": self.success,
            "tools_used": [t.tool_name for t in self.tool_traces],
            "errors": [t.error for t in self.tool_traces if t.error],
        }
```

Logs estruturados permitem:
- Ver quais tools são mais usadas (priorizar otimização)
- Identificar queries que estouram o limite de iterações
- Medir latência por tool (gargalos no PostGIS vs OSRM vs LLM)
- Calcular custo por query (tokens in/out * preço do modelo)

---

## 10. Resumo das Decisões Arquiteturais

| Decisão | Escolha | Justificativa |
|---|---|---|
| **Framework** | Nenhum. While-loop puro. | Consenso 2026: "os agentes que sobrevivem produção são os mais debugáveis, não os mais sofisticados" |
| **Protocolo de tools** | Function calling nativo da API | Todas as tools são locais. MCP resolve integração externa, que não precisamos |
| **Modelo (protótipo)** | GLM-4.7-Flash via OpenRouter | $0.06/$0.40, 79.5% τ²-Bench, formato OpenAI, roda local em RTX 4090 (15GB Q4) |
| **Modelo (produção)** | DeepSeek V3.2 ou GLM-5 | V3.2: melhor custo ($0.25/$0.38) + "thinking with tools". GLM-5: máxima acurácia (89.7% τ²-Bench) |
| **Modelo (local)** | GLM-4.7-Flash via vLLM/SGLang | Único modelo com score τ²-Bench alto (79.5%) que roda em single GPU 24GB |
| **Tool loading** | Todas 19 upfront, sem retrieval | ~4K tokens (2% do contexto). Degradação começa em 30-50 tools. Investir em descrições |
| **Geometrias no contexto** | Geometry Store com refs | Context engineering: LLM nunca vê GeoJSON, trabalha com referências opacas |
| **Orquestração** | While-loop + fallback Plan-then-Execute | While-loop para 80% dos casos; plano DAG para queries previsíveis de 4-8 steps |
| **Execução de tools** | Paralela (asyncio.gather) | LLMs modernos emitem múltiplas tool calls por iteração |
| **Observabilidade** | Tracing estruturado desde dia 1 | 89% das equipes com agentes em produção usam tracing |
| **Banco** | PostGIS local | Todas as queries são espaciais, tudo na mesma máquina |
| **Roteamento** | OSRM local | Sem dependência de API externa para compute_route |

### O que NÃO usar

| Tecnologia | Por que não |
|---|---|
| **LangChain** | Abstração pesada, 45% dos que experimentaram nunca deployaram |
| **LangGraph** | Overkill para nosso caso (single-agent, sem checkpointing necessário) |
| **CrewAI** | Multi-agente consome 2x tokens e 3x tempo vs single-agent em tarefas simples |
| **MCP** | Todas as tools são locais. MCP resolve o problema de integrar serviços remotos |
| **Modelos "Thinking"** | Raciocinam *sobre* tools em vez de executá-las. Usar modo não-thinking |
| **Tool retrieval dinâmico** | Prematuro com 19 tools. Retrieval miss é mais perigoso que ~4K tokens extras |
| **Qwen 3.5 via Ollama** | Tool calling completamente quebrado por bug de formato. Funciona via vLLM/SGLang |
| **Gemma 4 (ainda)** | Lançado 02/04/2026, sem benchmarks de tool calling. Aguardar 2-4 semanas de validação |

### Stack final do protótipo

```
Python 3.12 + FastAPI + asyncpg
PostgreSQL 16 + PostGIS 3.5 + pg_trgm + unaccent
OSRM (Docker, para rotas)
OpenRouter API (GLM-4.7-Flash primário, Gemma 4 31B como fallback)
~200 linhas de agent loop + ~500 linhas de tools + schema PostGIS
```

### Caminho de evolução

```
Fase 1 (protótipo):
  GLM-4.7-Flash via OpenRouter
  19 tools upfront
  While-loop simples
  Geometry Store com refs

Fase 2 (validação):
  Benchmark Gemma 4 quando scores saírem
  Testar DeepSeek V3.2 "thinking with tools" para queries complexas
  Adicionar few-shot examples dinâmicos nas descrições de tools
  Prompt caching

Fase 3 (produção):
  Roteamento por complexidade (GLM-4.7-Flash local para simples,
  DeepSeek V3.2/GLM-5 API para complexas)
  Se tools > 30: implementar deferred loading ou pgvector retrieval
  Se queries > 100/min: self-hosting GLM-4.7-Flash em vLLM com GPU dedicada
```
