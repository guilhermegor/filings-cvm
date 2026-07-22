"""Data contract for the CVM open-data *Cadastro de Administrador de FII* CSV (ingestion).

``cad_adm_fii.csv`` (dataset ``ADM_FII/CAD``) is the registry **snapshot** of the entities
registered to administer Fundos de Investimento Imobiliário (FII). Verified against the real
file: the 18 columns below are exactly as published, in source order.

A bare CSV at a **fixed URL** — CVM overwrites it in place, so there is no ``date_ref`` and a
persisted ``path_raw`` snapshot is the only record of what the registry said that day (the
``CadastroFiReader`` / ``CadastroEmissorCepacReader`` precedent). ``DT_REG`` / ``DT_CANCEL`` /
``DT_INI_SIT`` are dates; ``MOTIVO_CANCEL`` is free text (**not** a date), and every other column
is exact source text. Keyed by ``CNPJ`` (the administrator is an institution); there is **no**
CPF column. ``CEP`` / ``DDD`` / ``TEL`` are ``numeric`` in the META but stay ``str`` — they are
identifiers, not quantities.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_ADM_FII = FileContract(
	"Cadastro de Administrador de FII",
	"cad_adm_fii",
	(
		"CNPJ",
		"DENOM_SOCIAL",
		"DENOM_COMERC",
		"DT_REG",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"TP_ENDER",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"MUN",
		"UF",
		"CEP",
		"DDD",
		"TEL",
		"EMAIL",
	),
	("CNPJ",),
)
