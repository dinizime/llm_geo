"""Simple web interface for testing the geoportal search agent."""

import json
import sys
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

from .agent import run_agent
from .providers import PROVIDERS, create_client, detect_provider, get_default_model

app = Flask(__name__)

# Create client once at startup
_provider_id = detect_provider()
_client, _provider_config = create_client(_provider_id)
_model = get_default_model(_provider_id)

print(f"Provider: {PROVIDERS[_provider_id].name}", flush=True)
print(f"Model: {_model}", flush=True)


@app.route("/")
def index():
    return SEARCH_HTML


@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query vazia"}), 400

    result = run_agent(query, client=_client, model=_model, provider_config=_provider_config)

    # Extract products from trace
    products = []
    seen_ids = set()
    for step in result.trace:
        if step["tool"] == "search_products":
            for p in step["result"].get("products", []):
                pid = p.get("id")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    products.append(p)

    # Build step-by-step explanation
    steps = []
    for i, step in enumerate(result.trace, 1):
        tool = step["tool"]
        args = step["args"]
        res = step["result"]

        if tool == "geocode":
            desc = f"Geocodificou \"{args.get('place_name', '')}\""
            detail = f"Encontrado: {res.get('display_name', '?')} ({res.get('lat', '?')}, {res.get('lon', '?')})"
        elif tool == "search_municipality":
            desc = f"Buscou munic\u00edpio \"{args.get('nome', '')}\""
            detail = f"{res.get('nome', '?')}/{res.get('uf', '?')} (pop. {res.get('populacao', '?'):,})" if 'nome' in res else res.get('error', '?')
        elif tool == "search_state":
            desc = f"Buscou estado \"{args.get('uf', '')}\""
            detail = "Pol\u00edgono do estado obtido"
        elif tool == "search_named_region":
            desc = f"Buscou regi\u00e3o \"{args.get('nome', '')}\""
            detail = "Regi\u00e3o encontrada" if 'geometry_ref' in res else res.get('error', '?')
        elif tool == "search_products":
            tipo = args.get('tipo', '*')
            total = res.get('total', 0)
            desc = f"Buscou produtos (tipo={tipo})"
            detail = f"{total} produto(s) encontrado(s)"
        elif tool == "buffer":
            raio = args.get('raio_metros', '?')
            desc = f"Criou buffer de {raio}m"
            detail = "\u00c1rea de busca expandida"
        elif tool == "compute_route":
            desc = "Calculou rota rodovi\u00e1ria"
            detail = f"{res.get('distance_km', '?')}km, ~{res.get('duration_min', '?')}min"
        elif tool == "search_hydrography":
            desc = f"Buscou hidrografia \"{args.get('nome', '')}\""
            detail = f"Encontrado: {res.get('nome', '?')} ({res.get('tipo', '?')})" if 'nome' in res else res.get('error', '?')
        elif tool == "search_border":
            desc = f"Buscou fronteira com \"{args.get('pais', '')}\""
            detail = f"Fronteira com {res.get('pais', '?')}" if 'pais' in res else res.get('error', '?')
        elif tool == "search_military_installation":
            desc = f"Buscou instala\u00e7\u00e3o militar \"{args.get('nome_ou_sigla', '')}\""
            detail = f"Encontrado: {res.get('nome', '?')}" if 'nome' in res else res.get('error', '?')
        elif tool == "search_features":
            desc = f"Buscou fei\u00e7\u00f5es ({args.get('tipo', '?')})"
            features = res.get('features', [])
            detail = f"{len(features)} fei\u00e7\u00e3o(\u00f5es) encontrada(s)"
        elif tool == "intersect":
            desc = "Calculou interse\u00e7\u00e3o de geometrias"
            detail = f"\u00c1rea: {res.get('area_km2', '?')} km\u00b2"
        elif tool == "rank_by_scale":
            desc = f"Ordenou por escala ({args.get('order', '?')})"
            detail = "Produtos reordenados"
        elif tool == "rank_by_date":
            desc = f"Ordenou por data ({args.get('order', '?')})"
            detail = "Produtos reordenados"
        elif tool == "autocomplete_placename":
            desc = f"Autocompletou \"{args.get('fragmento', '')}\""
            candidates = res.get('candidates', [])
            detail = f"{len(candidates)} sugest\u00e3o(\u00f5es)"
        elif tool == "explain_product_type":
            desc = f"Explicou tipo \"{args.get('tipo', '')}\""
            detail = res.get('explanation', '?')[:100]
        else:
            desc = tool
            detail = json.dumps(res, ensure_ascii=False)[:100]

        steps.append({"step": i, "tool": tool, "description": desc, "detail": detail})

    return jsonify({
        "query": query,
        "answer": result.answer,
        "products": products,
        "steps": steps,
        "metrics": {
            "iterations": result.iterations,
            "duration_ms": result.duration_ms,
            "total_tokens": result.total_tokens,
        },
        "error": result.error,
    })


SEARCH_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Busca Inteligente de Produtos</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; color: #1a1a2e; }
.container { max-width: 960px; margin: 0 auto; padding: 20px; }
h1 { font-size: 1.4em; margin-bottom: 20px; color: #1a5632; }

/* Search */
.search-box { display: flex; gap: 8px; margin-bottom: 24px; }
.search-box input {
    flex: 1; padding: 12px 16px; font-size: 1em; border: 2px solid #ddd;
    border-radius: 8px; outline: none; transition: border 0.2s;
}
.search-box input:focus { border-color: #1a5632; }
.search-box button {
    padding: 12px 24px; background: #1a5632; color: white; border: none;
    border-radius: 8px; font-size: 1em; cursor: pointer; white-space: nowrap;
}
.search-box button:hover { background: #2d7a4a; }
.search-box button:disabled { background: #999; cursor: wait; }

/* Loading */
.loading { text-align: center; padding: 40px; color: #666; display: none; }
.loading.active { display: block; }
.spinner { display: inline-block; width: 24px; height: 24px; border: 3px solid #ddd;
    border-top-color: #1a5632; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Results */
.results { display: none; }
.results.active { display: block; }

/* Products */
.products-section { margin-bottom: 16px; }
.products-section h2 {
    font-size: 1em; color: #444; margin-bottom: 10px;
}
.product-card {
    background: white; border-radius: 8px; padding: 12px 16px;
    margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    display: grid; grid-template-columns: 1fr auto; gap: 4px;
}
.product-name { font-weight: 600; font-size: 0.95em; }
.product-type {
    font-size: 0.8em; padding: 2px 8px; border-radius: 12px;
    background: #e3f2fd; color: #1565c0; justify-self: end;
}
.product-meta { font-size: 0.82em; color: #666; grid-column: 1 / -1; }
.no-products { color: #999; font-size: 0.9em; font-style: italic; }

/* Collapsible details */
details { margin-bottom: 12px; }
details summary {
    cursor: pointer; font-size: 0.9em; color: #666; padding: 8px 0;
    user-select: none; list-style: none;
}
details summary::-webkit-details-marker { display: none; }
details summary::before {
    content: '\\25B6'; display: inline-block; margin-right: 8px;
    font-size: 0.7em; transition: transform 0.2s;
}
details[open] summary::before { transform: rotate(90deg); }

/* Answer */
.answer-box {
    background: white; border-radius: 10px; padding: 16px 20px;
    margin-top: 8px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border-left: 4px solid #1a5632; white-space: pre-wrap; line-height: 1.5;
    font-size: 0.92em;
}

/* Steps */
.step {
    background: white; border-radius: 8px; padding: 10px 14px;
    margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    display: flex; align-items: center; gap: 12px;
}
.step-num {
    background: #1a5632; color: white; width: 24px; height: 24px;
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-size: 0.75em; font-weight: 700; flex-shrink: 0;
}
.step-tool { font-family: monospace; font-size: 0.82em; color: #1a5632;
    background: #e8f5e9; padding: 2px 8px; border-radius: 4px; flex-shrink: 0; }
.step-desc { font-size: 0.9em; }
.step-detail { font-size: 0.8em; color: #888; margin-left: auto; flex-shrink: 0; }

/* Metrics */
.metrics {
    display: flex; gap: 16px; margin-top: 6px; font-size: 0.8em; color: #aaa;
}

/* Error */
.error-box {
    background: #fff3f3; border-left: 4px solid #d32f2f; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 16px; color: #b71c1c;
}
</style>
</head>
<body>
<div class="container">
    <h1>Busca Inteligente de Produtos</h1>

    <div class="search-box">
        <input type="text" id="query" placeholder="Descreva o que procura em linguagem natural..."
               autofocus autocomplete="off">
        <button id="btn" onclick="doSearch()">Buscar</button>
    </div>

    <div class="loading" id="loading">
        <div class="spinner"></div>
        <p style="margin-top:10px">Processando busca...</p>
    </div>

    <div class="results" id="results">
        <div id="error-container"></div>

        <div class="products-section" id="products-section">
            <h2>Produtos encontrados (<span id="product-count">0</span>)</h2>
            <div id="products"></div>
        </div>

        <details>
            <summary>Resposta do modelo</summary>
            <div class="answer-box" id="answer"></div>
        </details>

        <details>
            <summary>Passos executados (<span id="step-count">0</span>)</summary>
            <div id="steps" style="margin-top:8px"></div>
        </details>

        <details>
            <summary>Consumo</summary>
            <div class="metrics" id="metrics" style="margin-top:8px"></div>
        </details>
    </div>
</div>

<script>
const input = document.getElementById('query');
const btn = document.getElementById('btn');
input.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });

async function doSearch() {
    const query = input.value.trim();
    if (!query) return;

    btn.disabled = true;
    document.getElementById('loading').classList.add('active');
    document.getElementById('results').classList.remove('active');

    try {
        const res = await fetch('/api/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query})
        });
        const data = await res.json();
        renderResults(data);
    } catch (e) {
        renderResults({error: 'Erro de conexao: ' + e.message, steps: [], products: [], answer: ''});
    } finally {
        btn.disabled = false;
        document.getElementById('loading').classList.remove('active');
    }
}

function renderResults(data) {
    const results = document.getElementById('results');
    results.classList.add('active');

    // Error
    const errC = document.getElementById('error-container');
    if (data.error) {
        errC.innerHTML = '<div class="error-box">' + esc(data.error) + '</div>';
    } else {
        errC.innerHTML = '';
    }

    // Products (primary focus)
    const prodsEl = document.getElementById('products');
    const count = (data.products || []).length;
    document.getElementById('product-count').textContent = count;

    if (count) {
        prodsEl.innerHTML = data.products.map(p => {
            const tipo = (p.tipo || '').replace('_', ' ');
            const meta = [
                p.escala ? 'Escala: ' + p.escala : null,
                p.data_produto ? 'Data: ' + p.data_produto : null,
                p.resolucao_m ? 'Res: ' + p.resolucao_m + 'm' : null,
                p.articulacao ? 'MI: ' + p.articulacao : null,
            ].filter(Boolean).join(' | ');
            return '<div class="product-card">' +
                '<span class="product-name">' + esc(p.nome || '?') + '</span>' +
                '<span class="product-type">' + esc(tipo) + '</span>' +
                '<span class="product-meta">' + esc(meta) + '</span>' +
            '</div>';
        }).join('');
    } else {
        prodsEl.innerHTML = '<p class="no-products">Nenhum produto encontrado para esta busca.</p>';
    }

    // Answer (collapsible)
    document.getElementById('answer').textContent = data.answer || '(sem resposta)';

    // Steps (collapsible)
    const stepsEl = document.getElementById('steps');
    const stepCount = (data.steps || []).length;
    document.getElementById('step-count').textContent = stepCount;

    if (stepCount) {
        stepsEl.innerHTML = data.steps.map(s =>
            '<div class="step">' +
                '<div class="step-num">' + s.step + '</div>' +
                '<span class="step-tool">' + esc(s.tool) + '</span>' +
                '<span class="step-desc">' + esc(s.description) + '</span>' +
                '<span class="step-detail">' + esc(s.detail) + '</span>' +
            '</div>'
        ).join('');
    } else {
        stepsEl.innerHTML = '<p style="color:#999;font-size:0.9em">Nenhuma tool chamada</p>';
    }

    // Metrics (collapsible)
    if (data.metrics) {
        const m = data.metrics;
        document.getElementById('metrics').innerHTML =
            '<span>Tempo: ' + (m.duration_ms/1000).toFixed(1) + 's</span>' +
            '<span>Tokens: ' + m.total_tokens.toLocaleString('pt-BR') + '</span>' +
            '<span>Iterações: ' + m.iterations + '</span>';
    }
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
}
</script>
</body>
</html>
"""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Geoportal search interface")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--provider", type=str, default=None)
    parser.add_argument("--model", type=str, default=None)
    args = parser.parse_args()

    global _client, _provider_config, _model, _provider_id

    if args.provider:
        _provider_id = args.provider
        _client, _provider_config = create_client(_provider_id)

    if args.model:
        _model = args.model

    print(f"\nGeoportal Search - http://localhost:{args.port}", flush=True)
    print(f"Provider: {PROVIDERS[_provider_id].name} | Model: {_model}\n", flush=True)
    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
