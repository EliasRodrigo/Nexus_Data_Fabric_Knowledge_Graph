# Nexus — Data Fabric Knowledge Graph Catalog · Grupo 4 · UNIVESP 2026

**Unificação Semântica de Metadados em Ambientes Heterogêneos**  
Construção Automatizada de Grafos de Conhecimento orientada ao Data Fabric.

## Como rodar

### Requisitos
- Python 3.10 ou superior
- pip

### 1. Instalar dependências
```bash
pip install flask pandas networkx openpyxl
```

### 2. (Opcional) Reconstruir os bancos de dados a partir dos dados brutos
> Só necessário se os arquivos `data/warehouse/catalogo.db` e `data/warehouse/auth.db` não existirem.
```bash
python setup.py
```

### 3. Iniciar a aplicação
```bash
python run.py
```

Acesse: **http://127.0.0.1:5000**

### Usuários de teste
| Usuário   | Senha        | Perfil    |
|-----------|--------------|-----------|
| admin     | admin123     | Admin     |
| analista  | analista123  | Analista  |
| viewer    | viewer123    | Visualizador |

## Estrutura do projeto
```
Nexus — Data Fabric Knowledge Graph Catalog/
├── run.py                        # Ponto de entrada
├── setup.py                      # Setup inicial (cria DBs)
├── app/
│   ├── app.py                    # Rotas Flask
│   ├── services/
│   │   ├── data_service.py       # Lógica de dados
│   │   └── auth_service.py       # Autenticação e auditoria
│   ├── templates/                # HTML (Jinja2)
│   └── static/style.css          # CSS tema Data Fabric
├── data/
│   ├── raw/                      # Fontes originais (CSV, Excel, JSON, SQLite)
│   ├── raw_enterprise/           # Dataset maior
│   ├── processed/                # quality_report.json, summary.json
│   └── warehouse/                # catalogo.db, auth.db
├── src/etl/build_base.py         # Pipeline ETL completo
└── src/security/init_auth.py     # Inicialização de usuários
```
