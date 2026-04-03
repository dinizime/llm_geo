"""Web interface with SSE streaming for the geoportal search agent."""

import json
import sys
import threading
import queue

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

from .agent import run_agent
from .providers import PROVIDERS, create_client, detect_provider, get_default_model

app = Flask(__name__)

_provider_id = detect_provider()
_client, _provider_config = create_client(_provider_id)
_model = get_default_model(_provider_id)

print(f"Provider: {PROVIDERS[_provider_id].name}", flush=True)
print(f"Model: {_model}", flush=True)


def _format_tool_message(event_type: str, tool: str, args: dict, result: dict | None = None) -> str:
    """Build a human-readable message for a tool event."""
    if event_type == "tool_start":
        if tool == "geocode":
            return f"Geocodificando \"{args.get('place_name', '')}\"..."
        elif tool == "search_municipality":
            return f"Buscando munic\u00edpio \"{args.get('nome', '')}\"..."
        elif tool == "search_state":
            return f"Buscando estado \"{args.get('uf', '')}\"..."
        elif tool == "search_named_region":
            return f"Buscando regi\u00e3o \"{args.get('nome', '')}\"..."
        elif tool == "search_products":
            tipo = args.get('tipo', '*')
            return f"Buscando produtos (tipo={tipo})..."
        elif tool == "buffer":
            return f"Criando buffer de {args.get('raio_metros', '?')}m..."
        elif tool == "compute_route":
            return "Calculando rota rodovi\u00e1ria..."
        elif tool == "search_hydrography":
            return f"Buscando hidrografia \"{args.get('nome', '')}\"..."
        elif tool == "search_border":
            return f"Buscando fronteira com \"{args.get('pais', '')}\"..."
        elif tool == "search_military_installation":
            return f"Buscando instala\u00e7\u00e3o militar \"{args.get('nome_ou_sigla', '')}\"..."
        elif tool == "search_features":
            return f"Buscando fei\u00e7\u00f5es ({args.get('tipo', '?')})..."
        elif tool == "intersect":
            return "Calculando interse\u00e7\u00e3o..."
        elif tool == "rank_by_scale":
            return "Ordenando por escala..."
        elif tool == "rank_by_date":
            return "Ordenando por data..."
        elif tool == "autocomplete_placename":
            return f"Autocompletando \"{args.get('fragmento', '')}\"..."
        elif tool == "explain_product_type":
            return f"Explicando tipo \"{args.get('tipo', '')}\"..."
        return f"Executando {tool}..."

    # tool_result
    if tool == "geocode":
        return f"Encontrado: {result.get('display_name', '?')} ({result.get('lat', '?')}, {result.get('lon', '?')})"
    elif tool == "search_municipality":
        if 'nome' in result:
            return f"{result['nome']}/{result.get('uf', '?')} (pop. {result.get('populacao', '?'):,})"
        return result.get('error', 'N\u00e3o encontrado')
    elif tool == "search_state":
        return "Pol\u00edgono do estado obtido"
    elif tool == "search_named_region":
        return "Regi\u00e3o encontrada" if 'geometry_ref' in result else result.get('error', '?')
    elif tool == "search_products":
        total = result.get('total', 0)
        return f"{total} produto(s) encontrado(s)"
    elif tool == "buffer":
        return "\u00c1rea de busca expandida"
    elif tool == "compute_route":
        return f"Rota: {result.get('distance_km', '?')}km, ~{result.get('duration_min', '?')}min"
    elif tool == "search_hydrography":
        if 'nome' in result:
            return f"Encontrado: {result['nome']} ({result.get('tipo', '?')})"
        return result.get('error', '?')
    elif tool == "search_border":
        return f"Fronteira com {result.get('pais', '?')}" if 'pais' in result else result.get('error', '?')
    elif tool == "search_military_installation":
        return f"Encontrado: {result.get('nome', '?')}" if 'nome' in result else result.get('error', '?')
    elif tool == "search_features":
        return f"{len(result.get('features', []))} fei\u00e7\u00e3o(\u00f5es) encontrada(s)"
    elif tool == "intersect":
        return f"\u00c1rea: {result.get('area_km2', '?')} km\u00b2"
    elif tool == "rank_by_scale" or tool == "rank_by_date":
        return "Produtos reordenados"
    elif tool == "autocomplete_placename":
        return f"{len(result.get('candidates', []))} sugest\u00e3o(\u00f5es)"
    elif tool == "explain_product_type":
        return result.get('explanation', '?')[:120]
    return json.dumps(result, ensure_ascii=False)[:100]


@app.route("/")
def index():
    return SEARCH_HTML


@app.route("/api/search", methods=["POST"])
def search():
    """Non-streaming endpoint (kept for compatibility)."""
    data = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query vazia"}), 400

    result = run_agent(query, client=_client, model=_model, provider_config=_provider_config)

    products = []
    seen = set()
    for step in result.trace:
        if step["tool"] == "search_products":
            for p in step["result"].get("products", []):
                pid = p.get("id")
                if pid and pid not in seen:
                    seen.add(pid)
                    products.append(p)

    return jsonify({
        "answer": result.answer,
        "products": products,
        "trace": result.trace,
        "metrics": {"iterations": result.iterations, "duration_ms": result.duration_ms, "total_tokens": result.total_tokens},
        "error": result.error,
    })


@app.route("/api/search-stream", methods=["POST"])
def search_stream():
    """SSE streaming endpoint — emits events as the agent progresses."""
    data = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query vazia"}), 400

    q = queue.Queue()

    def on_event(event):
        q.put(event)

    def run_in_thread():
        try:
            result = run_agent(query, client=_client, model=_model, provider_config=_provider_config, on_event=on_event)
            # Extract products
            products = []
            seen = set()
            for step in result.trace:
                if step["tool"] == "search_products":
                    for p in step["result"].get("products", []):
                        pid = p.get("id")
                        if pid and pid not in seen:
                            seen.add(pid)
                            products.append(p)
            q.put({
                "type": "final",
                "answer": result.answer,
                "products": products,
                "metrics": {"iterations": result.iterations, "duration_ms": result.duration_ms, "total_tokens": result.total_tokens},
                "error": result.error,
            })
        except Exception as e:
            q.put({"type": "final", "answer": "", "products": [], "metrics": {}, "error": str(e)})
        finally:
            q.put(None)  # sentinel

    threading.Thread(target=run_in_thread, daemon=True).start()

    def generate():
        while True:
            event = q.get()
            if event is None:
                break
            # Add human-readable message for tool events
            if event["type"] == "tool_start":
                event["message"] = _format_tool_message("tool_start", event["tool"], event["args"])
            elif event["type"] == "tool_result":
                event["message"] = _format_tool_message("tool_result", event["tool"], event["args"], event["result"])
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
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

/* Progress feed */
.feed { margin-bottom: 20px; }
.feed-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 8px 0; animation: fadeIn 0.3s ease-in;
    font-size: 0.9em;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
.feed-icon {
    width: 20px; height: 20px; flex-shrink: 0; margin-top: 1px;
    display: flex; align-items: center; justify-content: center;
}
.feed-icon.spinner { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.feed-icon svg { width: 16px; height: 16px; }
.feed-text { color: #444; }
.feed-text.muted { color: #999; font-size: 0.85em; }
.feed-item.retry .feed-text { color: #b36b00; }

/* Results */
.results { display: none; animation: fadeIn 0.4s ease-in; }
.results.active { display: block; }

/* Products */
.products-section { margin-bottom: 16px; }
.products-section h2 { font-size: 1em; color: #444; margin-bottom: 10px; }
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

/* Collapsible */
details { margin-bottom: 8px; }
details summary {
    cursor: pointer; font-size: 0.88em; color: #888; padding: 6px 0;
    user-select: none; list-style: none;
}
details summary::-webkit-details-marker { display: none; }
details summary::before {
    content: '\\25B6'; display: inline-block; margin-right: 8px;
    font-size: 0.65em; transition: transform 0.2s;
}
details[open] summary::before { transform: rotate(90deg); }
.answer-box {
    background: white; border-radius: 10px; padding: 14px 18px;
    margin-top: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border-left: 4px solid #1a5632; white-space: pre-wrap; line-height: 1.5; font-size: 0.9em;
}
.metrics { display: flex; gap: 16px; margin-top: 6px; font-size: 0.8em; color: #aaa; }

/* Error */
.error-box {
    background: #fff3f3; border-left: 4px solid #d32f2f; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 16px; color: #b71c1c; font-size: 0.9em;
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

    <div class="feed" id="feed"></div>

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
            <summary>Consumo</summary>
            <div class="metrics" id="metrics" style="margin-top:6px"></div>
        </details>
    </div>
</div>

<script>
const input = document.getElementById('query');
const btn = document.getElementById('btn');
const feed = document.getElementById('feed');
input.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });

const SVG_SPINNER = '<svg viewBox="0 0 24 24" fill="none" stroke="#1a5632" stroke-width="2.5"><circle cx="12" cy="12" r="10" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg>';
const SVG_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="#2e7d32" stroke-width="2.5"><path d="M5 13l4 4L19 7"/></svg>';
const SVG_WARN = '<svg viewBox="0 0 24 24" fill="none" stroke="#b36b00" stroke-width="2.5"><path d="M12 9v4m0 4h.01M12 3l9.5 16.5H2.5z"/></svg>';

function addFeedItem(html, iconHtml, cssClass) {
    const item = document.createElement('div');
    item.className = 'feed-item' + (cssClass ? ' ' + cssClass : '');
    item.innerHTML = '<div class="feed-icon' + (iconHtml === SVG_SPINNER ? ' spinner' : '') + '">' + iconHtml + '</div>' +
                     '<div class="feed-text">' + html + '</div>';
    feed.appendChild(item);
    item.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    return item;
}

function finishLastSpinner(msg) {
    const items = feed.querySelectorAll('.feed-item');
    if (!items.length) return;
    const last = items[items.length - 1];
    const icon = last.querySelector('.feed-icon');
    if (icon && icon.classList.contains('spinner')) {
        icon.classList.remove('spinner');
        icon.innerHTML = SVG_CHECK;
    }
    if (msg) {
        const detail = document.createElement('div');
        detail.className = 'feed-text muted';
        detail.textContent = msg;
        last.appendChild(detail);
    }
}

async function doSearch() {
    const query = input.value.trim();
    if (!query) return;

    btn.disabled = true;
    feed.innerHTML = '';
    document.getElementById('results').classList.remove('active');

    try {
        const res = await fetch('/api/search-stream', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query})
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, {stream: true});
            const lines = buffer.split('\\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const data = JSON.parse(line.slice(6));
                handleEvent(data);
            }
        }
    } catch (e) {
        addFeedItem('Erro de conexão: ' + esc(e.message), SVG_WARN, 'retry');
    } finally {
        btn.disabled = false;
    }
}

function handleEvent(ev) {
    switch (ev.type) {
        case 'thinking':
            finishLastSpinner();
            addFeedItem(esc(ev.message), SVG_SPINNER);
            break;

        case 'tool_start':
            finishLastSpinner();
            addFeedItem(esc(ev.message), SVG_SPINNER);
            break;

        case 'tool_result':
            finishLastSpinner(ev.message);
            break;

        case 'retry':
            addFeedItem(esc(ev.message), SVG_WARN, 'retry');
            break;

        case 'done':
            finishLastSpinner();
            break;

        case 'final':
            renderFinalResults(ev);
            break;
    }
}

function renderFinalResults(data) {
    const results = document.getElementById('results');
    results.classList.add('active');

    // Error
    const errC = document.getElementById('error-container');
    if (data.error) {
        errC.innerHTML = '<div class="error-box">' + esc(data.error) + '</div>';
    } else {
        errC.innerHTML = '';
    }

    // Products
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

    // Answer
    document.getElementById('answer').textContent = data.answer || '(sem resposta)';

    // Metrics
    if (data.metrics && data.metrics.duration_ms) {
        document.getElementById('metrics').innerHTML =
            '<span>Tempo: ' + (data.metrics.duration_ms/1000).toFixed(1) + 's</span>' +
            '<span>Tokens: ' + (data.metrics.total_tokens || 0).toLocaleString('pt-BR') + '</span>' +
            '<span>Iterações: ' + (data.metrics.iterations || 0) + '</span>';
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
