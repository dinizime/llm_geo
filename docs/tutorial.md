# Tutorial: Configuração e Uso do Benchmark

## 1. Pré-requisitos

- Python 3.11+
- PostgreSQL rodando localmente (user: postgres, password: postgres)
- Conta no OpenRouter (https://openrouter.ai)

## 2. Configurar o OpenRouter

### 2.1 Criar conta e obter API key

1. Acesse https://openrouter.ai e crie uma conta (pode logar com Google/GitHub)
2. Vá em **Keys** (https://openrouter.ai/keys)
3. Clique em **Create Key**
4. Copie a chave gerada (formato: `sk-or-v1-...`)
5. Adicione créditos em **Credits** (https://openrouter.ai/credits) — $5 é suficiente para ~500 queries

### 2.2 Configurar a chave

No terminal (Linux/Mac):
```bash
export OPENROUTER_API_KEY=sk-or-v1-sua-chave-aqui
```

No PowerShell (Windows):
```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-sua-chave-aqui"
```

Para persistir, adicione ao seu `.bashrc`, `.zshrc` ou perfil do PowerShell.

### 2.3 Modelos disponíveis

O OpenRouter dá acesso a dezenas de modelos com uma única API key. Modelos recomendados para testar tool calling:

| Modelo | ID no OpenRouter | Preço (~por 1M tokens) | Notas |
|---|---|---|---|
| Gemma 4 27B | `google/gemma-4-27b-it` | $0.10 in / $0.20 out | Nativo em function calling, bom custo-benefício |
| Qwen3 32B | `qwen/qwen3-32b` | $0.20 in / $0.20 out | Forte em tool calling |
| Llama 4 Scout | `meta-llama/llama-4-scout` | $0.15 in / $0.40 out | Meta, bom em raciocínio |
| Gemini 2.5 Flash | `google/gemini-2.5-flash-preview` | $0.15 in / $0.60 out | Muito rápido |
| Mistral Small | `mistralai/mistral-small-3.2` | $0.10 in / $0.30 out | Europeu, bom em multi-idioma |
| GPT-4o Mini | `openai/gpt-4o-mini` | $0.15 in / $0.60 out | OpenAI, referência |
| Claude Haiku | `anthropic/claude-haiku-4-5` | $0.80 in / $4.00 out | Anthropic, mais caro |

Consulte preços atualizados em https://openrouter.ai/models

## 3. Instalar o projeto

```bash
cd llm_tool_calling
pip install -e .
```

Isso instala as dependências: `openai`, `psycopg2-binary`, `pytest`.

## 4. Verificar PostgreSQL

O benchmark armazena resultados no PostgreSQL local. Conexão padrão:
```
postgresql://postgres:postgres@localhost:5432/postgres
```

Para usar outra conexão:
```bash
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

As tabelas são criadas automaticamente na primeira execução.

## 5. Rodar o benchmark

### 5.1 Testar com um modelo

```bash
python -m llm_tool_calling.runner --models google/gemma-4-27b-it
```

Saída:
```
LLM Tool Calling Benchmark
Models: google/gemma-4-27b-it
Queries: 82

======================================================================
  Model: google/gemma-4-27b-it
  Queries: 82
======================================================================

  [  1/ 82] A01 (easy  ) Cartas topográficas de Alecrim                        PASS  (2.3s) tools=['search_municipality', 'search_products']
  [  2/ 82] A02 (easy  ) Ortoimagens de Porto Alegre                            PASS  (1.8s) tools=['search_municipality', 'search_products']
  ...

  Summary: 65/82 passed (79.3%)
  Failures: 15, Errors: 2
```

### 5.2 Comparar múltiplos modelos

```bash
python -m llm_tool_calling.runner \
  --models google/gemma-4-27b-it qwen/qwen3-32b openai/gpt-4o-mini
```

### 5.3 Filtrar queries

Por categoria:
```bash
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --category "Rota"
```

Por dificuldade:
```bash
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --difficulty easy
```

Por IDs específicos:
```bash
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --ids A01 B01 C01 L01
```

### 5.4 Ajustar delay entre queries

Para evitar rate limiting (padrão: 1 segundo):
```bash
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --delay 2.0
```

## 6. Gerar relatório de comparação

Após rodar benchmarks, gere o relatório HTML:

```bash
python -m llm_tool_calling.report
```

Isso cria `reports/index.html`. Abra no browser:

```bash
# Linux/Mac
open reports/index.html

# Windows
start reports/index.html
```

### O que o relatório mostra

1. **Cards de resumo** — total de modelos, queries, melhor pass rate
2. **Tabela comparativa** — pass rate, tempo médio, iterações por modelo
3. **Gráfico por categoria** — barras agrupadas mostrando onde cada modelo vai bem/mal
4. **Gráfico por dificuldade** — easy vs medium vs hard por modelo
5. **Tabela detalhada** — cada query com status, tools chamadas, tools faltantes
   - Filtrável por modelo, categoria, status, dificuldade
   - Clique na linha para expandir detalhes (answer, error, etc.)

## 7. Testes unitários (sem rede)

Para rodar os testes que não dependem de OpenRouter nem PostgreSQL:

```bash
pytest tests/test_tool_handlers.py -v
```

## 8. Exemplo de fluxo completo

```bash
# 1. Instalar
pip install -e .

# 2. Configurar
export OPENROUTER_API_KEY=sk-or-v1-...

# 3. Rodar benchmark rápido (só easy, 1 modelo)
python -m llm_tool_calling.runner --models google/gemma-4-27b-it --difficulty easy

# 4. Rodar completo com 3 modelos
python -m llm_tool_calling.runner \
  --models google/gemma-4-27b-it qwen/qwen3-32b openai/gpt-4o-mini

# 5. Ver resultados
python -m llm_tool_calling.report
start reports/index.html
```

## 9. Custos estimados

Uma execução completa (82 queries) com um modelo custa aproximadamente:
- Gemma 4 27B: ~$0.05-0.10
- GPT-4o Mini: ~$0.10-0.20
- Claude Haiku: ~$0.50-1.00

Comparar 5 modelos com todas as 82 queries: ~$1-3 total.

## 10. Categorias do benchmark

O benchmark tem 82 queries em 16 categorias, testando desde buscas simples
("cartas de Alecrim") até encadeamentos complexos ("imagens de drone nas pontes
da rota entre Santa Maria e Alegrete", que precisa geocode → compute_route →
buffer → search_features → search_products).

Cada query define:
- **required_tools**: tools que o modelo DEVE chamar
- **required_sequence**: ordem que deve ser respeitada
- **forbidden_tools**: tools que NÃO devem ser chamadas (ex: pergunta conceitual não deve chamar geocode)
- **difficulty**: easy, medium, hard

O pass/fail é determinístico: o modelo passa se chamou todas as tools requeridas,
na ordem certa, sem chamar tools proibidas.
