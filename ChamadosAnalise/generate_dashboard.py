#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CEX Dashboard Generator - v4
Gera um dashboard HTML a partir dos dados de chamados e clientes.
"""
import pandas as pd
import json

# ============================================================
# 1. CARREGAR
# ============================================================
print("Carregando planilhas...")
df_ch = pd.read_excel('data/raw/RELATORIO CHAMADOS.xlsx')
df_cl = pd.read_excel('data/raw/BASE CLIENTES MULTI.xlsx', sheet_name='Base')

# ============================================================
# 2. NORMALIZAR COLUNAS
# ============================================================
def _cc(c):
    s = str(c).strip()
    for k, v in {chr(186):'o','ç':'c','ã':'a','õ':'o','á':'a','é':'e','í':'i',
                 'ó':'o','ú':'u','â':'a','ê':'e','ô':'o','Ç':'C','Ã':'A','Õ':'O',
                 'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U','Â':'A','Ê':'E','Ô':'O'}.items():
        s = s.replace(k, v)
    return s

df_ch.columns = [_cc(c) for c in df_ch.columns]
df_cl.columns = [_cc(c) for c in df_cl.columns]

print("Colunas Relatorio:", df_ch.columns.tolist())
print("Colunas Base:", df_cl.columns.tolist())

# ============================================================
# 3. NORMALIZAR REGIOES: NE = NORDESTE
# ============================================================
REG_MAP = {
    'NE':          'NORDESTE',
    'CO':          'CENTRO-OESTE',
    'CENTRO OESTE':'CENTRO-OESTE',
}
def norm_reg(r):
    r = str(r).strip().upper()
    return REG_MAP.get(r, r)

# ============================================================
# 4. REFERENCIAS DE COLUNAS
# ============================================================
CC = dict(
    data='Data Criacao Chamado', aprov='Data Aprovacao Ocorrencia', sit='Situacao Chamado', cli='Cliente',
    key='Codigo Integracao Cliente', mot='Motivo', grp='Grupo Motivo',
    vat='Valor Atendimento', vnfd='Valor NFD', nfd='No NFD', qtd='Quantidade'
)
CL = dict(
    key='Destino ID.1', nome='Nome Destino', reg='Regiao',
    coord='Coordenador CEX', anal='Analista CEX', uf='UF', merc='Mercado'
)

# ============================================================
# 5. DIMENSAO CLIENTES
# ============================================================
df_cl['_key']   = df_cl[CL['key']].astype(str).str.strip()
df_cl['_nome']  = df_cl[CL['nome']].fillna('').str.strip()
df_cl['_reg']   = df_cl[CL['reg']].fillna('').apply(norm_reg)
df_cl['_coord'] = df_cl[CL['coord']].fillna('').str.strip()
df_cl['_anal']  = df_cl[CL['anal']].fillna('').str.strip()
df_cl['_uf']    = df_cl[CL['uf']].fillna('').str.strip()
df_cl['_merc']  = df_cl[CL['merc']].fillna('').str.strip()
dim = df_cl[['_key','_nome','_reg','_coord','_anal','_uf','_merc']].drop_duplicates('_key')

print(f"Clientes na BASE: {dim['_key'].nunique()}")

# ============================================================
# 6. PREPARAR CHAMADOS
# ============================================================
df_ch['_key']  = df_ch[CC['key']].astype(str).str.strip()
df_ch['_data'] = pd.to_datetime(df_ch[CC['data']], dayfirst=True, errors='coerce')
df_ch['_d_apr']= pd.to_datetime(df_ch[CC['aprov']], dayfirst=True, errors='coerce')
df_ch['_sla']  = (df_ch['_d_apr'] - df_ch['_data']).dt.days
df_ch['_mes']  = df_ch['_data'].dt.strftime('%Y-%m')
df_ch['_sit']  = df_ch[CC['sit']].fillna('').str.strip()
df_ch['_cli']  = df_ch[CC['cli']].fillna('').str.strip()
df_ch['_mot']  = df_ch[CC['mot']].fillna('').astype(str).str.strip()
df_ch['_grp']  = df_ch[CC['grp']].fillna('').astype(str).str.strip()
df_ch['_vat']  = pd.to_numeric(df_ch[CC['vat']], errors='coerce').fillna(0)
df_ch['_vnfd'] = pd.to_numeric(df_ch[CC['vnfd']], errors='coerce').fillna(0)
df_ch['_nfd']  = pd.to_numeric(df_ch[CC['nfd']], errors='coerce').fillna(0)
df_ch['_qtd']  = pd.to_numeric(df_ch[CC['qtd']], errors='coerce').fillna(0)
df_ch['_dev']  = (df_ch['_nfd'] > 0).astype(int)
print(f"Chamados total: {len(df_ch)}")

# ============================================================
# 7. FILTRAR: apenas clientes da base (INNER JOIN)
# ============================================================
df = df_ch.merge(dim, on='_key', how='inner')
df['_clif'] = df['_nome'].where(df['_nome'] != '', df['_cli'])
print(f"Chamados filtrados: {len(df)} | Clientes: {df['_key'].nunique()}")

# ============================================================
# 8. AGREGACOES
# ============================================================

# Mensal
mensal = []
for m, g in df[df['_mes'].notna()].groupby('_mes'):
    v_sla = g['_sla'].dropna()
    sla_med = round(float(v_sla.mean()), 1) if len(v_sla) > 0 else 0
    mensal.append({'m':m,'tc':int(len(g)),'ab':int((g['_sit']=='Aberto').sum()),
                   'fin':int((g['_sit']=='Finalizado').sum()),
                   'vat':round(float(g['_vat'].sum()),2),
                   'vnfd':round(float(g['_vnfd'].sum()),2),'dev':int(g['_dev'].sum()),
                   'sla':sla_med})
mensal.sort(key=lambda x: x['m'])

# Status
status = [{'s':str(s),'tc':int(len(g))} for s,g in df.groupby('_sit') if str(s).strip()]
status.sort(key=lambda x: -x['tc'])

# Todos os clientes
agg = df.groupby(['_clif','_reg','_coord','_anal','_uf','_merc']).agg(
    tc=('_sit','count'),vat=('_vat','sum'),vnfd=('_vnfd','sum'),
    dev=('_dev','sum'),qtd=('_qtd','sum')
).reset_index().sort_values('tc', ascending=False)
max_tc = int(agg['tc'].max()) if len(agg) > 0 else 1
top_list = [{
    'cl':str(r['_clif'])[:60],'reg':str(r['_reg']),'coord':str(r['_coord']),
    'anal':str(r['_anal']),'uf':str(r['_uf']),'merc':str(r['_merc']),
    'tc':int(r['tc']),'vat':round(float(r['vat']),2),'vnfd':round(float(r['vnfd']),2),
    'dev':int(r['dev']),'qtd':int(r['qtd']),'pct':round(int(r['tc'])/max_tc*100,1)
} for _, r in agg.iterrows()]

# Por regiao (ja normalizada)
por_reg = [{'r':str(r),'tc':int(len(g)),'vat':round(float(g['_vat'].sum()),2),
            'vnfd':round(float(g['_vnfd'].sum()),2)}
           for r, g in df.groupby('_reg') if str(r).strip()]
por_reg.sort(key=lambda x: -x['tc'])

# Todos os motivos com breakdown por cliente (drill-down)
por_mot = []
for mot, g in df[df['_mot'].str.strip() != ''].groupby('_mot'):
    cg = g.groupby(['_clif','_reg']).agg(tc=('_sit','count')).reset_index().sort_values('tc',ascending=False)
    tot = int(len(g))
    top_r = cg.iloc[0] if len(cg) > 0 else None
    por_mot.append({
        'm': str(mot)[:100], 'tc': tot,
        'cli': str(top_r['_clif'])[:50] if top_r is not None else '',
        'reg': str(top_r['_reg']) if top_r is not None else '',
        'clientes': [{'cl':str(r['_clif'])[:50],'reg':str(r['_reg']),
                      'tc':int(r['tc']),'pct':round(int(r['tc'])/tot*100,1)}
                     for _, r in cg.head(20).iterrows()]
    })
por_mot.sort(key=lambda x: -x['tc'])

# Por analista
por_anal = [{'a':str(a),'tc':int(len(g)),'vat':round(float(g['_vat'].sum()),2)}
            for a, g in df.groupby('_anal') if str(a).strip()]
por_anal.sort(key=lambda x: -x['tc'])

# Devolucoes por motivo
df_dev = df[df['_dev'] == 1]
por_dev = [{'m':str(m)[:60],'tc':int(len(g)),'vnfd':round(float(g['_vnfd'].sum()),2)}
           for m, g in df_dev.groupby('_mot') if str(m).strip()]
por_dev.sort(key=lambda x: -x['tc'])
por_dev = por_dev[:15]

# Degradação MoM (Clientes que mais pioraram)
cl_mes = df[df['_mes'].notna()].groupby(['_clif', '_mes']).size().reset_index(name='tc')
pivot = cl_mes.pivot(index='_clif', columns='_mes', values='tc').fillna(0)
meses = sorted(pivot.columns.tolist())
if len(meses) >= 2:
    m_curr, m_prev = meses[-1], meses[-2]
    pivot['diff'] = pivot[m_curr] - pivot[m_prev]
    pioras = pivot.sort_values('diff', ascending=False).head(10)
    top_deg = []
    for k, r in pioras.iterrows():
        if r['diff'] <= 0: continue
        df_c = df[(df['_clif'] == k) & (df['_mes'].isin([m_curr, m_prev]))]
        m_diff = {}
        for mot, g in df_c.groupby('_mot'):
            m_diff[mot] = len(g[g['_mes'] == m_curr]) - len(g[g['_mes'] == m_prev])
        top_mot = max(m_diff.items(), key=lambda x: x[1])[0] if m_diff else ""
        top_deg.append({'cl':str(k)[:40], 'curr':int(r[m_curr]), 'diff':int(r['diff']), 'mot':str(top_mot)[:35]})
else:
    top_deg = []

# KPIs globais
kpis = {
    'total':int(len(df)), 'fin':int((df['_sit']=='Finalizado').sum()),
    'dev':int(df['_dev'].sum()), 'vat':round(float(df['_vat'].sum()),2),
    'vnfd':round(float(df['_vnfd'].sum()),2), 'qtd':int(df['_qtd'].sum()),
    'clientes':len(top_list), 'motivos':len(por_mot)
}

data = {'kpis':kpis,'mensal':mensal,'status':status,'top':top_list,
        'regiao':por_reg,'motivo':por_mot,'analista':por_anal,'devolucao':por_dev, 'deg':top_deg}
json_str = json.dumps(data, ensure_ascii=False)

print(f"\n=== RESUMO ===")
print(f"Total: {kpis['total']:,} chamados | {kpis['clientes']} clientes | {kpis['motivos']} motivos")
print(f"Finalizados: {kpis['fin']:,} ({kpis['fin']/kpis['total']*100:.1f}%)")
print(f"Com devolucao: {kpis['dev']:,}")
print(f"Valor Atend: R${kpis['vat']/1e6:.2f}M | Valor NFD: R${kpis['vnfd']/1e6:.2f}M")

# ============================================================
# 9. GERAR HTML
# Usa __DATA_JSON__ como placeholder - sem problemas de f-string
# ============================================================
OUT = 'C:/Users/SUPERBOOK/ChamadosAnalise/dashboard.html'

HTML = """<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paulo Souza | Analytics Customer Operations</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
:root{
  --bg:#EEF2F7;--card:#FFF;--bd:#DDE3ED;
  --p:#003DA5;--p50:#EBF0FA;--p100:#C8D8F5;--p700:#002E7A;
  --tx:#111827;--mt:#4B5563;--lt:#9CA3AF;
  --gn:#1a7a4a;--gnb:#D1FAE5;
  --am:#B45309;--amb:#FEF3C7;
  --rd:#B91C1C;--rdb:#FEE2E2;
  --sk:#0369A1;--skb:#E0F2FE;
  --r:8px;
  --sh:0 1px 4px rgba(0,0,0,.07),0 1px 2px rgba(0,0,0,.05);
  --shm:0 4px 18px rgba(0,0,0,.09);
}
[data-theme="dark"] {
  --bg:#0F172A;--card:#1E293B;--bd:#334155;
  --tx:#F8FAFC;--mt:#94A3B8;--lt:#64748B;
  --p50:rgba(0,61,165,0.25);--p100:rgba(0,61,165,0.4);
  --gnb:rgba(26,122,74,0.2);--amb:rgba(180,83,9,0.2);
  --rdb:rgba(185,28,28,0.2);--skb:rgba(3,105,161,0.2);
  --sh:0 1px 4px rgba(0,0,0,.2);--shm:0 4px 18px rgba(0,0,0,.3);
}
[data-theme="dark"] .hdr{background:var(--card);border-bottom-color:var(--p)}
[data-theme="dark"] .sb{background:var(--card)}
[data-theme="dark"] thead th{background:#0F172A}
[data-theme="dark"] tbody tr:hover{background:#334155}
[data-theme="dark"] .exp-r{background:#0F172A;border-left-color:var(--bd)}
[data-theme="dark"] .donut-center strong{color:var(--tx)}
[data-theme="dark"] .donut-center span{color:var(--mt)}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--tx);font-size:14px;line-height:1.5}

/* ── HEADER ─────────────────────────────────── */
.hdr{
  background:#fff;
  border-bottom:3px solid var(--p);
  padding:0 28px;
  height:62px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:200;
  box-shadow:0 2px 8px rgba(0,0,0,.08);
}
.hdr-brand{display:flex;align-items:center;gap:0}
.unilever-logo{height:34px;width:auto;display:block}
.hdr-divider{width:1px;height:36px;background:var(--bd);margin:0 20px}
.hdr-name{display:flex;flex-direction:column;justify-content:center}
.hdr-name strong{font-size:15px;font-weight:700;color:var(--tx);letter-spacing:-.01em;line-height:1.25}
.hdr-name span{font-size:11px;font-weight:500;color:var(--mt);letter-spacing:.02em;text-transform:uppercase}
.hdr-right{display:flex;align-items:center;gap:10px}
.dg{display:flex;align-items:center;gap:7px;border:1px solid var(--bd);border-radius:7px;padding:6px 13px;background:var(--bg)}
.dg label{font-size:11px;color:var(--mt);font-weight:500}
input[type=date]{border:none;background:transparent;font-family:inherit;font-size:12px;color:var(--tx);cursor:pointer}
input[type=date]:focus{outline:none}
.hdr-tag{font-size:11px;font-weight:600;color:var(--mt);border:1px solid var(--bd);border-radius:6px;padding:4px 10px;background:var(--bg)}

/* ── LAYOUT ─────────────────────────────────── */
.main{padding:20px 24px;display:flex;flex-direction:column;gap:14px}

/* ── SECTION LABEL ───────────────────────────── */
.sec-label{
  font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
  color:var(--mt);padding:0 0 6px;border-bottom:1px solid var(--bd);margin-bottom:10px;
  display:flex;align-items:center;gap:8px;
}
.sec-label i{color:var(--p);font-size:11px}

/* ── KPI CARDS ───────────────────────────────── */
.kgrid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}
.kpi{
  background:var(--card);border:1px solid var(--bd);border-radius:var(--r);
  padding:16px 18px 14px;box-shadow:var(--sh);position:relative;overflow:hidden;
  transition:transform .18s,box-shadow .18s;
}
.kpi:hover{transform:translateY(-2px);box-shadow:var(--shm)}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--p);border-radius:var(--r) var(--r) 0 0}
.kpi.g::before{background:var(--gn)}.kpi.a::before{background:var(--am)}.kpi.r::before{background:var(--rd)}.kpi.s::before{background:var(--sk)}
.kpi-ico{
  width:32px;height:32px;border-radius:7px;
  display:flex;align-items:center;justify-content:center;
  background:var(--p50);color:var(--p);font-size:13px;margin-bottom:10px;
}
.kpi.g .kpi-ico{background:var(--gnb);color:var(--gn)}
.kpi.a .kpi-ico{background:var(--amb);color:var(--am)}
.kpi.r .kpi-ico{background:var(--rdb);color:var(--rd)}
.kpi.s .kpi-ico{background:var(--skb);color:var(--sk)}
.kl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--mt);margin-bottom:3px}
.kv{font-size:21px;font-weight:700;color:var(--tx);letter-spacing:-.02em}
.ks{font-size:11px;color:var(--lt);margin-top:3px}

/* ── CARD ────────────────────────────────────── */
.card{background:var(--card);border:1px solid var(--bd);border-radius:var(--r);box-shadow:var(--sh)}
.ch{
  padding:11px 16px;border-bottom:1px solid var(--bd);
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;
}
.ct{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--tx);display:flex;align-items:center;gap:7px}
.ct i{color:var(--p);font-size:11px}
.cs{font-size:11px;color:var(--lt);margin-top:1px}
.cb{padding:14px 16px}

/* ── GRIDS ───────────────────────────────────── */
.g2{display:grid;grid-template-columns:2fr 1fr;gap:14px}
.g3{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.cw{position:relative;height:198px}

/* ── TABLE ───────────────────────────────────── */
.tw{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
thead th{
  font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;
  color:var(--mt);padding:8px 12px;text-align:left;
  background:#F9FAFB;border-bottom:1px solid var(--bd);
  position:sticky;top:0;white-space:nowrap;z-index:1;
}
tbody td{padding:7px 12px;border-bottom:1px solid #F3F4F6;vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#F9FAFB}
tbody tr.sel{background:var(--p50)!important;border-left:3px solid var(--p)}
.click{cursor:pointer;transition:background .12s}

/* ── BADGES ──────────────────────────────────── */
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:.02em}
.bg{background:var(--gnb);color:var(--gn)}
.ba{background:var(--amb);color:var(--am)}
.br{background:var(--rdb);color:var(--rd)}
.bs{background:var(--skb);color:var(--sk)}
.bn{background:#F3F4F6;color:var(--mt)}
.tag{
  display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;
  background:var(--p50);color:var(--p);border:1px solid var(--p100);
}

/* ── PROGRESS ────────────────────────────────── */
.bar{height:5px;background:var(--bd);border-radius:3px;overflow:hidden;width:60px;display:inline-block;vertical-align:middle;margin-left:6px}
.bf{height:100%;border-radius:3px;background:var(--p)}

/* ── SEARCH ──────────────────────────────────── */
.sb{
  display:flex;align-items:center;gap:8px;
  background:#fff;border:1px solid var(--bd);border-radius:7px;
  padding:6px 12px;transition:border-color .2s,box-shadow .2s;
}
.sb:focus-within{border-color:var(--p);box-shadow:0 0 0 3px var(--p100)}
.sb i{color:var(--lt);font-size:12px;flex-shrink:0}
.sb input{border:none;background:transparent;font-family:inherit;font-size:12px;color:var(--tx);width:100%;min-width:0}
.sb input:focus{outline:none}
.sb input::placeholder{color:var(--lt)}

/* ── EXPLORER ────────────────────────────────── */
.explorer{display:grid;grid-template-columns:55fr 45fr;border:1px solid var(--bd);border-radius:var(--r);overflow:hidden;box-shadow:var(--sh)}
.exp-l{background:var(--card)}
.exp-r{background:#F7F9FD;border-left:1px solid var(--p100)}
.exp-h{padding:11px 16px;border-bottom:1px solid var(--bd);display:flex;align-items:center;justify-content:space-between;background:var(--card);flex-wrap:wrap;gap:8px}
.emp{display:flex;flex-direction:column;align-items:center;justify-content:center;height:260px;color:var(--lt);gap:8px;text-align:center;padding:24px}
.emp i{font-size:28px;opacity:.35;color:var(--p);display:block;margin-bottom:6px}
.emp strong{font-size:12px;color:var(--mt);font-weight:600}
.emp p{font-size:11px;color:var(--lt);max-width:220px;line-height:1.5}

/* ── MISC ────────────────────────────────────── */
.cnt{background:var(--p);color:#fff;border-radius:5px;padding:2px 9px;font-size:10px;font-weight:700;white-space:nowrap;letter-spacing:.02em}
.tr{text-align:right}.tc{text-align:center}
.fw6{font-weight:600}.fw7{font-weight:700}
.fs10{font-size:10px}.fs11{font-size:11px}.fs12{font-size:12px}
.cm{color:var(--mt)}.cl{color:var(--lt)}
.sli{display:flex;align-items:center;justify-content:space-between;padding:4px 8px;border-radius:5px;background:var(--bg);font-size:11px}
.sld{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-right:7px}

/* ── STATUS DONUT WRAP ───────────────────────── */
.donut-wrap{display:flex;gap:14px;align-items:center}
.donut-box{position:relative;width:132px;height:132px;flex-shrink:0}
.donut-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none}
.donut-center span{font-size:9px;color:var(--lt);text-transform:uppercase;letter-spacing:.06em}
.donut-center strong{font-size:17px;font-weight:700;color:var(--tx)}

.theme-btn {
  background:transparent;border:1px solid var(--bd);color:var(--mt);
  width:32px;height:32px;border-radius:6px;display:flex;align-items:center;justify-content:center;
  cursor:pointer;transition:all .2s;font-size:14px;
}
.theme-btn:hover {background:var(--p50);color:var(--p);border-color:var(--p100)}

@media(max-width:1280px){.kgrid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:900px){.kgrid{grid-template-columns:repeat(2,1fr)}.g2,.g3{grid-template-columns:1fr}.explorer{grid-template-columns:1fr}.main{padding:12px}}
</style>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
</head>
<body>

<!-- ══ HEADER ══════════════════════════════════════════════════ -->
<header class="hdr">
  <div class="hdr-brand">
    <!-- Unilever Brasil Logo -->
    <svg class="unilever-logo" width="110" height="32" viewBox="0 0 110 32" xmlns="http://www.w3.org/2000/svg">
      <rect width="110" height="32" rx="4" fill="#003DA5"/>
      <text x="55" y="22" text-anchor="middle" font-family="Inter, sans-serif" font-size="15" font-weight="800" fill="white">Unilever</text>
    </svg>
    <div class="hdr-divider"></div>
    <div class="hdr-name">
      <strong>Paulo Souza</strong>
      <span>Analytics &amp; Customer Operations</span>
    </div>
  </div>
  <div class="hdr-right">
    <button class="theme-btn" id="theme-toggle" title="Alternar Tema Escuro/Claro"><i class="fa-solid fa-moon"></i></button>
    <span class="hdr-tag" id="dr">Carregando...</span>
    <div class="dg">
      <label>De</label>
      <input type="date" id="dt-s">
      <label>Ate</label>
      <input type="date" id="dt-e">
    </div>
  </div>
</header>

<!-- ══ MAIN ════════════════════════════════════════════════════ -->
<main class="main">

  <!-- KPIs -->
  <div>
    <div class="sec-label"><i class="fa-solid fa-chart-simple"></i> Indicadores do Periodo</div>
    <div class="kgrid">
      <div class="kpi">
        <div class="kpi-ico"><i class="fa-solid fa-ticket"></i></div>
        <div class="kl">Total Chamados</div>
        <div class="kv" id="v1">—</div>
        <div class="ks" id="v1s">Periodo selecionado</div>
      </div>
      <div class="kpi g">
        <div class="kpi-ico"><i class="fa-solid fa-circle-check"></i></div>
        <div class="kl">Finalizados</div>
        <div class="kv" id="v2">—</div>
        <div class="ks" id="v2s">% do total</div>
      </div>
      <div class="kpi">
        <div class="kpi-ico"><i class="fa-solid fa-stopwatch"></i></div>
        <div class="kl">SLA Medio (Dias)</div>
        <div class="kv" id="v3">—</div>
        <div class="ks">Criação a Aprovação</div>
      </div>
      <div class="kpi a">
        <div class="kpi-ico"><i class="fa-solid fa-arrow-rotate-left"></i></div>
        <div class="kl">Devolucoes NFD</div>
        <div class="kv" id="v4">—</div>
        <div class="ks" id="v4s">Com nota de devolucao</div>
      </div>
      <div class="kpi s">
        <div class="kpi-ico"><i class="fa-solid fa-coins"></i></div>
        <div class="kl">Valor Atendimento</div>
        <div class="kv" id="v5">—</div>
        <div class="ks">R$ no periodo</div>
      </div>
      <div class="kpi r">
        <div class="kpi-ico"><i class="fa-solid fa-file-invoice-dollar"></i></div>
        <div class="kl">Valor NFD</div>
        <div class="kv" id="v6">—</div>
        <div class="ks">Notas de devolucao</div>
      </div>
    </div>
  </div>

  <!-- Graficos Linha 1 -->
  <div class="g2">
    <div class="card">
      <div class="ch">
        <div>
          <div class="ct"><i class="fa-solid fa-chart-line"></i> Evolucao Mensal de Chamados</div>
          <div class="cs">Total, finalizados e devolucoes — filtrado pelo periodo acima</div>
        </div>
      </div>
      <div class="cb"><div class="cw"><canvas id="c1"></canvas></div></div>
    </div>
    <div class="card">
      <div class="ch">
        <div>
          <div class="ct"><i class="fa-solid fa-chart-pie"></i> Status da Carteira</div>
          <div class="cs">Distribuicao por situacao</div>
        </div>
      </div>
      <div class="cb">
        <div class="donut-wrap">
          <div class="donut-box">
            <canvas id="c2" width="132" height="132"></canvas>
            <div class="donut-center"><span>Total</span><strong id="st-tot">—</strong></div>
          </div>
          <div id="st-leg" style="flex:1;display:flex;flex-direction:column;gap:4px;overflow:auto;max-height:148px"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Graficos Linha 2 -->
  <div class="g3">
    <div class="card">
      <div class="ch">
        <div>
          <div class="ct"><i class="fa-solid fa-earth-americas"></i> Chamados por Regiao</div>
          <div class="cs">NE e NORDESTE unificados</div>
        </div>
      </div>
      <div class="cb"><div class="cw"><canvas id="c3"></canvas></div></div>
    </div>
    <div class="card">
      <div class="ch">
        <div>
          <div class="ct"><i class="fa-solid fa-map-location-dot"></i> Mapa de Calor Regional</div>
          <div class="cs">Volume de chamados por UF</div>
        </div>
      </div>
      <div class="cb" style="padding:0"><div class="cw" id="brazil_map" style="height:226px"></div></div>
    </div>
    <div class="card">
      <div class="ch">
        <div>
          <div class="ct"><i class="fa-solid fa-users"></i> Carga por Analista</div>
          <div class="cs">Chamados por responsavel</div>
        </div>
      </div>
      <div class="cb"><div class="cw"><canvas id="c4"></canvas></div></div>
    </div>
    <div class="card">
      <div class="ch">
        <div>
          <div class="ct"><i class="fa-solid fa-arrow-trend-up"></i> Clientes em Atenção</div>
          <div class="cs">Ranking de Piora MoM (Mês atual vs anterior)</div>
        </div>
      </div>
      <div class="tw" style="max-height:226px">
        <table>
          <thead>
            <tr><th>Cliente</th><th class="tr">Aumento</th><th>Principal Ofensor</th></tr>
          </thead>
          <tbody id="tdeg"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- EXPLORER DE MOTIVOS -->
  <div>
    <div class="sec-label"><i class="fa-solid fa-magnifying-glass-chart"></i> Explorer de Motivos</div>
    <div style="display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px">
      <p class="fs11 cm" style="max-width:600px">Selecione um motivo na tabela para visualizar <strong>quais clientes geraram aquele tipo de chamado</strong> e as respectivas quantidades.</p>
      <span class="cnt" id="mc">—</span>
    </div>
    <div class="explorer">
      <!-- Esquerda: lista -->
      <div class="exp-l">
        <div class="exp-h">
          <div class="sb" style="flex:1">
            <i class="fa-solid fa-magnifying-glass"></i>
            <input type="text" id="smot" placeholder="Buscar motivo, cliente ou regiao...">
          </div>
          <span class="fs11 cl" id="mvis">—</span>
        </div>
        <div class="tw" style="max-height:380px">
          <table>
            <thead>
              <tr>
                <th style="width:36px">#</th>
                <th>Motivo</th>
                <th class="tr">Chamados</th>
                <th>Principal Cliente</th>
                <th>Regiao</th>
              </tr>
            </thead>
            <tbody id="tmot"></tbody>
          </table>
        </div>
      </div>
      <!-- Direita: detalhe -->
      <div class="exp-r">
        <div class="exp-h">
          <div style="min-width:0;flex:1">
            <div class="ct fs11" id="dtitle" style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
              <i class="fa-solid fa-list-check"></i> Selecione um Motivo
            </div>
            <div class="cs" id="dsub">Clique em uma linha a esquerda</div>
          </div>
        </div>
        <div id="demp" class="emp">
          <i class="fa-solid fa-hand-pointer"></i>
          <strong>Nenhum motivo selecionado</strong>
          <p>Clique em qualquer linha da tabela ao lado para ver quais clientes geraram esse chamado e as quantidades</p>
        </div>
        <div id="dcon" style="display:none">
          <div style="padding:12px 16px;border-bottom:1px solid var(--p100)">
            <div style="height:148px"><canvas id="c5"></canvas></div>
          </div>
          <div class="tw" style="max-height:214px">
            <table>
              <thead>
                <tr>
                  <th style="width:30px">#</th>
                  <th>Cliente</th>
                  <th>Regiao</th>
                  <th class="tr">Chamados</th>
                  <th class="tr">%</th>
                  <th>Volume</th>
                </tr>
              </thead>
              <tbody id="tdet"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- TABELA DE CLIENTES -->
  <div>
    <div class="sec-label"><i class="fa-solid fa-building-user"></i> Detalhamento de Clientes</div>
    <div class="card">
      <div class="ch">
        <div>
          <div class="ct"><i class="fa-solid fa-table-list"></i> Todos os Clientes da Base</div>
          <div class="cs">Clientes com movimentacao no periodo selecionado</div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <span class="cnt" id="cc">—</span>
          <div class="sb" style="width:270px">
            <i class="fa-solid fa-magnifying-glass"></i>
            <input type="text" id="scli" placeholder="Buscar cliente, analista, regiao, UF...">
          </div>
        </div>
      </div>
      <div class="tw" style="max-height:480px">
        <table>
          <thead>
            <tr>
              <th>#</th><th>Cliente</th><th>Regiao</th><th>UF</th>
              <th>Analista CEX</th><th>Coordenador</th>
              <th class="tr">Chamados</th><th>Vol.</th>
              <th class="tr">Devol.</th><th class="tr">R$ Atend.</th><th class="tr">R$ NFD</th><th>Criticidade</th>
            </tr>
          </thead>
          <tbody id="tcli"></tbody>
        </table>
      </div>
    </div>
  </div>

</main>

<script type="application/json" id="rd">__DATA_JSON__</script>
<script>
// ══ DATA ══════════════════════════════════════════════════════
const D = JSON.parse(document.getElementById('rd').textContent);

// ══ HELPERS ═══════════════════════════════════════════════════
const fmt  = n => (+n).toLocaleString('pt-BR');
const fmtR = n => { const v=+n; return v>=1e6?'R$'+(v/1e6).toFixed(2)+'M':v>=1e3?'R$'+(v/1e3).toFixed(0)+'k':'R$'+v.toFixed(0); };
const pct  = (a,b) => b>0?((a/b)*100).toFixed(1)+'%':'0%';
const esc  = s => (s+'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

// Unilever blue palette + region colors
const PCOLS = ['#003DA5','#0369A1','#1a7a4a','#B45309','#B91C1C','#5B21B6','#0F766E','#1D4ED8','#7C3AED','#B91C1C'];
const RCOL  = {
  'NORDESTE':'#0369A1','NE':'#0369A1','LESTE':'#003DA5','SUL':'#1a7a4a',
  'SP':'#B45309','SAO PAULO':'#B45309','RDB':'#BE185D','CN':'#5B21B6',
  'NORTE':'#0891B2','CENTRO-OESTE':'#B45309','FOODS':'#4D7C0F','PR':'#7C3AED'
};
const SCOL  = {'Finalizado':'#1a7a4a','Aberto':'#B91C1C','Em Tratativa':'#B45309','Rejeitado':'#6B7280','Cancelado':'#9CA3AF'};
const rc    = r => RCOL[(r+'').toUpperCase()] || '#6B7280';
const sc    = s => SCOL[s] || '#6B7280';

let CH = {}, dChart = null, actRow = null;
let allMR = [], allCR = [];

// ══ DATE FILTER ═══════════════════════════════════════════════
function getRange(){ return { s:document.getElementById('dt-s').value.substr(0,7), e:document.getElementById('dt-e').value.substr(0,7) }; }
function filtMen(){ const {s,e}=getRange(); return D.mensal.filter(r=>r.m>=s&&r.m<=e); }

// ══ KPIs ══════════════════════════════════════════════════════
function updKPIs(men){
  const tc=men.reduce((a,r)=>a+r.tc,0), fi=men.reduce((a,r)=>a+r.fin,0),
        dv=men.reduce((a,r)=>a+r.dev,0), va=men.reduce((a,r)=>a+r.vat,0),
        vn=men.reduce((a,r)=>a+r.vnfd,0);
  
  const val_sla = men.filter(r=>r.sla>0);
  const avg_sla = val_sla.length>0 ? (val_sla.reduce((a,r)=>a+r.sla,0)/val_sla.length).toFixed(1) : '0';

  document.getElementById('v1').textContent=fmt(tc);
  document.getElementById('v2').textContent=fmt(fi);
  document.getElementById('v2s').textContent=pct(fi,tc)+' do total';
  
  document.getElementById('v3').textContent=avg_sla+' d';
  
  document.getElementById('v4').textContent=fmt(dv);
  document.getElementById('v4s').textContent=pct(dv,tc)+' dos chamados';
  document.getElementById('v5').textContent=fmtR(va);
  document.getElementById('v6').textContent=fmtR(vn);
}

// ══ CHARTS ════════════════════════════════════════════════════
const baseOpts={responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
  scales:{x:{ticks:{font:{family:'Inter',size:9},color:'#9CA3AF'},grid:{color:'#F3F4F6'}},
          y:{ticks:{font:{family:'Inter',size:9},color:'#9CA3AF'},grid:{color:'#F3F4F6'}}}};
const hOpts={...baseOpts,indexAxis:'y',scales:{
  x:{ticks:{font:{family:'Inter',size:9},color:'#9CA3AF'},grid:{color:'#F3F4F6'}},
  y:{ticks:{font:{family:'Inter',size:9},color:'#4B5563'},grid:{display:false}}}};

function cMensal(men){
  if(CH.m)CH.m.destroy();
  CH.m=new Chart(document.getElementById('c1'),{type:'line',
    data:{labels:men.map(r=>r.m),datasets:[
      {label:'Total',data:men.map(r=>r.tc),borderColor:'#003DA5',backgroundColor:'rgba(0,61,165,.06)',fill:true,tension:.4,pointRadius:3,borderWidth:2},
      {label:'Finalizados',data:men.map(r=>r.fin),borderColor:'#1a7a4a',fill:false,tension:.4,pointRadius:2,borderWidth:1.5,borderDash:[5,3]},
      {label:'Devolucoes',data:men.map(r=>r.dev),borderColor:'#B45309',fill:false,tension:.4,pointRadius:2,borderWidth:1.5,borderDash:[3,3]}
    ]},
    options:{...baseOpts,interaction:{mode:'index',intersect:false},
      plugins:{legend:{labels:{font:{family:'Inter',size:10},boxWidth:10,color:'#6B7280'}}}}
  });
}

function cStatus(){
  const st=D.status, tot=st.reduce((a,r)=>a+r.tc,0);
  document.getElementById('st-tot').textContent=fmt(tot);
  if(CH.s)CH.s.destroy();
  CH.s=new Chart(document.getElementById('c2'),{type:'doughnut',
    data:{labels:st.map(r=>r.s),datasets:[{data:st.map(r=>r.tc),backgroundColor:st.map(r=>sc(r.s)),borderWidth:2,borderColor:'#fff',hoverOffset:4}]},
    options:{responsive:false,cutout:'70%',plugins:{legend:{display:false}}}
  });
  document.getElementById('st-leg').innerHTML=st.map(r=>{
    const p=tot>0?((r.tc/tot)*100).toFixed(1):'0', c=sc(r.s);
    return `<div class="sli"><div style="display:flex;align-items:center"><div class="sld" style="background:${c}"></div>${esc(r.s)}</div><div style="text-align:right"><div class="fw6 fs11">${fmt(r.tc)}</div><div class="fs10 cl">${p}%</div></div></div>`;
  }).join('');
}

function cRegiao(){
  const reg=D.regiao;
  if(CH.r)CH.r.destroy();
  CH.r=new Chart(document.getElementById('c3'),{type:'bar',
    data:{labels:reg.map(r=>r.r||'Outros'),datasets:[{data:reg.map(r=>r.tc),backgroundColor:reg.map(r=>rc(r.r)+'BB'),borderRadius:5,borderSkipped:false}]},
    options:baseOpts
  });
}

function cAnalista(){
  const an=D.analista.slice(0,15);
  if(CH.a)CH.a.destroy();
  CH.a=new Chart(document.getElementById('c4'),{type:'bar',
    data:{labels:an.map(r=>r.a.length>20?r.a.substr(0,18)+'..':r.a),
          datasets:[{data:an.map(r=>r.tc),backgroundColor:an.map((_,i)=>PCOLS[i%PCOLS.length]+'BB'),borderRadius:4,borderSkipped:false}]},
    options:hOpts
  });
}

// ══ MOTIVOS TABLE ═════════════════════════════════════════════
function rMotivos(){
  const mot=D.motivo;
  document.getElementById('mc').textContent=mot.length+' motivos';
  const tbody=document.getElementById('tmot'); tbody.innerHTML='';
  const rows=mot.map((r,i)=>{
    const tr=document.createElement('tr'); tr.className='click';
    tr.dataset.t=(r.m+' '+r.cli+' '+r.reg).toLowerCase();
    tr.innerHTML=`<td class="fs11 cl">${i+1}</td><td class="fs12" style="max-width:280px">${esc(r.m)}</td><td class="tr fw6">${fmt(r.tc)}</td><td class="fs11 cm" style="max-width:170px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${esc(r.cli)}">${esc(r.cli)}</td><td><span class="tag fs10">${esc(r.reg)}</span></td>`;
    tr.addEventListener('click',()=>showDet(r,i,tr));
    tbody.appendChild(tr); return tr;
  });
  allMR=rows; updMotVis();
}

function updMotVis(){
  const vis=allMR.filter(tr=>tr.style.display!=='none').length;
  document.getElementById('mvis').textContent=vis+' visiveis';
}

document.getElementById('smot').addEventListener('input',function(){
  const q=this.value.toLowerCase().trim();
  allMR.forEach(tr=>{tr.style.display=(!q||tr.dataset.t.includes(q))?'':'none';});
  updMotVis();
});

// ══ MOTIVO DETAIL ══════════════════════════════════════════════
function showDet(motData,idx,tr){
  if(actRow){actRow.classList.remove('sel');} tr.classList.add('sel'); actRow=tr;
  tr.scrollIntoView({block:'nearest'});
  document.getElementById('demp').style.display='none';
  document.getElementById('dcon').style.display='';
  const title=motData.m.length>55?motData.m.substr(0,53)+'...':motData.m;
  document.getElementById('dtitle').innerHTML='<i class="fa-solid fa-list-check" style="color:var(--p)"></i> '+esc(title);
  document.getElementById('dsub').textContent=fmt(motData.tc)+' chamados — '+motData.clientes.length+' clientes';
  const cls=motData.clientes.slice(0,10);
  if(dChart)dChart.destroy();
  dChart=new Chart(document.getElementById('c5'),{type:'bar',
    data:{labels:cls.map(c=>c.cl.length>22?c.cl.substr(0,20)+'..':c.cl),
          datasets:[{data:cls.map(c=>c.tc),backgroundColor:cls.map(c=>rc(c.reg)+'BB'),borderRadius:4,borderSkipped:false}]},
    options:hOpts
  });
  document.getElementById('tdet').innerHTML=motData.clientes.map((c,i)=>{
    const bw=Math.min(Math.round(c.pct),100), rc2=rc(c.reg);
    return `<tr><td class="fs11 cl">${i+1}</td><td class="fs12 fw6" title="${esc(c.cl)}">${c.cl.length>34?esc(c.cl.substr(0,32))+'..':esc(c.cl)}</td><td><span class="tag fs10" style="background:${rc2}18;color:${rc2};border-color:${rc2}44">${esc(c.reg)}</span></td><td class="tr fw7">${fmt(c.tc)}</td><td class="tr fs11 cm">${c.pct}%</td><td><div class="bar"><div class="bf" style="width:${bw}%;background:${rc2}"></div></div></td></tr>`;
  }).join('');
}

// ══ CLIENT TABLE & DEG TABLE ════════════════════════════════════
function rClientes(){
  const top=D.top;
  document.getElementById('cc').textContent=top.length+' clientes';
  const tbody=document.getElementById('tcli'); tbody.innerHTML='';
  const mtc=top.length>0?top[0].tc:1;
  const rows=top.map((r,i)=>{
    const tr=document.createElement('tr');
    tr.dataset.t=(r.cl+' '+r.anal+' '+r.coord+' '+r.reg+' '+r.uf+' '+r.merc).toLowerCase();
    const bw=Math.round(r.tc/mtc*100), dvp=r.tc>0?((r.dev/r.tc)*100).toFixed(0):0, rc2=rc(r.reg);
    let bdg;
    if(r.tc>=500)      bdg='<span class="badge br">CRITICO</span>';
    else if(r.tc>=200) bdg='<span class="badge ba">ALTO</span>';
    else if(r.tc>=50)  bdg='<span class="badge bs">MEDIO</span>';
    else               bdg='<span class="badge bn">BAIXO</span>';
    tr.innerHTML=`
      <td class="fs11 cl">${i+1}</td>
      <td class="fs12 fw6" title="${esc(r.cl)}" style="max-width:210px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(r.cl)}</td>
      <td><span class="tag fs10" style="background:${rc2}18;color:${rc2};border-color:${rc2}44">${esc(r.reg)}</span></td>
      <td class="fs11 cm">${esc(r.uf)}</td>
      <td class="fs11">${esc(r.anal)}</td>
      <td class="fs11 cm">${esc(r.coord)}</td>
      <td class="tr"><span class="fw7">${fmt(r.tc)}</span><div class="bar"><div class="bf" style="width:${bw}%"></div></div></td>
      <td class="tr fs11 cl">${r.qtd>0?fmt(r.qtd):'—'}</td>
      <td class="tr" style="color:${r.dev>0?'var(--am)':'var(--lt)'}">${fmt(r.dev)}<span class="fs10 cl"> (${dvp}%)</span></td>
      <td class="tr fs11">${fmtR(r.vat)}</td>
      <td class="tr fs11" style="color:${r.vnfd>0?'var(--rd)':'var(--lt)'}">${r.vnfd>0?fmtR(r.vnfd):'—'}</td>
      <td>${bdg}</td>`;
    tbody.appendChild(tr); return tr;
  });
  allCR=rows;
  
  // Deg table
  const tdeg=document.getElementById('tdeg'); tdeg.innerHTML='';
  if(D.deg.length===0){
    tdeg.innerHTML='<tr><td colspan="3" class="tc cl fs11" style="padding:20px">Sem dados suficientes para comparar meses</td></tr>';
  } else {
    D.deg.forEach(r=>{
      tdeg.innerHTML+=`<tr>
        <td class="fs11 fw6" style="max-width:140px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${esc(r.cl)}">${esc(r.cl)}</td>
        <td class="tr"><span class="badge br"><i class="fa-solid fa-arrow-up"></i> ${r.diff}</span></td>
        <td class="fs10 cm" style="max-width:120px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${esc(r.mot)}">${esc(r.mot)}</td>
      </tr>`;
    });
  }
}

document.getElementById('scli').addEventListener('input',function(){
  const q=this.value.toLowerCase().trim();
  allCR.forEach(tr=>{tr.style.display=(!q||tr.dataset.t.includes(q))?'':'none';});
});

// ══ UPDATE ════════════════════════════════════════════════════
function update(){ const men=filtMen(); updKPIs(men); cMensal(men); }

// ══ INIT ══════════════════════════════════════════════════════
function init(){
  if(D.mensal.length>0){
    document.getElementById('dt-s').value=D.mensal[0].m+'-01';
    document.getElementById('dt-e').value=D.mensal[D.mensal.length-1].m+'-28';
    document.getElementById('dr').textContent=
      D.mensal[0].m+' a '+D.mensal[D.mensal.length-1].m+
      '  |  '+D.kpis.clientes+' clientes  |  '+D.kpis.motivos+' motivos';
  }
  update(); cStatus(); cRegiao(); cAnalista(); rMotivos(); rClientes();
}

// ══ THEME TOGGLE ══════════════════════════════════════════════
const btnTheme = document.getElementById('theme-toggle');
let isDark = localStorage.getItem('theme') === 'dark';
if (isDark) document.documentElement.setAttribute('data-theme', 'dark');

function applyTheme() {
  const root = document.documentElement;
  if (isDark) {
    root.setAttribute('data-theme', 'dark');
    btnTheme.innerHTML = '<i class="fa-solid fa-sun"></i>';
    Chart.defaults.color = '#94A3B8';
    Chart.defaults.borderColor = '#334155';
  } else {
    root.removeAttribute('data-theme');
    btnTheme.innerHTML = '<i class="fa-solid fa-moon"></i>';
    Chart.defaults.color = '#9CA3AF';
    Chart.defaults.borderColor = '#F3F4F6';
  }
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  update(); cStatus(); cRegiao(); cAnalista();
}

btnTheme.addEventListener('click', () => {
  isDark = !isDark;
  applyTheme();
});

// ══ MAPA DE CALOR ══════════════════════════════════════════════
let mapLoaded = false;
google.charts.load('current', {'packages':['geochart']});
google.charts.setOnLoadCallback(() => { mapLoaded = true; drawMap(); });

function drawMap() {
  if(!mapLoaded) return;
  const ufAgg = {};
  D.top.forEach(r=>{
      if(r.uf) {
        let uf = r.uf.trim().toUpperCase();
        if(uf.length === 2) ufAgg[uf] = (ufAgg[uf] || 0) + r.tc;
      }
  });
  const mapData = [['Estado', 'Volume']];
  for(let uf in ufAgg) mapData.push(['BR-'+uf, ufAgg[uf]]);
  
  if(mapData.length === 1) return;
  const data = google.visualization.arrayToDataTable(mapData);
  const options = {
    region: 'BR', resolution: 'provinces',
    colorAxis: {colors: ['#EBF0FA', '#003DA5']},
    backgroundColor: 'transparent',
    datalessRegionColor: isDark ? '#334155' : '#F3F4F6',
    defaultColor: '#f5f5f5',
    legend: 'none'
  };
  const chart = new google.visualization.GeoChart(document.getElementById('brazil_map'));
  chart.draw(data, options);
}

document.getElementById('dt-s').addEventListener('change', () => { update(); drawMap(); });
document.getElementById('dt-e').addEventListener('change', () => { update(); drawMap(); });

// Patch applyTheme to redraw map
const oldApply = applyTheme;
applyTheme = function() {
    oldApply();
    if(mapLoaded) drawMap();
}

Chart.defaults.font.family = "'Inter', sans-serif";
if(isDark) { Chart.defaults.color = '#94A3B8'; Chart.defaults.borderColor = '#334155'; }
init();
if(isDark) applyTheme();
</script>
</body>
</html>"""

HTML = HTML.replace('__DATA_JSON__', json_str)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f"\nHTML salvo em: {OUT}")
