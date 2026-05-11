
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
import pandas as pd
import networkx as nx

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
WAREHOUSE_DB = DATA_DIR / "warehouse" / "catalogo.db"
AUTH_DB = DATA_DIR / "warehouse" / "auth.db"
QUALITY_PATH = DATA_DIR / "processed" / "quality_report.json"
SUMMARY_PATH = DATA_DIR / "processed" / "summary.json"
DICT_PATH = BASE_DIR / "docs" / "data_dictionary.csv"

def get_connection():
    return sqlite3.connect(WAREHOUSE_DB)

def load_base():
    conn = get_connection()
    df = pd.read_sql("select * from base_integrada", conn)
    conn.close()
    if "transacao_data" in df.columns:
        df["transacao_data"] = pd.to_datetime(df["transacao_data"], errors="coerce")
    if "contrato_data" in df.columns:
        df["contrato_data"] = pd.to_datetime(df["contrato_data"], errors="coerce")
    return df

def summary():
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def quality():
    with open(QUALITY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def data_dictionary():
    return pd.read_csv(DICT_PATH)

def global_search(query: str = "", entity: str = "all", page: int = 1, per_page: int = 20):
    df = load_base()
    q = (query or "").strip()
    if q:
        mask = False
        if entity in ("all", "cliente"):
            mask = mask | df["cliente_nome"].astype(str).str.contains(q, case=False, na=False)
        if entity in ("all", "agencia"):
            mask = mask | df["nome_agencia"].astype(str).str.contains(q, case=False, na=False)
        if entity in ("all", "produto"):
            mask = mask | df["produto_nome"].astype(str).str.contains(q, case=False, na=False)
        if entity in ("all", "contrato"):
            if q.isdigit():
                mask = mask | (df["id_contrato"] == int(q))
        if entity in ("all", "cpf"):
            mask = mask | df["cpf"].astype(str).str.contains(q, case=False, na=False)
        results = df[mask].copy()
    else:
        results = df.copy()
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    view_cols = [
        "id_cliente","id_agencia","id_produto","id_transacao","transacao_data","transacao_tipo","transacao_valor",
        "id_contrato","contrato_valor","cliente_nome","cpf","nome_agencia","produto_nome","produto_tipo"
    ]
    view_cols = [c for c in view_cols if c in results.columns]
    return results.iloc[start:end][view_cols], total

def export_search(query: str = "", entity: str = "all"):
    df, total = global_search(query, entity, page=1, per_page=1000000)
    return df

def entity_detail(entity_type: str, entity_id: int):
    df = load_base()
    if entity_type == "cliente":
        sub = df[df["id_cliente"] == int(entity_id)].copy()
        label = sub["cliente_nome"].iloc[0] if not sub.empty else ""
    elif entity_type == "agencia":
        sub = df[df["id_agencia"] == int(entity_id)].copy()
        label = sub["nome_agencia"].iloc[0] if not sub.empty else ""
    elif entity_type == "produto":
        sub = df[df["id_produto"] == int(entity_id)].copy()
        label = sub["produto_nome"].iloc[0] if not sub.empty else ""
    elif entity_type == "contrato":
        sub = df[df["id_contrato"] == int(entity_id)].copy()
        label = f"Contrato {entity_id}" if not sub.empty else ""
    else:
        return None, "", {}
    if sub.empty:
        return None, "", {}
    metrics = {
        "linhas_relacionadas": int(len(sub)),
        "transacoes": int(sub["id_transacao"].nunique()),
        "contratos": int(sub["id_contrato"].nunique()),
        "valor_total_transacoes": round(float(sub["transacao_valor"].sum()), 2),
    }
    return sub, label, metrics

def dashboard_payload():
    df = load_base()
    produtos = (df[["id_contrato","produto_nome"]].drop_duplicates()
                .groupby("produto_nome")["id_contrato"].count().sort_values(ascending=False).head(10))
    clientes = (df.groupby("cliente_nome")["id_transacao"].count().sort_values(ascending=False).head(10))
    agencias = (df.groupby("nome_agencia")["transacao_valor"].sum().sort_values(ascending=False).head(10))
    tipos = (df.groupby("transacao_tipo")["id_transacao"].count().sort_values(ascending=False))
    mensal = (df.groupby("ano_mes")["transacao_valor"].sum().sort_index())
    qualidade = quality()
    return {
        "produtos_labels": list(produtos.index), "produtos_values": [int(v) for v in produtos.values],
        "clientes_labels": list(clientes.index), "clientes_values": [int(v) for v in clientes.values],
        "agencias_labels": list(agencias.index), "agencias_values": [float(v) for v in agencias.values],
        "tipos_labels": list(tipos.index), "tipos_values": [int(v) for v in tipos.values],
        "mensal_labels": list(mensal.index), "mensal_values": [float(v) for v in mensal.values],
        "quality": qualidade,
    }

def graph_payload(focus_type: str = "cliente", focus_id: int | None = None, limit: int = 60):
    df = load_base()
    unique = df[["id_contrato","id_cliente","cliente_nome","id_agencia","nome_agencia","id_produto","produto_nome"]].drop_duplicates()
    if focus_id is not None:
        if focus_type == "cliente":
            unique = unique[unique["id_cliente"] == int(focus_id)]
        elif focus_type == "agencia":
            unique = unique[unique["id_agencia"] == int(focus_id)]
        elif focus_type == "produto":
            unique = unique[unique["id_produto"] == int(focus_id)]
        elif focus_type == "contrato":
            unique = unique[unique["id_contrato"] == int(focus_id)]
        if unique.empty:
            unique = df[["id_contrato","id_cliente","cliente_nome","id_agencia","nome_agencia","id_produto","produto_nome"]].drop_duplicates().head(limit)
    else:
        unique = unique.head(limit)

    G = nx.Graph()
    for _, row in unique.iterrows():
        cid = f"cliente_{int(row['id_cliente'])}"
        aid = f"agencia_{int(row['id_agencia'])}"
        pid = f"produto_{int(row['id_produto'])}"
        coid = f"contrato_{int(row['id_contrato'])}"
        G.add_node(cid, label=str(row["cliente_nome"]), group="cliente")
        G.add_node(aid, label=str(row["nome_agencia"]), group="agencia")
        G.add_node(pid, label=str(row["produto_nome"]), group="produto")
        G.add_node(coid, label=f"Contrato {int(row['id_contrato'])}", group="contrato")
        G.add_edge(cid, aid, label="pertence_a")
        G.add_edge(cid, coid, label="possui")
        G.add_edge(coid, pid, label="usa")
    nodes = [{"id": n, **attrs} for n, attrs in G.nodes(data=True)]
    edges = [{"from": u, "to": v, **attrs} for u, v, attrs in G.edges(data=True)]
    return {"nodes": nodes, "edges": edges, "count_nodes": len(nodes), "count_edges": len(edges)}
