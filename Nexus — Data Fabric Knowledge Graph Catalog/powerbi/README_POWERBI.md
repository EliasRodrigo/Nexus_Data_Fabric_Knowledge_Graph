
# Power BI - Guia de conexão

## Opção 1: Conectar pelos CSVs
Use os arquivos:
- dim_cliente.csv
- dim_agencia.csv
- dim_produto.csv
- dim_tempo.csv
- fato_transacoes.csv
- fato_contratos.csv

## Relacionamentos sugeridos
- fato_transacoes[id_cliente] -> dim_cliente[id_cliente]
- fato_transacoes[id_agencia] -> dim_agencia[id_agencia]
- fato_transacoes[id_produto] -> dim_produto[id_produto]
- fato_transacoes[data_key] -> dim_tempo[data_key]
- fato_contratos[id_cliente] -> dim_cliente[id_cliente]
- fato_contratos[id_agencia] -> dim_agencia[id_agencia]
- fato_contratos[id_produto] -> dim_produto[id_produto]
- fato_contratos[data_key] -> dim_tempo[data_key]

## Opção 2: Conectar no SQLite
Banco: `data/warehouse/catalogo.db`

## Opção 3: Conectar no PostgreSQL
Execute `src/db/migrate_to_postgres.py` e conecte no schema padrão.

## Páginas recomendadas no dashboard
1. Visão executiva
2. Produtos e contratos
3. Agências e valor movimentado
4. Qualidade de dados
5. Clientes e comportamento transacional
