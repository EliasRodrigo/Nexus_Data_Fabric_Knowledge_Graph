# Nexus — Data Fabric Knowledge Graph Catalog

> Prova de Conceito desenvolvida como Trabalho de Conclusão de Curso
> **TCC530 · Turma 2 · Grupo 4 · Ciência de Dados · UNIVESP 2026**
> Orientador: Felipe Ivo da Silva

---

## Sobre o projeto

Demonstração técnica da **unificação semântica de metadados** provenientes
de fontes heterogêneas (CSV, Excel, JSON e SQLite) por meio da construção
automatizada de um **Grafo de Conhecimento** orientado à arquitetura
**Data Fabric**.

O sistema integra:
- Pipeline **ETL** automatizado em Python
- Modelagem **ontológica** (RDF/OWL) com classes e propriedades de objeto
- **Catálogo ativo** de dados com busca global unificada
- **Dashboard** analítico com gráficos interativos
- **Grafo interativo** de relacionamentos entre entidades
- Camadas de **governança** e **qualidade** de dados
- Área administrativa com controle do pipeline e auditoria

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.10+ |
| Web Framework | Flask |
| ETL / Análise | Pandas · NetworkX |
| Banco de dados | SQLite |
| Visualização | Chart.js · vis-network |
| Frontend | HTML5 · CSS3 · Jinja2 |

---

## Como rodar

### 1. Clonar o repositório
```bash
git clone https://github.com/seu-usuario/Nexus_Data_Fabric_Knowledge_Graph.git
cd Nexus_Data_Fabric_Knowledge_Graph
```

### 2. Instalar dependências
```bash
pip install flask pandas networkx openpyxl
```

### 3. Iniciar
```bash
python run.py
```

Acesse **http://127.0.0.1:5000**

> Caso os bancos de dados não existam, execute primeiro:
> ```bash
> python setup.py
> ```

---

## Credenciais de teste

| Usuário | Senha | Perfil |
|---|---|---|
| admin | admin123 | Administrador |
| analista | analista123 | Analista |
| viewer | viewer123 | Visualizador |

---

## Estrutura do projeto

```
├── run.py                     # Ponto de entrada
├── setup.py                   # Inicialização dos bancos
├── app/
│   ├── app.py                 # Rotas Flask
│   ├── services/
│   │   ├── data_service.py    # Lógica de dados e grafo
│   │   └── auth_service.py    # Autenticação e auditoria
│   ├── templates/             # HTML Jinja2
│   └── static/style.css       # CSS tema Data Fabric
├── data/
│   ├── raw/                   # Fontes brutas (CSV, Excel, JSON, SQLite)
│   ├── processed/             # Relatórios de qualidade
│   └── warehouse/             # Banco integrado (catalogo.db, auth.db)
└── src/
    ├── etl/build_base.py      # Pipeline ETL completo
    └── security/init_auth.py  # Criação de usuários
```

---

## Ontologia fundacional

```
:Cliente    rdfs:subClassOf  :Entidade
:Agência    rdfs:subClassOf  :Entidade
:Produto    rdfs:subClassOf  :Entidade
:Contrato   rdfs:subClassOf  :Entidade

:pertence_a   Contrato → Cliente
:usa_produto  Contrato → Produto
:vinculado_a  Contrato → Agência
:associado_a  Cliente  → Agência
```

---

## Referências

- HOGAN et al. *Knowledge Graphs*. ACM Computing Surveys, 2021.
- NARGESIAN et al. *Data Lake Management*. VLDB, 2019.
- JONKER; KRANTZ. *What is a Data Fabric?* IBM, s.d.
- LENZERINI, M. *Data Integration: a theoretical perspective*. ACM, 2002.
