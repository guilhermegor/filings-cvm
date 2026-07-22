"""Data contracts for the CVM open-data *Cadastro de Coordenadores de Oferta* ZIP (ingestion).

``cad_coord_oferta.zip`` (dataset ``COORD_OFERTA/CAD``) ships **two members**, declared here
together (the ``cad_intermed.py`` precedent — members of one archive share a module):

- ``cad_coord_oferta.csv`` — the offering-coordinator registry (25 columns).
- ``cad_coord_oferta_resp.csv`` — its responsible-officer table (6 columns).

⚠️ The two members are **not** a ``pf``/``pj`` split (unlike the AUDITOR / AGENTE_FIDUC / INVNR
mould): they are two related tables of the same registry, **both keyed by the coordinator's
``CNPJ``** — 100% valid in both members. Their columns are **generated from and pinned to** the
verbatim published headers (``tests/fixtures/cad_coord_oferta/*_header.csv``).

A **fixed URL** — CVM overwrites the archive in place, so there is no ``date_ref`` and a persisted
``path_raw`` snapshot is the only record of what the registry said that day. ``DT_*`` columns are
dates; ``MOTIVO_CANCEL`` is free text (**not** a date), and every other column is exact source
text. ``RESP`` carries an officer's name but there is **no** CPF column. ``CD_CVM`` / ``CEP`` /
``TEL`` / ``FAX`` / ``DDD_*`` are ``numeric``/``char`` in the META but stay ``str`` — they are
identifiers, not quantities.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_COORD_OFERTA = FileContract(
	"Cadastro de Coordenador de Oferta",
	"cad_coord_oferta",
	(
		"CNPJ",
		"DENOM_SOCIAL",
		"DENOM_COMERC",
		"DT_REG",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"CD_CVM",
		"SETOR_ATIV",
		"VL_PATRIM_LIQ",
		"DT_PATRIM_LIQ",
		"TP_ENDER",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"MUN",
		"UF",
		"CEP",
		"DDD_TEL",
		"TEL",
		"DDD_FAX",
		"FAX",
		"EMAIL",
		"SITE_WEB",
	),
	("CNPJ",),
)

CAD_COORD_OFERTA_RESP = FileContract(
	"Cadastro de Coordenador de Oferta — responsáveis",
	"cad_coord_oferta_resp",
	(
		"CNPJ",
		"DENOM_SOCIAL",
		"DT_REG",
		"TP_RESP",
		"RESP",
		"DT_INI_RESP",
	),
	("CNPJ",),
)
