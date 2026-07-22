"""Data contract for the CVM open-data *Cadastro de Companhias Abertas* CSV (ingestion).

``cad_cia_aberta.csv`` (dataset ``CIA_ABERTA/CAD``) is the registry **snapshot** of the publicly
held companies (companhias abertas) registered with the CVM. Its 47 columns are **generated from
and pinned to** the verbatim published header
(``tests/fixtures/cad_cia_aberta/cad_cia_aberta_header.csv``) — at this width, hand-transcription
is exactly the error a pinned oracle exists to catch.

Close to ``CAD_CIA_ESTRANG`` / ``CAD_CIA_INCENT`` but **not** a copy: its issuer key is
``CNPJ_CIA`` (not ``CNPJ``), and it adds ``TP_MERC`` (market type). A bare CSV at a **fixed URL** —
CVM overwrites it in place, so there is no ``date_ref`` and a persisted ``path_raw`` snapshot is
the only record of what the registry said that day. The seven ``DT_*`` columns are dates;
``MOTIVO_CANCEL`` is free
text (**not** a date), and every other column is exact source text. **Two** columns hold valid
CNPJs — ``CNPJ_CIA`` (the company) and ``CNPJ_AUDITOR`` (its auditor). ``RESP`` carries a legal
representative's name but there is **no** CPF column. ``CD_CVM`` / ``CEP`` / ``TEL`` / ``FAX`` /
``DDD_*`` are ``numeric``/``char`` in the META but stay ``str`` — they are identifiers, not
quantities.

Inaugurates the ``cia_aberta/`` portal root — the last and largest of the #41 sweep. This contract
covers **only** the ``CAD`` registry; the seven ``DOC`` financial-statement datasets and the
``EVENTOS`` sub-root each get their own contracts.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_CIA_ABERTA = FileContract(
	"Cadastro de Companhia Aberta",
	"cad_cia_aberta",
	(
		"CNPJ_CIA",
		"DENOM_SOCIAL",
		"DENOM_COMERC",
		"DT_REG",
		"DT_CONST",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"CD_CVM",
		"SETOR_ATIV",
		"TP_MERC",
		"CATEG_REG",
		"DT_INI_CATEG",
		"SIT_EMISSOR",
		"DT_INI_SIT_EMISSOR",
		"CONTROLE_ACIONARIO",
		"TP_ENDER",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"MUN",
		"UF",
		"PAIS",
		"CEP",
		"DDD_TEL",
		"TEL",
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
	("CNPJ_CIA", "CNPJ_AUDITOR"),
)
