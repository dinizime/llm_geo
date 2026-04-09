# CLAUDE.md - Benchmark de Raciocínio Espacial com Tool Calling

## O que é este projeto

Benchmark para avaliar a capacidade de LLMs de orquestrar ferramentas espaciais
para responder perguntas geográficas em linguagem natural. Testa raciocínio multi-step
com 27 tools e ~226 queries em 34 categorias operacionais.

O objetivo final é um agente para o Geoportal do Exército Brasileiro que recebe perguntas
como "quantas pontes tem na rota entre Alegrete e Rosário do Sul?", "obstáculos verticais
num raio de 5km de Uruguaiana" ou "qual o hospital mais próximo da 8ª Brigada?" e as
resolve encadeando tools espaciais.

## Stack

- **Python 3.11+**
- **OpenRouter** como gateway de LLM (API compatível com OpenAI)
- **SDK openai** (apontando para OpenRouter)
- **PostgreSQL** local (postgres/postgres) para armazenar resultados dos benchmarks
- **Shapely** + **pyproj** para operações geométricas reais
- **pytest** para testes de integração
- Sem framework de agente — while-loop direto

## Arquitetura

```
Pergunta (texto) → Agent Loop (while tool_calls) → Tools reais → Resposta
     │                                                                │
     └─── benchmark.py (~226 queries) ──→ runner.py ──→ PostgreSQL ──→ report.py ──→ HTML
```

- O agent loop é um while-loop simples (~70 linhas)
- As tools usam **APIs reais**: Nominatim (geocoding), Overpass/OSM (feições),
  IBGE (municípios/estados), OSRM (rotas), Open-Meteo (elevação)
- Operações geométricas usam **Shapely/pyproj** (intersect, contains, area, length)
- Dados de domínio do Geoportal (produtos, instalações militares, regiões nomeadas) são mantidos localmente
- O GeometryStore mantém referências de geometria fora do contexto do LLM
- O runner testa N modelos contra ~226 queries e salva resultados no PostgreSQL
- O report gera `reports/index.html` estático com gráficos comparativos

## Estrutura de pastas

```
├── CLAUDE.md
├── pyproject.toml
├── docs/                       # Documentação e pesquisa de referência
├── reports/                    # HTML gerado pelo report.py
│   └── index.html
├── src/llm_tool_calling/
│   ├── agent.py                # Agent loop (while tool_calls)
│   ├── tools.py                # 26 tool definitions (JSON schema)
│   ├── tool_handlers.py        # Implementação das tools (APIs reais)
│   ├── geo.py                  # Operações geométricas (Shapely/pyproj)
│   ├── geometry_store.py       # Store de geometrias (refs, não GeoJSON)
│   ├── synthetic_data.py       # Dados de domínio do Geoportal (produtos, OM, regiões)
│   ├── benchmark.py            # ~180 queries categorizadas com expectativas
│   ├── runner.py               # CLI: roda benchmark multi-modelo
│   ├── report.py               # Gera relatório HTML com gráficos
│   └── db.py                   # PostgreSQL CRUD para resultados
└── tests/
    ├── test_tool_handlers.py   # 68 testes unitários (sem rede)
    └── test_agent.py           # Testes de integração (requer OpenRouter)
```

## 27 Tools em 7 categorias

### Buscas geográficas (13)
geocode, create_point, reverse_geocode, search_municipality, search_state,
search_named_region, search_hydrography, search_border, search_features,
search_military_installation, search_road, list_municipalities_in, get_neighbors

### Operações espaciais (5)
buffer, intersect, compute_route, check_intersection, check_contains

### Computação geométrica (3)
compute_distance, compute_area, compute_length

### Elevação e terreno (2)
get_elevation, get_terrain_profile

### Análise de feições (2)
find_nearest, features_along_route

### Produtos (2)
search_products, search_by_articulation

## 20 tipos de feições (search_features)

| Grupo | Tipos |
|-------|-------|
| Transporte | ponte, tunel, estacao_ferroviaria, travessia_balsa |
| Obstáculos verticais | torre_comunicacao, aerogerador, linha_transmissao, chamine_industrial |
| Aviação | aeroporto, heliporto, campo_pouso |
| Infraestrutura social | hospital, escola, posto_combustivel |
| Hídrica | barragem, reservatorio, estacao_tratamento_agua |
| Territorial | terra_indigena, edificacao_destaque |
| Militar | area_treinamento |

Cada feição tem **atributos** (altura_m, comprimento_m, leitos, pista_m, etc.)
que permitem ranking e superlativos ("maior ponte", "torre mais alta").

## Convenções

- Código e comentários em inglês; docs e queries de exemplo em português
- Nomes de tools em snake_case com prefixo semântico (search_, compute_, get_, check_)
- search_features aceita filtro de atributos (atributo, operador, valor) com operadores: >, <, >=, <=, =, in
- Testes unitários (test_tool_handlers) não precisam de rede nem DB
- Benchmark requer OPENROUTER_API_KEY e PostgreSQL rodando

## Variáveis de ambiente

- `OPENROUTER_API_KEY` — chave do OpenRouter (obrigatória para benchmark)
- `OPENROUTER_MODEL` — modelo default (default: `google/gemma-4-27b-it`)
- `DATABASE_URL` — conexão PostgreSQL (default: `postgresql://postgres:postgres@localhost:5432/postgres`)

## Como rodar

```bash
# Setup
pip install -e .

# Testes unitários (sem rede, sem DB) — 44 testes
pytest tests/test_tool_handlers.py -v

# Benchmark com um modelo
export OPENROUTER_API_KEY=sk-or-...
python -m llm_tool_calling.runner --models google/gemma-4-27b-it

# Benchmark comparando modelos
python -m llm_tool_calling.runner --models google/gemma-4-27b-it qwen/qwen3-32b meta-llama/llama-4-scout

# Filtrar por categoria
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --category "Planejamento de Rota"
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --category "Identificação de Obstáculos"
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --difficulty hard

# Rodar queries específicas
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --ids Q01 R01 S01 AA01

# Gerar relatório HTML
python -m llm_tool_calling.report

# Interface web (requer Flask e OPENROUTER_API_KEY)
python -m llm_tool_calling.web                          # http://localhost:5000
python -m llm_tool_calling.web --port 8080              # porta customizada
python -m llm_tool_calling.web --model qwen/qwen3-32b   # modelo específico
```

## Benchmark: ~226 queries em 34 categorias

### Domínio: Busca de Produtos (82 queries, A-P)
| Categoria | Queries | Dificuldade | Padrão principal |
|---|---|---|---|
| Localização Simples | A01-A10 | easy-medium | municipality/geocode → search_products |
| Região Informal | B01-B06 | medium | search_named_region → search_products |
| Rota | C01-C05 | hard | geocode → compute_route → buffer → search_products |
| Filtro Temporal | D01-D06 | medium | search → rank_by_date |
| Instalação Militar | E01-E05 | medium-hard | search_military_installation → search_products |
| Fronteira | F01-F05 | hard | search_border → buffer → search_products |
| Feições Geográficas | G01-G05 | hard | search_features → search_products |
| Hidrografia | H01-H05 | medium-hard | search_hydrography → buffer → search_products |
| Inventário | I01-I04 | easy | search_products (tipo="*") |
| Escala | J01-J04 | medium | search_products → rank_by_scale |
| Desambiguação | K01-K03 | medium-hard | autocomplete_placename |
| Conceitual | L01-L05 | easy | explain_product_type (sem busca) |
| Buffer/Raio | M01-M04 | medium | geocode → buffer → search_products |
| Combinada | N01-N06 | hard | multi-step complexo |
| Formulação Variada | O01-O05 | easy | mesma intenção, frases diferentes |
| Estado | P01-P04 | medium | search_state → search_products |

### Domínio: Raciocínio Espacial (~100 queries, Q-AB)
| Categoria | Queries | Dificuldade | Padrão principal |
|---|---|---|---|
| Planejamento de Rota | Q01-Q12 | medium-hard | geocode → compute_route → features_along_route |
| Identificação de Obstáculos | R01-R10 | medium-hard | geocode → buffer → search_features(torre/aerogerador/linha) |
| Infraestrutura | S01-S10 | easy-hard | search_municipality → search_features/find_nearest |
| Resposta a Desastres | T01-T08 | medium-hard | geocode → find_nearest/buffer → search_features |
| Planejamento de Aviação | U01-U08 | medium-hard | geocode → buffer → search_features + rank_features |
| Hidrografia e Terreno | V01-V08 | medium-hard | search_hydrography → compute_length/check_intersection |
| Operações de Fronteira | W01-W08 | medium-hard | search_border → buffer → search_features |
| Rodovias | X01-X08 | medium-hard | search_road → features_along_route/list_municipalities |
| Militar Avançado | Y01-Y08 | medium-hard | search_military → compute_route → features_along_route |
| Multi-Step Complexo | Z01-Z10 | hard | 4+ tools encadeados |
| Atributos e Superlativos | AA01-AA10 | easy-hard | search → rank_features / compute_area |
| Formulação Natural | AB01-AB08 | easy-medium | mesma intenção, linguagem informal |

### Domínio: Novas Capacidades (36 queries, AC-AH)
| Categoria | Queries | Dificuldade | Padrão principal |
|---|---|---|---|
| Coordenadas | AC01-AC06 | medium-hard | create_point/reverse_geocode → search/find |
| Elevação | AD01-AD07 | medium-hard | geocode → get_elevation/get_terrain_profile |
| Contenção Espacial | AE01-AE06 | medium-hard | search → check_contains |
| Vizinhança | AF01-AF05 | medium-hard | search_municipality → get_neighbors |
| Articulação | AG01-AG05 | easy-medium | search_by_articulation |
| Filtro por Atributo | AH01-AH07 | medium-hard | search_features com atributo/operador/valor |
| Fora do Escopo | AI01-AI05 | easy-medium | recusa sem tools (off-topic, prompt injection) |

## Validação de resultados

O benchmark usa 7 tipos de validação (não-exclusivos):
- **answer_keywords**: palavras que DEVEM aparecer na resposta
- **expected_product_ids**: IDs de produtos encontrados no trace
- **expected_numeric**: valores numéricos dentro de um range (distância, área)
- **expected_boolean**: predicados booleanos (intersecta, contém)
- **expected_count**: contagem de feições dentro de um range
- **reject**: agente NÃO deve chamar tools (fora do escopo / prompt injection)
