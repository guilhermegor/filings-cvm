"""Data contracts for the CVM open-data *Entrega de Documentos FI* CSVs (ingestion).

``fi_entrega_documento_AAAAMM.zip`` (dataset ``FI/DOC/ENTREGA``) is an **index of what was
delivered**, not the documents: one row per delivery of a document by a fund/class. Series
``202501`` to present, one ZIP per month, **two CSV members**:

* ``fi_entrega_documento_AAAAMM.csv`` -- every document type
  (``BALANCETE``, ``CDA``, ``PERFIL``...);
* ``fi_entrega_documento_diario_AAAAMM.csv`` -- the daily-fund report (``DIÁRIO FUNDOS``) only,
  ~14x more rows (1.4M against 103k in ``202609``).

The two members carry the **same 11-column header, byte for byte, in all 22 months measured
(``202501``-``202610``)**: there is no schema cut in this series, so there is one regime and no
``Pre*`` reader. Each member still gets its own contract, pinned to its own published header
(``tests/fixtures/entrega_fi/*_header.csv``) -- sameness is a measurement, not a licence to share
one pin -- and its own ``source_key`` so provenance tells them apart.

``Data_Inicio_Competencia`` and ``Data_Fim_Competencia`` are pure dates (ISO, 100% filled).
``Data_Hora_Entrega`` is a ``datetime`` with milliseconds (``2025-01-03 14:57:33.537``): the
coercion seam only produces a pure ``date``, so it stays **exact text**.
``ID_Documento`` is ``int`` in the META but stays text (an identifier).
``ID_Subclasse`` is ~99% empty. Only
``CNPJ_Fundo_Classe`` is a CNPJ column (14 digits, unpunctuated, 100% filled). No personal data.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


_TUPLE_COLUMNS: tuple[str, ...] = (
	"Tipo_Fundo_Classe",
	"CNPJ_Fundo_Classe",
	"ID_Subclasse",
	"Tipo_Documento",
	"Data_Inicio_Competencia",
	"Data_Fim_Competencia",
	"ID_Documento",
	"Data_Hora_Entrega",
	"Tipo_Apresentacao",
	"Ativo",
	"Sistema_Origem",
)

# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
ENTREGA_FI = FileContract(
	"Entrega de Documentos FI",
	"entrega_fi",
	_TUPLE_COLUMNS,
	("CNPJ_Fundo_Classe",),
)

ENTREGA_FI_DIARIO = FileContract(
	"Entrega de Documentos FI (diário)",
	"entrega_fi_diario",
	_TUPLE_COLUMNS,
	("CNPJ_Fundo_Classe",),
)
