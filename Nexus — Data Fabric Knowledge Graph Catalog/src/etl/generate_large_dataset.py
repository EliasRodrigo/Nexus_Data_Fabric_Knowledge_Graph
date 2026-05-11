
from __future__ import annotations
import json, random, sqlite3
from pathlib import Path
import pandas as pd
from faker import Faker

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "data" / "raw_enterprise"

def main():
    fake = Faker("pt_BR")
    random.seed(42)

    clientes = []
    for i in range(1, 3001):
        clientes.append({
            "id_cliente": i,
            "nome": fake.name(),
            "cpf": fake.cpf(),
            "email": fake.email(),
            "telefone": fake.phone_number(),
            "endereco": fake.address().replace("\n", ", ")
        })
    pd.DataFrame(clientes).to_csv(OUT_DIR / "clientes.csv", index=False)

    print("Base enterprise gerada com sucesso.")

if __name__ == "__main__":
    main()
