"""Data contracts for the CVM open-data *Cadastro de Plataformas de Crowdfunding* ZIP (ingestion).

``cad_crowdfunding.zip`` (dataset ``CROWDFUNDING/CAD``) ships **three members**, declared here
together (the ``cad_adm_cart.py`` / ``cad_coord_oferta.py`` precedent — members of one archive
share a module):

- ``cad_crowdfunding.csv`` — the platform registry (17 columns).
- ``cad_crowdfunding_adm_resp.csv`` — its responsible-administrator table (2 columns).
- ``cad_crowdfunding_socios.csv`` — its partners table (2 columns).

⚠️ The members are **not** a ``pf``/``pj`` split: they are a registry plus two satellite tables,
**all keyed by the platform's ``CNPJ``** — 100% valid in all three. Their columns are **generated
from and pinned to** the verbatim published headers
(``tests/fixtures/cad_crowdfunding/*_header.csv``).

⚠️ The registry is **leaner than its COORD_OFERTA / INTERMED siblings**: it has **no**
``DT_CANCEL`` / ``MOTIVO_CANCEL`` / ``CD_CVM``, and it spells the site column ``WEBSITE`` (not
``SITE_WEB``) and the area code ``DDD`` (not ``DDD_TEL``). Copying a sibling's contract would ship
the wrong columns with every test green.

A **fixed URL** — CVM overwrites the archive in place, so there is no ``date_ref`` and a persisted
``path_raw`` snapshot is the only record of what the registry said that day. ``DT_REG`` /
``DT_INI_SIT`` are dates; the two satellites carry **no date column at all**. ``ADM_RESP`` and
``SOCIO`` hold people's names (``SOCIO`` mixes natural and legal persons) but there is **no** CPF
column. ``CEP`` / ``TEL`` / ``DDD`` are ``numeric`` in the META but stay ``str`` — they are
identifiers, not quantities.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_CROWDFUNDING = FileContract(
	"Cadastro de Plataforma de Crowdfunding",
	"cad_crowdfunding",
	(
		"CNPJ",
		"DENOM_SOCIAL",
		"DENOM_COMERC",
		"DT_REG",
		"SIT",
		"DT_INI_SIT",
		"WEBSITE",
		"EMAIL",
		"TP_ENDER",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"MUN",
		"UF",
		"CEP",
		"DDD",
		"TEL",
	),
	("CNPJ",),
)

CAD_CROWDFUNDING_ADM_RESP = FileContract(
	"Cadastro de Plataforma de Crowdfunding — administradores responsáveis",
	"cad_crowdfunding_adm_resp",
	(
		"CNPJ",
		"ADM_RESP",
	),
	("CNPJ",),
)

CAD_CROWDFUNDING_SOCIOS = FileContract(
	"Cadastro de Plataforma de Crowdfunding — sócios",
	"cad_crowdfunding_socios",
	(
		"CNPJ",
		"SOCIO",
	),
	("CNPJ",),
)
