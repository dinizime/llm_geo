# CLAUDE.md - Protótipo LLM Tool Calling para Busca Espacial

## O que é este projeto

Protótipo para validar a capacidade de modelos LLM de orquestrar buscas geoespaciais
em linguagem natural usando tool calling nativo. Benchmark multi-modelo com 75 queries.

O objetivo final é um agente para o Geoportal do Exército Brasileiro que recebe perguntas
como "cartas topográficas de Alecrim" ou "ortoimagens ao longo da BR-101 entre Florianópolis
e Porto Alegre" e as resolve encadeando tools espaciais (geocode, buffer, intersect, search).

## Stack

- **Python 3.11+**
- **OpenRouter** como gateway de LLM (API compatível com OpenAI)
- **SDK openai** (apontando para OpenRouter)
- **PostgreSQL** local (postgres/postgres) para armazenar resultados dos benchmarks
- **pytest** para testes unitários
- Sem framework de agente — while-loop direto

## Arquitetura

```
Pergunta (texto) → Agent Loop (while tool_calls) → Tools simuladas → Resposta
     │                                                                    │
     └─── benchmark.py (75 queries) ──→ runner.py ──→ PostgreSQL ──→ report.py ──→ HTML
```

- O agent loop é um while-loop simples (~70 linhas)
- As tools são **simuladas** — retornam dados sintéticos determinísticos
- O GeometryStore mantém referências de geometria fora do contexto do LLM
- O runner testa N modelos contra 75 queries e salva resultados no PostgreSQL
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
│   ├── tools.py                # 16 tool definitions (JSON schema)
│   ├── tool_handlers.py        # Implementação simulada das tools
│   ├── geometry_store.py       # Store de geometrias (refs, não GeoJSON)
│   ├── synthetic_data.py       # Dados sintéticos determinísticos
│   ├── benchmark.py            # 75 queries categorizadas com expectativas
│   ├── runner.py               # CLI: roda benchmark multi-modelo
│   ├── report.py               # Gera relatório HTML com gráficos
│   └── db.py                   # PostgreSQL CRUD para resultados
└── tests/
    ├── test_tool_handlers.py   # 22 testes unitários (sem rede)
    └── test_agent.py           # Testes de integração (requer OpenRouter)
```

## Convenções

- Código e comentários em inglês; docs e queries de exemplo em português
- Nomes de tools em snake_case com prefixo semântico (search_, compute_, rank_)
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

# Testes unitários (sem rede, sem DB)
pytest tests/test_tool_handlers.py -v

# Benchmark com um modelo
export OPENROUTER_API_KEY=sk-or-...
python -m llm_tool_calling.runner --models google/gemma-4-27b-it

# Benchmark comparando modelos
python -m llm_tool_calling.runner --models google/gemma-4-27b-it qwen/qwen3-32b meta-llama/llama-4-scout

# Filtrar por categoria ou dificuldade
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --category "Localização Simples"
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --difficulty easy

# Rodar queries específicas
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --ids A01 B01 C01

# Gerar relatório HTML
python -m llm_tool_calling.report
# Abrir reports/index.html no browser
```

## Benchmark: 75 queries em 16 categorias

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
