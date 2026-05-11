"""
setup.py — executa o ETL e inicializa os bancos de dados.
Rode uma vez antes de iniciar a aplicação:
    python setup.py
"""
import subprocess, sys, os
from pathlib import Path

BASE = Path(__file__).resolve().parent
etl  = BASE / "src" / "etl" / "build_base.py"
auth = BASE / "src" / "security" / "init_auth.py"

print("=" * 50)
print("  DATA FABRIC CATALOG — Setup inicial")
print("=" * 50)

if not (BASE / "data" / "warehouse" / "catalogo.db").exists():
    print("\n[1/2] Executando ETL (pode demorar ~30s)...")
    r = subprocess.run([sys.executable, str(etl)], cwd=str(BASE))
    if r.returncode != 0:
        print("  ERRO no ETL. Verifique os arquivos em data/raw/")
        sys.exit(1)
    print("  ETL concluído.")
else:
    print("\n[1/2] catalogo.db já existe — ETL ignorado.")

if not (BASE / "data" / "warehouse" / "auth.db").exists():
    print("\n[2/2] Inicializando banco de autenticação...")
    r = subprocess.run([sys.executable, str(auth)], cwd=str(BASE))
    if r.returncode != 0:
        print("  ERRO na criação do auth.db.")
        sys.exit(1)
    print("  auth.db criado.")
else:
    print("\n[2/2] auth.db já existe — ignorado.")

print("\n✓ Setup concluído. Execute:  python run.py")
print("  Acesse: http://127.0.0.1:5000")
print("  Login:  admin / admin123")
