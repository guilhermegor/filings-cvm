"""Data contract for the CVM open-data *Cadastro de Companhias Incentivadas* CSV (ingestion).

``cad_cia_incent.csv`` (dataset ``CIA_INCENT/CAD``) is the registry **snapshot** of the
incentivised companies (companhias incentivadas) registered with the CVM. Its 47 columns are
**generated from and pinned to** the verbatim published header
(``tests/fixtures/cad_cia_incent/cad_cia_incent_header.csv``) — at this width, hand-transcription
is exactly the error a pinned oracle exists to catch.

Close to ``CAD_CIA_ESTRANG`` but **not** a copy: it adds ``ST_CIA_INCENT_REG``, drops
``PAIS_ORIGEM`` / ``CD_PAIS_*``, and uses ``MUN`` / ``UF`` (domestic) rather than ``CIDADE`` /
``ESTADO``.

A bare CSV at a **fixed URL** — CVM overwrites it in place, so there is no ``date_ref`` and a
persisted ``path_raw`` snapshot is the only record of what the registry said that day. The seven
``DT_*`` columns are dates; ``MOTIVO_CANCEL`` is free text (**not** a date), and every other
column is exact source text. **Two** columns hold valid CNPJs — ``CNPJ`` (the company) and
``CNPJ_AUDITOR`` (its auditor). ``RESP`` carries a legal representative's name but there is **no**
CPF column.
``CD_CVM`` / ``CEP`` / ``TEL`` / ``FAX`` / ``DDD_*`` are ``numeric``/``char`` in the META but
stay ``str`` — they are identifiers, not quantities.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_CIA_INCENT = FileContract(
	"Cadastro de Companhias Incentivadas",
	"cad_cia_incent",
	(
		"CNPJ",
		"ST_CIA_INCENT_REG",
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
	("CNPJ", "CNPJ_AUDITOR"),
)
