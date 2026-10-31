"""Data contract for the CVM open-data *Atos Declaratorios* CSV (ingestion).

``ato_declr.csv`` (dataset ``ATO_DECLR/INTERMED``) lists the CVM declaratory acts that suspend
irregular securities intermediation. Its 7 columns are **generated from and pinned to** the
verbatim published header (``tests/fixtures/ato_declr/ato_declr_header.csv``).

A bare ``;``-separated ISO-8859-1 CSV at a **fixed URL**: CVM overwrites it in place, so there is
no ``date_ref``. ``Data_Ato_Declaratorio`` and ``Data_Publicacao_DOU`` are ISO dates;
``Numero_Ato_Declaratorio`` is ``numeric`` in the META but stays ``str`` (an identifier).

``CNPJ_CPF`` holds a masked CNPJ **or** a masked CPF (or nothing — 252 of 914 rows are blank, and
one CNPJ arrives unmasked and without its leading zero), so it is **not** a CNPJ column and
``tuple_cnpj_cols`` is empty. ``Denominacao`` carries the names of natural persons, hence the
header-only fixture. ``Link_Download`` is returned as text, never followed.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
ATO_DECLR = FileContract(
	"Atos Declaratórios",
	"ato_declr",
	(
		"Numero_Ato_Declaratorio",
		"Data_Ato_Declaratorio",
		"Denominacao",
		"Data_Publicacao_DOU",
		"CNPJ_CPF",
		"Link_Download",
		"Observacao",
	),
	(),
)
