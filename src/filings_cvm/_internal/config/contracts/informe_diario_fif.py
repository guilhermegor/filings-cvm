"""Data contract for the CVM open-data *Informe Diário FIF* CSV (ingestion).

Declares the columns the monthly ``inf_diario_fi_AAAAMM.csv`` dump must carry and the
column that must hold valid CNPJs. The ingestion reader passes this instance to
``utils.tabular_reader.read_table``, which raises ``ContractError`` on any violation
before types are applied. Column names mirror the current (2023+ class/subclass
restructure) CVM open-data layout.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
INFORME_DIARIO_FIF = FileContract(
	"Informe Diário FIF",
	"informe_diario_fif",
	(
		"TP_FUNDO_CLASSE",
		"CNPJ_FUNDO_CLASSE",
		"ID_SUBCLASSE",
		"DT_COMPTC",
		"VL_TOTAL",
		"VL_QUOTA",
		"VL_PATRIM_LIQ",
		"CAPTC_DIA",
		"RESG_DIA",
		"NR_COTST",
	),
	("CNPJ_FUNDO_CLASSE",),
)
