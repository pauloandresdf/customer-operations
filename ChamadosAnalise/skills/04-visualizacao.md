### 📂 4. Conteúdo para `docs/04-visualizacao.md`

```md
# Skill 04 — Visualização HTML Premium (CEX Custom Dashboard)

## O que esta skill produz
Um dashboard executivo e operacional completo rodando dentro de um único visual customizado "HTML Content" no Power BI. O design adota uma estética futurista cyberpunk/dark theme focado em monitoramento de cadeia de suprimentos.

## ❶ REGRA ABSOLUTA — ASPAS SIMPLES
O código HTML/CSS/JS deve conter **APENAS aspas simples ('')**. Toda aspa dupla necessária para a estrutura do JSON interno deve ser gerada via função `UNICHAR(34)` do DAX. Qualquer aspa dupla direta no template quebrará o motor de renderização da medida sem aviso prévio.

---

## ❷ Arquitetura do Fluxo de Dados In-Memory
Medida DAX [Visual Dashboard]
└─ Realiza o CROSSJOIN (Analista × Região) e calcula volumetria
└─ Concatena tudo via CONCATENATEX gerando um JSON comprimido (< 30KB)
└─ Injeta o JSON em uma 
JS lê a div 'raw'
└─ Aplica os filtros de input de tela e renderiza os gráficos via Chart.js


---

## ❸ Mapeamento de Chaves Curtas para o JSON (Proteção de Limite de String)
Para garantir que o payload não estoure o limite de **30KB** do Power BI, os campos reais foram reduzidos a chaves de uma ou duas letras:

| Coluna Real no Modelo | Chave Curta no JS |
|-----------------------|-------------------|
| `BASE CLIENTES MULTI[Analista CEX]` | `a` |
| `BASE CLIENTES MULTI[Região]` | `r` |
| `[Total Chamados]` | `tc` |
| `[Total Chamados Finalizados]` | `cf` |
| `[Total Chamados Abertos]` | `ca` |

---

## ❹ Estrutura DAX de Geração do JSON Mestre
```dax
Visual Dashboard = 
VAR _base = 
    ADDCOLUMNS(
        CROSSJOIN(
            VALUES('BASE CLIENTES MULTI'[Analista CEX]),
            VALUES('BASE CLIENTES MULTI'[Região])
        ),
        "tc", [Total Chamados],
        "cf", [Total Chamados Finalizados],
        "ca", [Total Chamados Abertos]
    )

VAR _json = 
    '{"records":[' &
    CONCATENATEX(
        FILTER(_base, [tc] > 0),
        '{' &
        UNICHAR(34) & 'a'  & UNICHAR(34) & ':' & UNICHAR(34) & 'BASE CLIENTES MULTI'[Analista CEX] & UNICHAR(34) & ',' &
        UNICHAR(34) & 'r'  & UNICHAR(34) & ':' & UNICHAR(34) & 'BASE CLIENTES MULTI'[Região] & UNICHAR(34) & ',' &
        UNICHAR(34) & 'tc' & UNICHAR(34) & ':' & FORMAT([tc],"0") & ',' &
        UNICHAR(34) & 'cf' & UNICHAR(34) & ':' & FORMAT([cf],"0") & ',' &
        UNICHAR(34) & 'ca' & UNICHAR(34) & ':' & FORMAT([ca],"0") &
        '}',
        ','
    ) & ']}'

VAR _html = 
"<!DOCTYPE html>
<html lang='pt-br' data-theme='dark'>
<head>
    <meta charset='UTF-8'>
    <script src='[https://cdn.jsdelivr.net/npm/chart.js](https://cdn.jsdelivr.net/npm/chart.js)'></script>
    <link href='[https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;700;900&display=swap](https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;700;900&display=swap)' rel='stylesheet'>
    <style>
        :root {
            --bg:#04040f; --bg2:#080818; --card:#0b0b1e; --border:#1a1a3e;
            --accent:#6d28d9; --text:#e2e8f0; --muted:#64748b;
            --success:#10b981; --warn:#f59e0b; --danger:#ef4444;
        }
        body { font-family:'Exo 2', sans-serif; background:var(--bg); color:var(--text); padding:20px; }
        .kpi-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; margin-bottom:16px; }
        .kpi-card { background:var(--card); padding:16px; border-radius:12px; border:1px solid var(--border); }
        .kpi-value { font-family:'Share Tech Mono', monospace; font-size:1.8rem; font-weight:700; color:white; }
        .charts-container { display:grid; grid-template-columns: 1fr 1fr; gap:16px; }
        .chart-box { background:var(--card); padding:16px; border-radius:12px; border:1px solid var(--border); height:260px; }
    </style>
</head>
<body>
    <div class='header'>
        <h2 style='font-family:Share Tech Mono, monospace; letter-spacing:2px;'>🎯 CEX CONTROL CENTER</h2>
    </div>
    
    <div class='kpi-grid'>
        <div class='kpi-card'><div style='color:var(--muted); font-size:0.7rem;'>TOTAL CHAMADOS</div><div id='v1' class='kpi-value'>—</div></div>
        <div class='kpi-card'><div style='color:var(--muted); font-size:0.7rem;'>BACKLOG ATIVO (ABERTOS)</div><div id='v2' class='kpi-value' style='color:var(--warn)'>—</div></div>
        <div class='kpi-card'><div style='color:var(--muted); font-size:0.7rem;'>TAXA DE OPERAÇÃO</div><div id='v3' class='kpi-value' style='color:var(--success)'>—</div></div>
    </div>

    <div class='charts-container'>
        <div class='chart-box'><canvas id='chart-regiao'></canvas></div>
        <div class='chart-box'><canvas id='chart-analista'></canvas></div>
    </div>

    <div id='raw' style='display:none;'>" & _json & "</div>

    <script>
        function updateDashboard() {
            var rawData = JSON.parse(document.getElementById('raw').innerText);
            var records = rawData.records;

            var total = records.reduce((s, x) => s + x.tc, 0);
            var abertos = records.reduce((s, x) => s + x.ca, 0);
            var finalizados = records.reduce((s, x) => s + x.cf, 0);
            var taxa = total > 0 ? ((finalizados / total) * 100).toFixed(1) : 0;

            document.getElementById('v1').innerText = total.toLocaleString('pt-BR');
            document.getElementById('v2').innerText = abertos.toLocaleString('pt-BR');
            document.getElementById('v3').innerText = taxa + '%';

            var regioes = [...new Set(records.map(r => r.r))];
            var dadosRegiao = regioes.map(reg => records.filter(x => x.r === reg).reduce((s, y) => s + y.tc, 0));

            new Chart(document.getElementById('chart-regiao'), {
                type: 'bar',
                data: {
                    labels: regioes,
                    datasets: [{ label: 'Chamados por Região', data: dadosRegiao, backgroundColor: '#6d28d9' }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }
        updateDashboard();
    </script>
</body>
</html>"

RETURN _html