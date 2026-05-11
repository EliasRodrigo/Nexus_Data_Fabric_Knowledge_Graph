
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED = BASE_DIR / "data" / "processed" / "base_integrada.csv"
POWERBI = BASE_DIR / "powerbi"

def main():
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "postgres")
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    db = os.getenv("PGDATABASE", "catalogo_tcc")
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(url)

    base = pd.read_csv(PROCESSED)
    base.to_sql("base_integrada", engine, if_exists="replace", index=False)

    for name in ["dim_cliente","dim_agencia","dim_produto","dim_tempo","fato_transacoes","fato_contratos"]:
        df = pd.read_csv(POWERBI / f"{name}.csv")
        df.to_sql(name, engine, if_exists="replace", index=False)

    print("Migração para PostgreSQL concluída.")

if __name__ == "__main__":
    main()
