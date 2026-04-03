"""Generate static HTML report from benchmark results in PostgreSQL.

Usage:
    python -m llm_tool_calling.report
    # Opens reports/index.html
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from .db import (
    get_all_results,
    get_all_runs,
    get_category_breakdown,
    get_comparison_summary,
    get_difficulty_breakdown,
    init_db,
)

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__float__"):
        return float(obj)
    return str(obj)


def generate_report():
    init_db()

    runs = get_all_runs()
    if not runs:
        print("No benchmark runs found. Run a benchmark first.")
        sys.exit(1)

    results = get_all_results()
    summary = get_comparison_summary()
    category_data = get_category_breakdown()
    difficulty_data = get_difficulty_breakdown()

    REPORTS_DIR.mkdir(exist_ok=True)

    data = {
        "generated_at": datetime.now().isoformat(),
        "runs": runs,
        "results": results,
        "summary": summary,
        "category_breakdown": category_data,
        "difficulty_breakdown": difficulty_data,
    }

    data_json = json.dumps(data, default=json_serial, ensure_ascii=False)

    html = HTML_TEMPLATE.replace("__DATA_JSON__", data_json)
    out_path = REPORTS_DIR / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Report generated: {out_path.resolve()}")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM Tool Calling Benchmark</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
:root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --text: #e1e4ed;
    --muted: #8b8fa3;
    --pass: #22c55e;
    --fail: #ef4444;
    --warn: #f59e0b;
    --accent: #6366f1;
    --accent2: #06b6d4;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
    background: var(--bg); color: var(--text);
    padding: 20px; line-height: 1.5;
}
h1 { font-size: 1.5rem; margin-bottom: 8px; }
h2 { font-size: 1.1rem; color: var(--accent); margin: 24px 0 12px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }
.grid { display: grid; gap: 16px; margin-bottom: 24px; }
.grid-4 { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
.grid-2 { grid-template-columns: 1fr 1fr; }
.card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 16px;
}
.card-value { font-size: 2rem; font-weight: bold; }
.card-label { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; }
table {
    width: 100%; border-collapse: collapse;
    background: var(--surface); border-radius: 8px;
    overflow: hidden; margin-bottom: 16px;
}
th, td {
    padding: 8px 12px; text-align: left;
    border-bottom: 1px solid var(--border);
    font-size: 0.85rem;
}
th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }
.pass { color: var(--pass); }
.fail { color: var(--fail); }
.badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 0.75rem; font-weight: 600;
}
.badge-pass { background: #22c55e22; color: var(--pass); }
.badge-fail { background: #ef444422; color: var(--fail); }
.badge-easy { background: #22c55e22; color: var(--pass); }
.badge-medium { background: #f59e0b22; color: var(--warn); }
.badge-hard { background: #ef444422; color: var(--fail); }
.tools-list {
    display: flex; flex-wrap: wrap; gap: 4px;
}
.tool-tag {
    background: var(--border); padding: 1px 6px; border-radius: 3px;
    font-size: 0.75rem;
}
.tool-tag.missing { background: #ef444433; color: var(--fail); text-decoration: line-through; }
.tool-tag.forbidden { background: #f59e0b33; color: var(--warn); }
.filters { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.filters select, .filters input {
    background: var(--surface); color: var(--text); border: 1px solid var(--border);
    padding: 6px 10px; border-radius: 4px; font-family: inherit; font-size: 0.85rem;
}
.chart-container { position: relative; height: 350px; }
.detail-row { display: none; }
.detail-row td { background: #12141d; }
.detail-content { padding: 8px; white-space: pre-wrap; font-size: 0.8rem; color: var(--muted); max-height: 200px; overflow-y: auto; }
tr.clickable { cursor: pointer; }
tr.clickable:hover { background: #1e2130; }
.progress-bar {
    width: 100%; height: 6px; background: var(--border); border-radius: 3px;
    overflow: hidden; margin-top: 4px;
}
.progress-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
@media (max-width: 800px) {
    .grid-2 { grid-template-columns: 1fr; }
}
</style>
</head>
<body>

<h1>LLM Tool Calling Benchmark</h1>
<p class="subtitle">Geoportal — Busca espacial em linguagem natural</p>

<div id="app"></div>

<script>
const DATA = __DATA_JSON__;

function render() {
    const app = document.getElementById('app');
    const models = [...new Set(DATA.summary.map(s => s.model))];
    const categories = [...new Set(DATA.category_breakdown.map(c => c.category))];

    // Summary cards
    const bestRun = DATA.summary.reduce((a, b) => (a.pass_rate||0) > (b.pass_rate||0) ? a : b, {});
    const totalQueries = DATA.results.length;
    const totalPassed = DATA.results.filter(r => r.passed).length;

    let html = `
    <div class="grid grid-4">
        <div class="card">
            <div class="card-value">${models.length}</div>
            <div class="card-label">Modelos testados</div>
        </div>
        <div class="card">
            <div class="card-value">${DATA.runs.length}</div>
            <div class="card-label">Runs</div>
        </div>
        <div class="card">
            <div class="card-value">${(DATA.summary[0]?.total_queries) || 0}</div>
            <div class="card-label">Queries no benchmark</div>
        </div>
        <div class="card">
            <div class="card-value" style="color:var(--pass)">${bestRun.pass_rate?.toFixed(1) || 0}%</div>
            <div class="card-label">Melhor pass rate</div>
        </div>
    </div>`;

    // Comparison table
    html += `<h2>Comparação de Modelos</h2>
    <table>
    <thead><tr>
        <th>Modelo</th><th>Pass Rate</th><th>Passed</th><th>Failed</th><th>Errors</th><th>Avg Time</th><th>Avg Tokens</th><th>Total Tokens</th><th>Data</th>
    </tr></thead><tbody>`;
    for (const s of DATA.summary) {
        const rate = s.pass_rate?.toFixed(1) || 0;
        const color = rate >= 80 ? 'var(--pass)' : rate >= 50 ? 'var(--warn)' : 'var(--fail)';
        html += `<tr>
            <td><strong>${s.model}</strong></td>
            <td>
                <span style="color:${color};font-weight:bold">${rate}%</span>
                <div class="progress-bar"><div class="progress-fill" style="width:${rate}%;background:${color}"></div></div>
            </td>
            <td class="pass">${s.passed}</td>
            <td class="fail">${s.failed}</td>
            <td>${s.errors}</td>
            <td>${(s.avg_duration_ms/1000).toFixed(1)}s</td>
            <td>${Number(s.avg_tokens).toLocaleString('pt-BR', {maximumFractionDigits:0})}</td>
            <td>${Number(s.sum_tokens).toLocaleString('pt-BR')}</td>
            <td style="color:var(--muted)">${new Date(s.started_at).toLocaleDateString('pt-BR')}</td>
        </tr>`;
    }
    html += `</tbody></table>`;

    // Charts
    html += `<div class="grid grid-2">
        <div class="card"><h2 style="margin-top:0">Pass Rate por Categoria</h2><div class="chart-container"><canvas id="chartCategory"></canvas></div></div>
        <div class="card"><h2 style="margin-top:0">Pass Rate por Dificuldade</h2><div class="chart-container"><canvas id="chartDifficulty"></canvas></div></div>
    </div>`;

    // Category breakdown table
    html += `<h2>Detalhamento por Categoria</h2><table>
    <thead><tr><th>Modelo</th><th>Categoria</th><th>Total</th><th>Passed</th><th>Rate</th><th>Avg Time</th></tr></thead><tbody>`;
    for (const c of DATA.category_breakdown) {
        const rate = c.pass_rate || 0;
        const color = rate >= 80 ? 'var(--pass)' : rate >= 50 ? 'var(--warn)' : 'var(--fail)';
        html += `<tr>
            <td>${c.model}</td>
            <td>${c.category}</td>
            <td>${c.total}</td>
            <td class="pass">${c.passed}</td>
            <td style="color:${color}">${rate}%</td>
            <td>${(c.avg_duration_ms/1000).toFixed(1)}s</td>
        </tr>`;
    }
    html += `</tbody></table>`;

    // Detailed results with filters
    html += `<h2>Resultados Detalhados</h2>
    <div class="filters">
        <select id="filterModel"><option value="">Todos modelos</option>${models.map(m=>`<option value="${m}">${m}</option>`).join('')}</select>
        <select id="filterCategory"><option value="">Todas categorias</option>${categories.map(c=>`<option value="${c}">${c}</option>`).join('')}</select>
        <select id="filterStatus"><option value="">Todos</option><option value="pass">Pass</option><option value="fail">Fail</option></select>
        <select id="filterDifficulty"><option value="">Todas dificuldades</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select>
    </div>
    <table id="resultsTable">
    <thead><tr><th>ID</th><th>Modelo</th><th>Status</th><th>Dif.</th><th>Categoria</th><th>Query</th><th>Tools chamadas</th><th>Tempo</th><th>Tokens</th></tr></thead>
    <tbody id="resultsBody"></tbody>
    </table>`;

    app.innerHTML = html;

    // Render results table
    renderResults();

    // Render charts
    renderCharts(models, categories);

    // Filter listeners
    ['filterModel','filterCategory','filterStatus','filterDifficulty'].forEach(id => {
        document.getElementById(id).addEventListener('change', renderResults);
    });
}

function renderResults() {
    const fm = document.getElementById('filterModel').value;
    const fc = document.getElementById('filterCategory').value;
    const fs = document.getElementById('filterStatus').value;
    const fd = document.getElementById('filterDifficulty').value;

    let filtered = DATA.results;
    if (fm) filtered = filtered.filter(r => r.model === fm);
    if (fc) filtered = filtered.filter(r => r.category === fc);
    if (fs) filtered = filtered.filter(r => fs === 'pass' ? r.passed : !r.passed);
    if (fd) filtered = filtered.filter(r => r.difficulty === fd);

    const tbody = document.getElementById('resultsBody');
    let rows = '';
    for (const r of filtered) {
        const status = r.passed ? '<span class="badge badge-pass">PASS</span>' : '<span class="badge badge-fail">FAIL</span>';
        const diffBadge = `<span class="badge badge-${r.difficulty}">${r.difficulty}</span>`;

        let toolsHtml = '<div class="tools-list">';
        for (const t of r.tools_called) {
            const isForbidden = r.extra_forbidden?.includes(t);
            toolsHtml += `<span class="tool-tag${isForbidden?' forbidden':''}">${t}</span>`;
        }
        for (const t of (r.missing_tools || [])) {
            toolsHtml += `<span class="tool-tag missing">${t}</span>`;
        }
        toolsHtml += '</div>';

        rows += `<tr class="clickable" onclick="toggleDetail('detail-${r.id}')">
            <td>${r.query_id}</td>
            <td style="font-size:0.75rem">${r.model.split('/').pop()}</td>
            <td>${status}</td>
            <td>${diffBadge}</td>
            <td>${r.category}</td>
            <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${r.query_text}">${r.query_text}</td>
            <td>${toolsHtml}</td>
            <td>${(r.duration_ms/1000).toFixed(1)}s</td>
            <td>${(r.total_tokens||0).toLocaleString()}</td>
        </tr>
        <tr class="detail-row" id="detail-${r.id}">
            <td colspan="9"><div class="detail-content"><strong>Query:</strong> ${r.query_text}
<strong>Tools:</strong> ${(r.tools_called||[]).join(' → ') || 'none'}
<strong>Keywords expected:</strong> ${(r.answer_keywords||[]).join(', ') || '—'}
<strong>Keywords found:</strong> ${(r.keywords_found||[]).join(', ') || '—'}
<strong>Keywords missing:</strong> ${(r.keywords_missing||[]).join(', ') || '—'}
<strong>Products expected:</strong> ${(r.expected_product_ids||[]).join(', ') || '—'}
<strong>Products found:</strong> ${(r.found_product_ids||[]).join(', ') || '—'}
<strong>Products missing:</strong> ${(r.missing_product_ids||[]).join(', ') || '—'}
<strong>Tokens:</strong> prompt=${r.prompt_tokens||0} completion=${r.completion_tokens||0} total=${r.total_tokens||0}
<strong>Iterations:</strong> ${r.iterations}
<strong>Error:</strong> ${r.error || '—'}
<strong>Answer:</strong> ${(r.answer||'').substring(0,800)}</div></td>
        </tr>`;
    }
    tbody.innerHTML = rows;
}

function toggleDetail(id) {
    const row = document.getElementById(id);
    row.style.display = row.style.display === 'table-row' ? 'none' : 'table-row';
}

function renderCharts(models, categories) {
    const colors = ['#6366f1','#06b6d4','#22c55e','#f59e0b','#ef4444','#ec4899','#8b5cf6','#14b8a6'];

    // Category chart
    const catCtx = document.getElementById('chartCategory').getContext('2d');
    const catDatasets = models.map((model, i) => {
        const rates = categories.map(cat => {
            const entry = DATA.category_breakdown.find(c => c.model === model && c.category === cat);
            return entry ? Number(entry.pass_rate) : 0;
        });
        return { label: model.split('/').pop(), data: rates, backgroundColor: colors[i % colors.length] + 'cc' };
    });
    new Chart(catCtx, {
        type: 'bar',
        data: { labels: categories, datasets: catDatasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, max: 100, ticks: { color: '#8b8fa3' }, grid: { color: '#2a2d3a' } }, x: { ticks: { color: '#8b8fa3', maxRotation: 45 }, grid: { display: false } } },
            plugins: { legend: { labels: { color: '#e1e4ed' } } }
        }
    });

    // Difficulty chart
    const diffCtx = document.getElementById('chartDifficulty').getContext('2d');
    const diffs = ['easy', 'medium', 'hard'];
    const diffDatasets = models.map((model, i) => {
        const rates = diffs.map(d => {
            const entry = DATA.difficulty_breakdown.find(c => c.model === model && c.difficulty === d);
            return entry ? Number(entry.pass_rate) : 0;
        });
        return { label: model.split('/').pop(), data: rates, backgroundColor: colors[i % colors.length] + 'cc' };
    });
    new Chart(diffCtx, {
        type: 'bar',
        data: { labels: diffs.map(d => d.charAt(0).toUpperCase() + d.slice(1)), datasets: diffDatasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, max: 100, ticks: { color: '#8b8fa3' }, grid: { color: '#2a2d3a' } }, x: { ticks: { color: '#8b8fa3' }, grid: { display: false } } },
            plugins: { legend: { labels: { color: '#e1e4ed' } } }
        }
    });
}

render();
</script>
</body>
</html>"""


def main():
    from dotenv import load_dotenv
    load_dotenv()
    generate_report()


if __name__ == "__main__":
    main()
