import subprocess, sys, sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
print("=" * 50)
print("  NEXUS — Data Fabric Knowledge Graph Catalog")
print("=" * 50)

def db_valido(path):
    try:
        with sqlite3.connect(str(path)) as c:
            return c.execute("SELECT COUNT(*) FROM base_integrada").fetchone()[0] > 0
    except:
        return False

db = BASE / "data" / "warehouse" / "catalogo.db"
if not db.exists() or not db_valido(db):
    print("\n[1/2] Executando ETL...")
    r = subprocess.run([sys.executable, str(BASE / "src" / "etl" / "build_nexus.py")], cwd=str(BASE))
    if r.returncode != 0:
        print("ERRO no ETL."); sys.exit(1)
else:
    print("\n[1/2] catalogo.db OK.")

print("\n[2/2] Criando usuários...")
r = subprocess.run([sys.executable, str(BASE / "src" / "security" / "init_auth.py")], cwd=str(BASE))

print("\n✅ Pronto! Execute: python run.py")
print("   http://127.0.0.1:5000")
print("   admin / admin123")
