"""Data contract for the CVM open-data *DFIN CRI* index CSV (ingestion).

``dfin_cri_AAAA.csv`` (dataset ``SECURIT/DOC/DFIN_CRI``) is the **index of financial statements of
the CRI** (Certificados de Recebíveis Imobiliários) delivered by securitisation issuers — one row
per document, not the statement itself. Verified against the real file (``2025``): the 9 columns
below are exactly as published, in order. Structurally identical to :data:`DFIN_CRA` — the only
difference is the certificate type (imobiliário vs agronegócio), reflected in the dataset, not the
columns.

Partitioned by year, a **plain CSV** (not a ZIP). ``Link_Download`` points at the actual document
on B3's fnet portal; the reader returns it as text and does **not** follow it (``DfinFiiReader``
precedent). Keyed loosely by ``CNPJ_Emissora``; no unique key.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
DFIN_CRI = FileContract(
	"DFIN CRI",
	"dfin_cri",
	(
		"CNPJ_Emissora",
		"Nome_Emissora",
		"Data_Referencia",
		"Versao",
		"Data_Entrega",
		"Nome_Certificado",
		"Codigo_Identificacao_Certificado",
		"Link_Download",
		"Parecer_Auditor",
	),
	("CNPJ_Emissora",),
)
