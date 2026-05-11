
from __future__ import annotations
import hashlib
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB = BASE_DIR / "data" / "warehouse" / "auth.db"

def hp(v): return hashlib.sha256(v.encode()).hexdigest()

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("create table if not exists users (username text primary key, password_hash text, role text, full_name text)")
    cur.execute("create table if not exists audit_logs (id integer primary key autoincrement, ts text, username text, action text, detail text)")
    cur.execute("delete from users")
    cur.executemany("insert into users values (?,?,?,?)", [
        ("admin", hp("admin123"), "admin", "Administrador"),
        ("analista", hp("analista123"), "analyst", "Analista de Dados"),
        ("viewer", hp("viewer123"), "viewer", "Visualizador"),
    ])
    conn.commit()
    conn.close()
    print("Usuários padrão inicializados.")

if __name__ == "__main__":
    main()
