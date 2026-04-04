"""Web interface with SSE streaming for the geoportal spatial reasoning agent."""

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


_TOOL_MESSAGES = {
    "tool_start": {
        "geocode": lambda a: f'Geocodificando "{a.get("place_name", "")}"...',
        "search_municipality": lambda a: f'Buscando município "{a.get("nome", "")}"...',
        "search_state": lambda a: f'Buscando estado "{a.get("uf", "")}"...',
        "search_named_region": lambda a: f'Buscando região "{a.get("nome", "")}"...',
        "search_products": lambda a: f'Buscando produtos (tipo={a.get("tipo", "*")})...',
        "buffer": lambda a: f'Criando buffer de {a.get("raio_metros", "?")}m...',
        "compute_route": lambda a: "Calculando rota rodoviária...",
        "search_hydrography": lambda a: f'Buscando hidrografia "{a.get("nome", "")}"...',
        "search_border": lambda a: f'Buscando fronteira com "{a.get("pais", "")}"...',
        "search_military_installation": lambda a: f'Buscando instalação militar "{a.get("nome_ou_sigla", "")}"...',
        "search_features": lambda a: f'Buscando feições ({a.get("tipo", "?")})...',
        "intersect": lambda a: "Calculando interseção...",
        "compute_distance": lambda a: "Calculando distância...",
        "compute_area": lambda a: "Calculando área...",
        "compute_length": lambda a: "Calculando comprimento...",
        "find_nearest": lambda a: f'Buscando {a.get("tipo", "?")} mais próximo...',
        "features_along_route": lambda a: f'Buscando {a.get("tipo", "?")} ao longo da rota...',
        "check_intersection": lambda a: "Verificando interseção...",
        "search_road": lambda a: f'Buscando rodovia "{a.get("identificador", "")}"...',
        "list_municipalities_in": lambda a: "Listando municípios na área...",
    },
    "tool_result": {
        "geocode": lambda a, r: f'{r.get("display_name", "?")} ({r.get("lat", "?")}, {r.get("lon", "?")})',
        "search_municipality": lambda a, r: f'{r["nome"]}/{r.get("uf", "?")} (pop. {r.get("populacao", "?"):,})' if "nome" in r else r.get("error", "Não encontrado"),
        "search_state": lambda a, r: f'Estado {r.get("nome", "?")}',
        "search_named_region": lambda a, r: f'Região {r.get("nome", "?")}' if "geometry_ref" in r else r.get("error", "?"),
        "search_products": lambda a, r: f'{r.get("total", 0)} produto(s)',
        "buffer": lambda a, r: "Área expandida",
        "compute_route": lambda a, r: f'{r.get("distance_km", "?")} km, ~{r.get("duration_min", "?")} min',
        "search_hydrography": lambda a, r: f'{r.get("nome", "?")} ({r.get("tipo", "?")})' if "nome" in r else r.get("error", "?"),
        "search_border": lambda a, r: f'Fronteira com {r.get("pais", "?")}' if "pais" in r else r.get("error", "?"),
        "search_military_installation": lambda a, r: f'{r.get("sigla", "?")} — {r.get("cidade", "?")}/{r.get("uf", "?")}' if "sigla" in r else r.get("error", "?"),
        "search_features": lambda a, r: f'{r.get("total", 0)} {a.get("tipo", "feição")}(s)',
        "intersect": lambda a, r: f'Área: {r.get("area_km2", "?")} km²' if not r.get("is_empty") else "Sem interseção",
        "compute_distance": lambda a, r: f'{r.get("distance_km", "?")} km',
        "compute_area": lambda a, r: f'{r.get("area_km2", "?")} km²',
        "compute_length": lambda a, r: f'{r.get("length_km", "?")} km',
        "find_nearest": lambda a, r: f'{r.get("total", 0)} resultado(s)' + (f' — mais próximo: {r["nearest"][0]["nome"]} ({r["nearest"][0]["distance_km"]} km)' if r.get("nearest") else ""),
        "features_along_route": lambda a, r: f'{r.get("total", 0)} {a.get("tipo", "feição")}(s) na rota',
        "check_intersection": lambda a, r: "Sim, interceptam" if r.get("intersects") else "Não interceptam",
        "search_road": lambda a, r: f'{r.get("nome", "?")} — {r.get("extensao_km", "?")} km' if "nome" in r else r.get("error", "?"),
        "list_municipalities_in": lambda a, r: f'{r.get("total", 0)} município(s)',
    },
}


def _format_tool_message(event_type: str, tool: str, args: dict, result: dict | None = None) -> str:
    handlers = _TOOL_MESSAGES.get(event_type, {})
    handler = handlers.get(tool)
    if handler:
        try:
            return handler(args, result) if event_type == "tool_result" else handler(args)
        except Exception:
            pass
    if event_type == "tool_start":
        return f"Executando {tool}..."
    return json.dumps(result or {}, ensure_ascii=False)[:100]


@app.route("/")
def index():
    resp = Response(SEARCH_HTML, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query vazia"}), 400

    result = run_agent(query, client=_client, model=_model, provider_config=_provider_config)

    return jsonify({
        "answer": result.answer,
        "trace": result.trace,
        "metrics": {"iterations": result.iterations, "duration_ms": result.duration_ms, "total_tokens": result.total_tokens},
        "error": result.error,
    })


@app.route("/api/search-stream", methods=["POST"])
def search_stream():
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

            # Extract all features from trace with geometry for map
            gs = result._geometry_store
            all_features = []
            seen_feat = set()
            for step in result.trace:
                tool = step["tool"]
                res = step.get("result", {})
                feat_list = res.get("features") or res.get("nearest") or []
                if tool in ("search_features", "features_along_route", "find_nearest") and feat_list:
                    tipo = step.get("args", {}).get("tipo", "")
                    for f in feat_list:
                        key = f.get("nome", "")
                        if key not in seen_feat:
                            seen_feat.add(key)
                            f_copy = dict(f)
                            f_copy["_tipo"] = tipo
                            # Attach geometry for map
                            ref = f.get("geometry_ref", "")
                            if gs and ref:
                                try:
                                    f_copy["_geometry"] = gs.get(ref)
                                except KeyError:
                                    pass
                            all_features.append(f_copy)

            q.put({
                "type": "final",
                "answer": result.answer,
                "products": products,
                "features": all_features,
                "metrics": {"iterations": result.iterations, "duration_ms": result.duration_ms, "total_tokens": result.total_tokens},
                "error": result.error,
            })
        except Exception as e:
            q.put({"type": "final", "answer": "", "products": [], "features": [], "metrics": {}, "error": str(e)})
        finally:
            q.put(None)

    threading.Thread(target=run_in_thread, daemon=True).start()

    def generate():
        while True:
            event = q.get()
            if event is None:
                break
            if event["type"] == "tool_start":
                event["message"] = _format_tool_message("tool_start", event["tool"], event["args"])
            elif event["type"] == "tool_result":
                event["message"] = _format_tool_message("tool_result", event["tool"], event["args"], event["result"])
            elif event["type"] == "retry":
                event["message"] = "Aguardando... tentando novamente"
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


SEARCH_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Geoportal — Assistente Espacial</title>
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css">
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; color: #1a1a2e; }

.layout { display: flex; height: 100vh; }
.panel { width: 480px; min-width: 380px; overflow-y: auto; padding: 20px; border-right: 1px solid #ddd; background: #fff; display: flex; flex-direction: column; }
.map-container { flex: 1; position: relative; }
#map { width: 100%; height: 100%; }

h1 { font-size: 1.2em; margin-bottom: 16px; color: #1a5632; }

.search-box { display: flex; gap: 8px; margin-bottom: 16px; }
.search-box input {
    flex: 1; padding: 10px 14px; font-size: 0.95em; border: 2px solid #ddd;
    border-radius: 8px; outline: none; transition: border 0.2s;
}
.search-box input:focus { border-color: #1a5632; }
.search-box button {
    padding: 10px 20px; background: #1a5632; color: white; border: none;
    border-radius: 8px; font-size: 0.95em; cursor: pointer; white-space: nowrap;
}
.search-box button:hover { background: #2d7a4a; }
.search-box button:disabled { background: #999; cursor: wait; }

/* Feed */
.feed { margin-bottom: 12px; flex-shrink: 0; }
.feed-item {
    display: flex; align-items: flex-start; gap: 8px;
    padding: 5px 0; animation: fadeIn 0.3s ease-in; font-size: 0.85em;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; } }
.feed-icon { width: 18px; height: 18px; flex-shrink: 0; margin-top: 1px; display: flex; align-items: center; justify-content: center; }
.feed-icon.spinner { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.feed-icon svg { width: 14px; height: 14px; }
.feed-text { color: #555; }
.feed-text.muted { color: #999; font-size: 0.9em; }

/* Answer */
.answer-section { margin-bottom: 12px; }
.answer-box {
    background: #f8faf8; border-radius: 8px; padding: 12px 14px;
    border-left: 3px solid #1a5632; line-height: 1.55; font-size: 0.9em;
    white-space: pre-wrap; word-wrap: break-word;
}

/* Thoughts */
.thought-block {
    background: #f0f0f0; border-radius: 6px; padding: 8px 10px; margin: 6px 0;
    font-size: 0.82em; color: #666; cursor: pointer; border-left: 3px solid #ccc;
}
.thought-block summary { color: #888; font-size: 0.9em; }
.thought-content { margin-top: 4px; white-space: pre-wrap; }

/* Results cards */
.results-section { margin-bottom: 12px; }
.results-section h2 { font-size: 0.9em; color: #666; margin-bottom: 6px; }
.result-card {
    background: #f8f9fa; border-radius: 6px; padding: 8px 12px;
    margin-bottom: 4px; font-size: 0.85em; display: flex; justify-content: space-between; align-items: center;
}
.result-card .name { font-weight: 600; }
.result-card .badge {
    font-size: 0.75em; padding: 2px 8px; border-radius: 10px;
    background: #e3f2fd; color: #1565c0; white-space: nowrap;
}
.result-card .badge.feature { background: #e8f5e9; color: #2e7d32; }
.result-card .meta { font-size: 0.8em; color: #888; }

.no-results { color: #999; font-size: 0.85em; font-style: italic; }

/* Collapsible */
details { margin-bottom: 6px; }
details summary { cursor: pointer; font-size: 0.85em; color: #888; padding: 4px 0; user-select: none; }

.metrics { display: flex; gap: 14px; font-size: 0.78em; color: #aaa; margin-top: 4px; }

.map-btn {
    background: none; border: 1px solid #ccc; border-radius: 4px; cursor: pointer;
    padding: 3px 6px; margin-left: 4px; flex-shrink: 0;
    opacity: 0.6; transition: opacity 0.2s, border-color 0.2s;
    display: inline-flex; align-items: center; justify-content: center;
    color: #1a5632;
}
.map-btn:hover { opacity: 1; border-color: #1a5632; }

.error-box {
    background: #fff3f3; border-left: 3px solid #d32f2f; border-radius: 6px;
    padding: 10px 14px; margin-bottom: 10px; color: #b71c1c; font-size: 0.85em;
}
</style>
</head>
<body>
<div class="layout">
    <div class="panel">
        <h1>Geoportal — Assistente Espacial</h1>

        <div class="search-box">
            <input type="text" id="query" placeholder="Pergunte sobre geografia, infraestrutura, rotas..."
                   autofocus autocomplete="off">
            <button id="btn" onclick="doSearch()">Buscar</button>
        </div>

        <div class="feed" id="feed"></div>

        <div id="results" style="display:none">
            <div id="error-container"></div>

            <div class="answer-section" id="answer-section" style="display:none">
                <div class="answer-box" id="answer"></div>
            </div>

            <div class="results-section" id="features-section" style="display:none">
                <h2 id="features-title">Feições encontradas</h2>
                <div id="features-list"></div>
            </div>

            <div class="results-section" id="products-section" style="display:none">
                <h2>Produtos encontrados (<span id="product-count">0</span>)</h2>
                <div id="products-list"></div>
            </div>

            <details>
                <summary>Consumo</summary>
                <div class="metrics" id="metrics"></div>
            </details>
        </div>
    </div>
    <div class="map-container">
        <div id="map"></div>
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
const SVG_PIN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>';

// Map setup
const map = new maplibregl.Map({
    container: 'map',
    style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
    center: [-53.5, -30.0],
    zoom: 5.5,
});
map.addControl(new maplibregl.NavigationControl(), 'top-right');
let mapMarkers = [];
let mapSources = [];

function clearMap() {
    mapMarkers.forEach(m => m.remove());
    mapMarkers = [];
    mapSources.forEach(id => {
        if (map.getLayer(id)) map.removeLayer(id);
        if (map.getSource(id)) map.removeSource(id);
    });
    mapSources = [];
}

const FEATURE_COLORS = {
    ponte: '#e65100', hospital: '#c62828', escola: '#1565c0', aeroporto: '#6a1b9a',
    torre_comunicacao: '#ef6c00', aerogerador: '#00838f', heliporto: '#7b1fa2',
    campo_pouso: '#4527a0', posto_combustivel: '#2e7d32', barragem: '#01579b',
    estacao_ferroviaria: '#4e342e', terra_indigena: '#33691e', edificacao_destaque: '#37474f',
    geocode: '#1a5632', route: '#1565c0', road: '#e65100',
};

function addToMap(geojsonFeatures) {
    if (!geojsonFeatures || !geojsonFeatures.length) return;

    const bounds = new maplibregl.LngLatBounds();
    let hasPoints = false;

    geojsonFeatures.forEach((feat, i) => {
        const props = feat.properties || {};
        const geomType = feat.geometry?.type;
        const color = FEATURE_COLORS[props.type] || '#666';

        if (geomType === 'Point') {
            const [lng, lat] = feat.geometry.coordinates;
            bounds.extend([lng, lat]);
            hasPoints = true;

            const el = document.createElement('div');
            el.style.cssText = `width:12px;height:12px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,.3);cursor:pointer;`;

            const popup = new maplibregl.Popup({offset: 12, maxWidth: '260px'})
                .setHTML(`<strong>${esc(props.name)}</strong><br><span style="color:#888;font-size:0.85em">${esc(props.type || '')}</span>`
                    + Object.entries(props).filter(([k]) => !['name','type','icon'].includes(k)).map(([k,v]) => `<br><span style="font-size:0.82em">${k}: ${v}</span>`).join(''));

            const marker = new maplibregl.Marker({element: el}).setLngLat([lng, lat]).setPopup(popup).addTo(map);
            mapMarkers.push(marker);

        } else if (geomType === 'LineString') {
            const srcId = 'line-' + i;
            map.addSource(srcId, {type: 'geojson', data: feat});
            map.addLayer({
                id: srcId, type: 'line', source: srcId,
                paint: {'line-color': color, 'line-width': props.type === 'route' ? 4 : 3, 'line-opacity': 0.8},
            });
            mapSources.push(srcId);
            feat.geometry.coordinates.forEach(c => bounds.extend(c));
            hasPoints = true;

        } else if (geomType === 'Polygon') {
            const srcId = 'poly-' + i;
            map.addSource(srcId, {type: 'geojson', data: feat});
            map.addLayer({
                id: srcId, type: 'fill', source: srcId,
                paint: {'fill-color': color, 'fill-opacity': 0.15},
            });
            map.addLayer({
                id: srcId + '-outline', type: 'line', source: srcId,
                paint: {'line-color': color, 'line-width': 2},
            });
            mapSources.push(srcId, srcId + '-outline');
            feat.geometry.coordinates[0]?.forEach(c => bounds.extend(c));
            hasPoints = true;
        }
    });

    if (hasPoints) {
        map.fitBounds(bounds, {padding: 60, maxZoom: 12});
    }
}

let loadedOnMap = new Set();

function zoomToGeometry(geom) {
    const bounds = new maplibregl.LngLatBounds();
    if (geom.type === 'Point') {
        map.flyTo({center: geom.coordinates, zoom: 12});
        return;
    }
    const coords = geom.type === 'LineString' ? geom.coordinates : (geom.coordinates[0] || []);
    coords.forEach(c => bounds.extend(c));
    map.fitBounds(bounds, {padding: 60, maxZoom: 13});
}

function addFeedItem(html, iconHtml, mapFeatures) {
    const item = document.createElement('div');
    item.className = 'feed-item';
    let btnHtml = '';
    if (mapFeatures && mapFeatures.length) {
        btnHtml = `<button class="map-btn" title="Ver no mapa">${SVG_PIN}</button>`;
    }
    item.innerHTML = `<div class="feed-icon${iconHtml === SVG_SPINNER ? ' spinner' : ''}">${iconHtml}</div><div class="feed-text">${html}</div>${btnHtml}`;
    if (mapFeatures && mapFeatures.length) {
        item.querySelector('.map-btn').addEventListener('click', () => {
            const toAdd = mapFeatures.filter(f => {
                const key = f.properties?.name || JSON.stringify(f.geometry?.coordinates);
                if (loadedOnMap.has(key)) return false;
                loadedOnMap.add(key);
                return true;
            });
            if (toAdd.length) addToMap(toAdd);
        });
    }
    feed.appendChild(item);
    item.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    return item;
}

function finishLastSpinner(msg, mapFeatures) {
    const items = feed.querySelectorAll('.feed-item');
    if (!items.length) return;
    const last = items[items.length - 1];
    const icon = last.querySelector('.feed-icon');
    if (icon?.classList.contains('spinner')) {
        icon.classList.remove('spinner');
        icon.innerHTML = SVG_CHECK;
    }
    if (msg) {
        const detail = document.createElement('div');
        detail.className = 'feed-text muted';
        detail.textContent = msg;
        last.appendChild(detail);
    }
    if (mapFeatures && mapFeatures.length) {
        const btn = document.createElement('button');
        btn.className = 'map-btn';
        btn.title = 'Ver no mapa';
        btn.innerHTML = SVG_PIN;
        btn.addEventListener('click', () => {
            const toAdd = mapFeatures.filter(f => {
                const key = f.properties?.name || JSON.stringify(f.geometry?.coordinates);
                if (loadedOnMap.has(key)) return false;
                loadedOnMap.add(key);
                return true;
            });
            if (toAdd.length) addToMap(toAdd);
        });
        last.appendChild(btn);
    }
}

function formatAnswer(text) {
    // Replace <thought>...</thought> with collapsible blocks
    return text.replace(/<thought>([\s\S]*?)<\/thought>/gi, (_, content) => {
        return `<details class="thought-block"><summary>Raciocínio do modelo</summary><div class="thought-content">${esc(content.trim())}</div></details>`;
    });
}

async function doSearch() {
    const query = input.value.trim();
    if (!query) return;

    btn.disabled = true;
    feed.innerHTML = '';
    document.getElementById('results').style.display = 'none';
    clearMap();
    loadedOnMap = new Set();

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
            const lines = buffer.split('\n');
            buffer = lines.pop();
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try { handleEvent(JSON.parse(line.slice(6))); } catch(e) {}
            }
        }
    } catch (e) {
        addFeedItem('Erro de conexão: ' + esc(e.message), SVG_WARN);
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
            finishLastSpinner(ev.message, ev.map_features);
            break;
        case 'retry':
            addFeedItem(esc(ev.message), SVG_WARN);
            break;
        case 'done':
            finishLastSpinner();
            break;
        case 'final':
            renderResults(ev);
            break;
    }
}

function renderResults(data) {
    const results = document.getElementById('results');
    results.style.display = 'block';

    // Error
    const errC = document.getElementById('error-container');
    if (data.error) {
        errC.innerHTML = `<div class="error-box">${esc(data.error)}</div>`;
    } else {
        errC.innerHTML = '';
    }

    // Answer
    const answerSection = document.getElementById('answer-section');
    const answerEl = document.getElementById('answer');
    if (data.answer) {
        answerSection.style.display = 'block';
        answerEl.innerHTML = formatAnswer(data.answer);
    } else {
        answerSection.style.display = 'none';
    }

    // Features
    const featSection = document.getElementById('features-section');
    const featList = document.getElementById('features-list');
    const feats = data.features || [];
    if (feats.length) {
        featSection.style.display = 'block';
        document.getElementById('features-title').textContent = `Feições encontradas (${feats.length})`;
        featList.innerHTML = '';
        feats.forEach((f, i) => {
            const tipo = (f._tipo || '').replace('_', ' ');
            const attrs = Object.entries(f)
                .filter(([k]) => !['nome','geometry_ref','_tipo','_geometry'].includes(k))
                .map(([k,v]) => `${k}: ${v}`).join(' | ');
            const card = document.createElement('div');
            card.className = 'result-card';
            const hasGeo = !!f._geometry;
            card.innerHTML = `<div><span class="name">${esc(f.nome || '?')}</span>
                ${attrs ? `<div class="meta">${esc(attrs)}</div>` : ''}</div>
                <div style="display:flex;align-items:center;gap:6px">
                    ${hasGeo ? `<button class="map-btn" data-feat-idx="${i}" title="Ver no mapa">${SVG_PIN}</button>` : ''}
                    <span class="badge feature">${esc(tipo)}</span>
                </div>`;
            if (hasGeo) {
                card.querySelector('.map-btn').addEventListener('click', () => {
                    const key = f.nome || i;
                    if (loadedOnMap.has(key)) {
                        // Already loaded — just zoom to it
                        zoomToGeometry(f._geometry);
                        return;
                    }
                    loadedOnMap.add(key);
                    const geojson = {
                        type: 'Feature',
                        geometry: f._geometry,
                        properties: {name: f.nome || '', type: f._tipo || 'feature'}
                    };
                    addToMap([geojson]);
                });
            }
            featList.appendChild(card);
        });
    } else {
        featSection.style.display = 'none';
    }

    // Products
    const prodSection = document.getElementById('products-section');
    const prodList = document.getElementById('products-list');
    const prods = data.products || [];
    document.getElementById('product-count').textContent = prods.length;
    if (prods.length) {
        prodSection.style.display = 'block';
        prodList.innerHTML = prods.map(p => {
            const tipo = (p.tipo || '').replace('_', ' ');
            const meta = [p.escala, p.data_produto, p.resolucao_m ? `${p.resolucao_m}m` : null, p.articulacao].filter(Boolean).join(' | ');
            return `<div class="result-card">
                <div><span class="name">${esc(p.nome || '?')}</span>
                ${meta ? `<div class="meta">${esc(meta)}</div>` : ''}</div>
                <span class="badge">${esc(tipo)}</span>
            </div>`;
        }).join('');
    } else {
        prodSection.style.display = 'none';
    }

    // Metrics
    if (data.metrics?.duration_ms) {
        document.getElementById('metrics').innerHTML =
            `<span>Tempo: ${(data.metrics.duration_ms/1000).toFixed(1)}s</span>` +
            `<span>Tokens: ${(data.metrics.total_tokens || 0).toLocaleString('pt-BR')}</span>` +
            `<span>Iterações: ${data.metrics.iterations || 0}</span>`;
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
    parser = argparse.ArgumentParser(description="Geoportal spatial reasoning interface")
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

    print(f"\nGeoportal — Assistente Espacial", flush=True)
    print(f"http://localhost:{args.port}", flush=True)
    print(f"Provider: {PROVIDERS[_provider_id].name} | Model: {_model}\n", flush=True)
    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
