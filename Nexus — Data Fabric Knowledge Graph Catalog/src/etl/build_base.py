
from __future__ import annotations
import json
import logging
import sqlite3
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw_enterprise"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
WAREHOUSE_DIR = BASE_DIR / "data" / "warehouse"
LOG_DIR = BASE_DIR / "logs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("etl")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_DIR / "etl.log", encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
if not logger.handlers:
    logger.addHandler(fh)

def main():
    logger.info("ETL iniciado.")
    clientes = pd.read_csv(RAW_DIR / "clientes.csv").rename(columns={"nome":"cliente_nome"})
    agencias = pd.read_csv(RAW_DIR / "agencias.csv")
    produtos = pd.read_excel(RAW_DIR / "produtos.xlsx").rename(columns={"nome":"produto_nome","tipo":"produto_tipo"})

    conn = sqlite3.connect(RAW_DIR / "contratos.db")
    contratos = pd.read_sql("select * from contratos", conn)
    conn.close()
    contratos = contratos.rename(columns={"valor":"contrato_valor","data":"contrato_data"})
    contratos["contrato_data"] = pd.to_datetime(contratos["contrato_data"], errors="coerce")

    with open(RAW_DIR / "transacoes.json", "r", encoding="utf-8") as f:
        transacoes = pd.DataFrame(json.load(f))
    transacoes = transacoes.rename(columns={"valor":"transacao_valor","tipo":"transacao_tipo","data":"transacao_data"})
    transacoes["transacao_data"] = pd.to_datetime(transacoes["transacao_data"], errors="coerce")

    base_contratos = (
        contratos.merge(clientes, on="id_cliente", how="left")
                 .merge(agencias, on="id_agencia", how="left")
                 .merge(produtos, on="id_produto", how="left")
    )
    base = transacoes.merge(base_contratos, on="id_contrato", how="left")
    base["ano_mes"] = base["transacao_data"].dt.to_period("M").astype(str)
    base["ano"] = base["transacao_data"].dt.year
    base["mes"] = base["transacao_data"].dt.month
    base["dia"] = base["transacao_data"].dt.day
    base["faixa_valor_transacao"] = pd.cut(
        base["transacao_valor"],
        bins=[0,100,1000,5000,10000,10**9],
        labels=["Até 100","101-1k","1k-5k","5k-10k","10k+"],
        include_lowest=True
    ).astype(str)

    base.to_csv(PROCESSED_DIR / "base_integrada.csv", index=False, encoding="utf-8-sig")

    with sqlite3.connect(WAREHOUSE_DIR / "catalogo.db") as wh:
        base.to_sql("base_integrada", wh, if_exists="replace", index=False)
        clientes.to_sql("dim_cliente", wh, if_exists="replace", index=False)
        agencias.to_sql("dim_agencia", wh, if_exists="replace", index=False)
        produtos.to_sql("dim_produto", wh, if_exists="replace", index=False)

    quality = {
        "rows_base_integrada": int(base.shape[0]),
        "cols_base_integrada": int(base.shape[1]),
        "duplicate_rows": int(base.duplicated().sum()),
        "orphan_transactions_without_contract": int(base["cliente_nome"].isna().sum()),
        "null_percent_by_column": {c: round(float(base[c].isna().mean() * 100), 4) for c in base.columns}
    }
    with open(PROCESSED_DIR / "quality_report.json", "w", encoding="utf-8") as f:
        json.dump(quality, f, ensure_ascii=False, indent=2)

    summary = {
        "clients": int(base["id_cliente"].nunique()),
        "agencies": int(base["id_agencia"].nunique()),
        "products": int(base["id_produto"].nunique()),
        "contracts": int(base["id_contrato"].nunique()),
        "transactions": int(base["id_transacao"].nunique()),
        "transaction_value_total": round(float(base["transacao_valor"].sum()), 2)
    }
    with open(PROCESSED_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with open(LOG_DIR / "etl_last_run.json", "w", encoding="utf-8") as f:
        json.dump({"status":"success", "summary":summary}, f, ensure_ascii=False, indent=2)

    logger.info("ETL concluído com sucesso.")
    print("ETL concluído com sucesso.")

if __name__ == "__main__":
    main()
