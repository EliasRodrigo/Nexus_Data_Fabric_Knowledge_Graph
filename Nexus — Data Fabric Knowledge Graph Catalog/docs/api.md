
# API interna

## Autenticada por sessão Flask
Após login, os endpoints abaixo retornam JSON.

### GET /api/summary
Resumo geral do catálogo.

### GET /api/quality
Métricas de qualidade da base.

### GET /api/search?q=termo&entity=all&page=1
Busca global paginada.

### GET /api/graph?focus_type=cliente&focus_id=10
Retorna nós e arestas do grafo para visualização.
