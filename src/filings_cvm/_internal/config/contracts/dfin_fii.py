"""Data contract for the CVM open-data *DFIN FII* CSV (ingestion).

``dfin_fii_AAAA.csv`` (dataset ``FII/DOC/DFIN``) is **not a financial statement** — it is the
**index** of the financial statements a FII delivered in a year: one row per delivered document,
carrying the fund's identity, the reference and delivery dates, the auditor's opinion, and a
``Link_Download`` pointing at the actual statement on B3's fnet portal. Verified against the real
file (``2025``): the eight columns below are exactly as published, in order.

Two things to keep in mind, both reflected in the reader:

- **Partitioned by year** (``dfin_fii_2025.csv``), and a **plain CSV**, not a ZIP.
- ``Link_Download`` is an external URL (``fnet.bmfbovespa.com.br``). The reader returns it as text
  and **does not follow it** — fetching the linked statement is a downstream concern, and the
  reader stays thin.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
DFIN_FII = FileContract(
	"DFIN FII — índice das demonstrações financeiras",
	"dfin_fii",
	(
		"Tipo_Fundo_Classe",
		"CNPJ_Fundo_Classe",
		"Nome_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Data_Entrega",
		"Link_Download",
		"Parecer_Auditor",
	),
	("CNPJ_Fundo_Classe",),
)
