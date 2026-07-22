"""Data contract for the CVM open-data *Cadastro de Companhias Estrangeiras* CSV (ingestion).

``cad_cia_estrang.csv`` (dataset ``CIA_ESTRANG/CAD``) is the registry **snapshot** of the foreign
companies (companhias estrangeiras) registered with the CVM. Its 49 columns are **generated from
and pinned to** the verbatim published header
(``tests/fixtures/cad_cia_estrang/cad_cia_estrang_header.csv``) — at this width, hand-transcription
is exactly the error a pinned oracle exists to catch.

A bare CSV at a **fixed URL** — CVM overwrites it in place, so there is no ``date_ref`` and a
persisted ``path_raw`` snapshot is the only record of what the registry said that day (the
``CadastroFiReader`` / ``CadastroAdmFiiReader`` precedent). The seven ``DT_*`` columns are dates;
``MOTIVO_CANCEL`` is free text (**not** a date), and every other column is exact source text.
**Two** columns hold valid CNPJs — ``CNPJ`` (the company, masked) and ``CNPJ_AUDITOR`` (its
auditor). ``RESP`` carries a legal representative's name but there is **no** CPF column.
``CD_CVM`` / ``CEP`` / ``TEL`` / ``FAX`` / ``DDD_*`` / ``CD_PAIS_*`` are ``numeric``/``char`` in
the META but stay ``str`` — they are identifiers, not quantities.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_CIA_ESTRANG = FileContract(
	"Cadastro de Companhias Estrangeiras",
	"cad_cia_estrang",
	(
		"CNPJ",
		"DENOM_SOCIAL",
		"DENOM_COMERC",
		"PAIS_ORIGEM",
		"DT_REG",
		"DT_CONST",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"CD_CVM",
		"SETOR_ATIV",
		"CATEG_REG",
		"DT_INI_CATEG",
		"SIT_EMISSOR",
		"DT_INI_SIT_EMISSOR",
		"CONTROLE_ACIONARIO",
		"TP_ENDER",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"CIDADE",
		"ESTADO",
		"PAIS",
		"CEP",
		"CD_PAIS_TEL",
		"DDD_TEL",
		"TEL",
		"CD_PAIS_FAX",
		"DDD_FAX",
		"FAX",
		"EMAIL",
		"TP_RESP",
		"RESP",
		"DT_INI_RESP",
		"LOGRADOURO_RESP",
		"COMPL_RESP",
		"BAIRRO_RESP",
		"MUN_RESP",
		"UF_RESP",
		"PAIS_RESP",
		"CEP_RESP",
		"DDD_TEL_RESP",
		"TEL_RESP",
		"DDD_FAX_RESP",
		"FAX_RESP",
		"EMAIL_RESP",
		"CNPJ_AUDITOR",
		"AUDITOR",
	),
	("CNPJ", "CNPJ_AUDITOR"),
)
