"""data_service.py — queries SQL sem full table scan, cache, DiGraph."""
from __future__ import annotations
import json, sqlite3, time
from contextlib import contextmanager
from pathlib import Path
import pandas as pd
import networkx as nx

BASE_DIR     = Path(__file__).resolve().parents[2]
WAREHOUSE_DB = BASE_DIR / "data" / "warehouse" / "catalogo.db"
QUALITY_PATH = BASE_DIR / "data" / "processed" / "quality_report.json"
SUMMARY_PATH = BASE_DIR / "data" / "processed" / "summary.json"
DICT_PATH    = BASE_DIR / "docs" / "data_dictionary.csv"

_cache: dict = {}

def _get(key, ttl=300):
    if key in _cache:
        v, ts = _cache[key]
        if time.time() - ts < ttl:
            return v
    return None

def _set(key, val, ttl=300):
    _cache[key] = (val, time.time())

VIEW_COLS = [
    "id_transacao","transacao_data","transacao_tipo","transacao_valor",
    "fraude","anomaly_score","id_contrato","contrato_valor",
    "id_cliente","cliente_nome","cpf","id_agencia","nome_agencia",
    "sigla","uf","id_produto","produto_nome","produto_tipo",
    "faixa_valor","ano_mes","hora",
]

@contextmanager
def get_conn():
    conn = sqlite3.connect(str(WAREHOUSE_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


def summary() -> dict:
    c = _get("summary"); 
    if c: return c
    with open(SUMMARY_PATH, encoding="utf-8") as f:
        d = json.load(f)
    _set("summary", d)
    return d


def quality() -> dict:
    c = _get("quality")
    if c: return c
    with open(QUALITY_PATH, encoding="utf-8") as f:
        d = json.load(f)
    _set("quality", d)
    return d


def data_dictionary() -> pd.DataFrame:
    if DICT_PATH.exists():
        return pd.read_csv(DICT_PATH)
    return pd.DataFrame({"campo":[],"descricao":[],"tipo":[],"fonte":[]})


def global_search(query="", entity="all", page=1, per_page=20):
    q = (query or "").strip()
    params, clauses = [], []
    if q:
        if entity in ("all","cliente"):
            clauses.append("cliente_nome LIKE ?"); params.append(f"%{q}%")
        if entity in ("all","agencia"):
            clauses.append("nome_agencia LIKE ?"); params.append(f"%{q}%")
        if entity in ("all","produto"):
            clauses.append("produto_nome LIKE ?"); params.append(f"%{q}%")
        if entity in ("all","contrato") and q.isdigit():
            clauses.append("id_contrato = ?"); params.append(int(q))
        if entity == "fraude":
            clauses.append("fraude = 1")
    where  = ("WHERE " + " OR ".join(clauses)) if clauses else ""
    cols   = [c for c in VIEW_COLS]
    col_sql = ", ".join(cols)
    offset = (page - 1) * per_page
    with get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM base_integrada {where}", params).fetchone()[0]
        df    = pd.read_sql(f"SELECT {col_sql} FROM base_integrada {where} LIMIT {per_page} OFFSET {offset}", conn, params=params)
    return df[[c for c in cols if c in df.columns]], total


def export_search(query="", entity="all") -> pd.DataFrame:
    q = (query or "").strip()
    params, clauses = [], []
    if q:
        clauses.append("cliente_nome LIKE ?"); params.append(f"%{q}%")
    if entity == "fraude":
        clauses.append("fraude = 1")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    cols  = [c for c in VIEW_COLS]
    with get_conn() as conn:
        df = pd.read_sql(f"SELECT {', '.join(cols)} FROM base_integrada {where}", conn, params=params)
    return df[[c for c in cols if c in df.columns]]


def entity_detail(entity_type, entity_id):
    col_map = {"cliente":("id_cliente","cliente_nome"),"agencia":("id_agencia","nome_agencia"),
               "produto":("id_produto","produto_nome"),"contrato":("id_contrato",None)}
    if entity_type not in col_map: return None,"",{}
    id_col, name_col = col_map[entity_type]
    with get_conn() as conn:
        sub = pd.read_sql(f"SELECT * FROM base_integrada WHERE {id_col}=?", conn, params=[entity_id])
    if sub.empty: return None,"",{}
    label = str(sub[name_col].iloc[0]) if name_col and name_col in sub.columns else f"{entity_type} {entity_id}"
    metrics = {
        "transacoes":  int(sub["id_transacao"].nunique()) if "id_transacao" in sub.columns else 0,
        "valor_total": round(float(sub["transacao_valor"].sum()), 2) if "transacao_valor" in sub.columns else 0,
        "fraudes":     int(sub["fraude"].sum()) if "fraude" in sub.columns else 0,
        "ticket_medio":round(float(sub["transacao_valor"].mean()), 2) if "transacao_valor" in sub.columns else 0,
        "anomaly_score_medio": round(float(sub["anomaly_score"].mean()), 4) if "anomaly_score" in sub.columns else 0,
    }
    return sub, label, metrics


def dashboard_payload() -> dict:
    c = _get("dashboard", ttl=120)
    if c: return c
    with get_conn() as conn:
        produtos   = pd.read_sql("SELECT produto_nome, COUNT(DISTINCT id_contrato) n FROM base_integrada GROUP BY produto_nome ORDER BY n DESC LIMIT 10", conn)
        agencias   = pd.read_sql("SELECT nome_agencia, sigla, SUM(transacao_valor) vol, COUNT(*) qtd FROM base_integrada GROUP BY id_agencia ORDER BY vol DESC LIMIT 10", conn)
        tipos      = pd.read_sql("SELECT transacao_tipo, COUNT(*) n, SUM(transacao_valor) vol FROM base_integrada GROUP BY transacao_tipo", conn)
        mensal     = pd.read_sql("SELECT ano_mes, SUM(transacao_valor) vol, COUNT(*) qtd, SUM(fraude) fraudes FROM base_integrada GROUP BY ano_mes ORDER BY ano_mes", conn)
        fraude_h   = pd.read_sql("SELECT hora, COUNT(*) total, SUM(fraude) fraudes FROM base_integrada GROUP BY hora ORDER BY hora", conn)
        faixas     = pd.read_sql("SELECT faixa_valor, COUNT(*) n FROM base_integrada GROUP BY faixa_valor ORDER BY n DESC", conn)
        anomalias  = pd.read_sql("SELECT id_transacao,transacao_valor,anomaly_score,nome_agencia,transacao_tipo FROM base_integrada WHERE fraude=1 ORDER BY anomaly_score DESC LIMIT 10", conn)
        fraude_p   = pd.read_sql("SELECT produto_tipo, COUNT(*) total, SUM(fraude) fraudes FROM base_integrada GROUP BY produto_tipo ORDER BY fraudes DESC", conn)
        uf_dist    = pd.read_sql("SELECT uf, COUNT(DISTINCT id_cliente) clientes, SUM(transacao_valor) vol FROM base_integrada WHERE uf IS NOT NULL GROUP BY uf ORDER BY vol DESC", conn)
    
    # Preenche hora 0-23 que podem não ter dados
    all_hours = list(range(24))
    hora_map  = dict(zip(fraude_h["hora"].tolist(), zip(fraude_h["total"].tolist(), fraude_h["fraudes"].tolist())))
    fraude_hora_total   = [int(hora_map.get(h,(0,0))[0]) for h in all_hours]
    fraude_hora_fraudes = [int(hora_map.get(h,(0,0))[1]) for h in all_hours]

    payload = {
        "produtos_labels": list(produtos["produto_nome"]),
        "produtos_values": [int(v) for v in produtos["n"]],
        "agencias_labels": list(agencias["nome_agencia"]),
        "agencias_siglas": list(agencias["sigla"].fillna("")),
        "agencias_vol":    [round(float(v),2) for v in agencias["vol"]],
        "agencias_qtd":    [int(v) for v in agencias["qtd"]],
        "tipos_labels":    list(tipos["transacao_tipo"]),
        "tipos_values":    [int(v) for v in tipos["n"]],
        "tipos_vol":       [round(float(v),2) for v in tipos["vol"]],
        "mensal_labels":   list(mensal["ano_mes"]),
        "mensal_vol":      [round(float(v),2) for v in mensal["vol"]],
        "mensal_qtd":      [int(v) for v in mensal["qtd"]],
        "mensal_fraudes":  [int(v) for v in mensal["fraudes"]],
        "fraude_hora_labels":   all_hours,
        "fraude_hora_total":    fraude_hora_total,
        "fraude_hora_fraudes":  fraude_hora_fraudes,
        "faixas_labels":   list(faixas["faixa_valor"]),
        "faixas_values":   [int(v) for v in faixas["n"]],
        "anomalias":       anomalias.fillna("").to_dict(orient="records"),
        "fraude_prod_labels": list(fraude_p["produto_tipo"].fillna("Outros")),
        "fraude_prod_total":  [int(v) for v in fraude_p["total"]],
        "fraude_prod_fraud":  [int(v) for v in fraude_p["fraudes"]],
        "uf_labels":   list(uf_dist["uf"]),
        "uf_vol":      [round(float(v),2) for v in uf_dist["vol"]],
        "quality":  quality(),
        "summary":  summary(),
    }
    _set("dashboard", payload, ttl=120)
    return payload


def graph_payload(focus_type="cliente", focus_id=None, limit=80) -> dict:
    cols = "id_contrato, id_cliente, cliente_nome, id_agencia, nome_agencia, sigla, id_produto, produto_nome, fraude"
    col_map = {"cliente":"id_cliente","agencia":"id_agencia","produto":"id_produto","contrato":"id_contrato"}
    params = []
    if focus_id is not None and focus_type in col_map:
        sql = f"SELECT DISTINCT {cols} FROM base_integrada WHERE {col_map[focus_type]}=? LIMIT {limit}"
        params = [focus_id]
    else:
        sql = f"SELECT DISTINCT {cols} FROM base_integrada LIMIT {limit}"
    with get_conn() as conn:
        rows = pd.read_sql(sql, conn, params=params)
    if rows.empty and focus_id is not None:
        with get_conn() as conn:
            rows = pd.read_sql(f"SELECT DISTINCT {cols} FROM base_integrada LIMIT {limit}", conn)

    G = nx.DiGraph()
    for _, r in rows.iterrows():
        try:
            vals = {k: int(r[k]) for k in ["id_cliente","id_agencia","id_produto","id_contrato"]}
        except (ValueError, TypeError):
            continue
        cid=f"cliente_{vals['id_cliente']}"; aid=f"agencia_{vals['id_agencia']}"
        pid=f"produto_{vals['id_produto']}"; coid=f"contrato_{vals['id_contrato']}"
        G.add_node(cid,  label=str(r.get("cliente_nome","?")),  group="cliente")
        G.add_node(aid,  label=str(r.get("sigla") or r.get("nome_agencia","?")), group="agencia")
        G.add_node(pid,  label=str(r.get("produto_nome","?")),  group="produto")
        G.add_node(coid, label=f"CTR-{vals['id_contrato']}", group="contrato",
                   has_fraud=bool(r.get("fraude",0)))
        G.add_edge(coid, cid,  label=":pertence_a")
        G.add_edge(coid, pid,  label=":usa_produto")
        G.add_edge(coid, aid,  label=":vinculado_a")
        G.add_edge(cid,  aid,  label=":associado_a")

    nodes = [{"id":n,**a} for n,a in G.nodes(data=True)]
    edges = [{"from":u,"to":v,**d} for u,v,d in G.edges(data=True)]
    return {"nodes":nodes,"edges":edges,"count_nodes":len(nodes),"count_edges":len(edges)}


def fraud_stats() -> dict:
    c = _get("fraud_stats")
    if c: return c
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) total, SUM(fraude) fraudes, AVG(transacao_valor) avg_val, "
            "SUM(CASE WHEN fraude=1 THEN transacao_valor ELSE 0 END) fraud_vol FROM base_integrada"
        ).fetchone()
    result = {
        "total": int(row[0]), "fraudes": int(row[1] or 0),
        "pct":   round((row[1] or 0) / max(row[0],1) * 100, 3),
        "avg_val":   round(row[2] or 0, 2),
        "fraud_vol": round(row[3] or 0, 2),
    }
    _set("fraud_stats", result)
    return result
