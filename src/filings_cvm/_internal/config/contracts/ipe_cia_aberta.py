"""Data contract for the CVM open-data *IPE CIA_ABERTA* CSV (ingestion).

``ipe_cia_aberta_AAAA.csv`` (dataset ``CIA_ABERTA/DOC/IPE``, *Informações Periódicas e
Eventuais*) is **not a document** — it is the **index** of the documents a listed company filed
with CVM in a year: one row per delivered document, carrying the company's identity, the
reference and delivery dates, the document's taxonomy (``Categoria`` / ``Tipo`` / ``Especie`` /
``Assunto``), its delivery protocol and version, and a ``Link_Download`` pointing at the actual
document on CVM's RAD portal. The thirteen columns below were **generated from the real 2025
header**, not transcribed, and are pinned to ``tests/fixtures/ipe_cia_aberta/`` verbatim.

Four things to keep in mind, all reflected in the reader:

- **Partitioned by year** (``ipe_cia_aberta_2025.zip``) and shipped as a **ZIP of one member**
  (``ipe_cia_aberta_AAAA.csv``) — unlike DFIN, which is a loose CSV.
- ``Link_Download`` is an external URL (``rad.cvm.gov.br``). The reader returns it as text and
  **does not follow it** — fetching the linked document is a downstream concern, and the reader
  stays thin.
- ⚠️ ``CNPJ_Companhia`` legitimately carries the placeholder ``00.000.000/0000-00`` for foreign
  issuers with no Brazilian CNPJ (44 of 49,277 rows in 2025; **zero** malformed). It stays in
  ``tuple_cnpj_cols`` because that check requires *at least one* valid CNPJ, not all of them —
  and the placeholders are returned **exactly as published**, never repaired.
- ``Tipo``, ``Especie``, ``Assunto`` and ``Protocolo_Entrega`` arrive **partially filled** (a
  document's taxonomy depends on its category). They are required *columns*, not required
  *values*.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
IPE_CIA_ABERTA = FileContract(
	"IPE CIA_ABERTA — índice de informações periódicas e eventuais",
	"ipe_cia_aberta",
	(
		"CNPJ_Companhia",
		"Nome_Companhia",
		"Codigo_CVM",
		"Data_Referencia",
		"Categoria",
		"Tipo",
		"Especie",
		"Assunto",
		"Data_Entrega",
		"Tipo_Apresentacao",
		"Protocolo_Entrega",
		"Versao",
		"Link_Download",
	),
	("CNPJ_Companhia",),
)
