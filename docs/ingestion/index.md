# **Leitura (← CVM)**

A seção `filings_cvm.ingestion` analisa e interpreta arquivos **recebidos/baixados** da CVM de
volta para modelos tipados — a contraparte do [Envio](../submission/perfil_mensal.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Padrões implementados

- **[Informe Diário FIF](informe_diario.md)** — `InformeDiarioReader`: lê o dump mensal de
  *open-data* (`inf_diario_fi_AAAAMM`) e devolve um `DataFrame` tipado e validado por contrato.

Cada padrão de leitura ganha a sua própria página, com **Descrição** e **Exemplos**, no mesmo
formato das páginas de [Envio](../submission/informe_diario.md).

## Forma de um leitor

Todo leitor implementa o **port** `read() -> pd.DataFrame` (o contrato compartilhado, privado, em
`_internal/ports`) e devolve um `DataFrame` cujas colunas são tipadas explicitamente — nunca pela
inferência do pandas. Leitores de *open-data* (CSV) declaram o seu próprio contrato de colunas e
**não** reaproveitam o schema Pydantic de submissão, pois consomem um artefato distinto do XML.
Consulte o catálogo completo de padrões (implementados e pendentes) no `CLAUDE.md` do repositório.
