# **Leitura (← CVM)**

A seção `filings_cvm.ingestion` analisa e interpreta arquivos **recebidos/baixados** da CVM de
volta para modelos tipados — a contraparte do [Envio](../submission/perfil_mensal.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Status

Nenhum padrão de leitura foi implementado ainda. A seção é criada quando o primeiro padrão de
leitura chega — cada padrão ganhará aqui a sua própria página, com **Descrição** e **Exemplos**,
no mesmo formato das páginas de [Envio](../submission/informe_diario.md).

O schema compartilhado (modelos [Pydantic](https://docs.pydantic.dev/) que espelham cada padrão
XML) é neutro em relação à direção: os mesmos modelos usados no envio serão reaproveitados na
leitura. Consulte o catálogo completo de padrões (implementados e pendentes) no `CLAUDE.md` do
repositório.
