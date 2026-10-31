"""Data contracts for the CVM open-data *Complemento FI* CSVs (ingestion).

``compl_fi_AAAAMM.zip`` (dataset ``FI/DOC/COMPL``) ships **4 CSV members** -- the complementary
information funds declare about themselves (risk policy, rating agency, how information is
disclosed to unitholders, service providers). Series ``201801`` to ``201904`` (16 months), then
the dataset stops: it is a **closed** series.

⚠️ **One schema across the whole series.** The header of every member is byte-identical in all 16
months (measured), so there is one contract per member and no regime cut. The 4 members have
**different widths and different column lists**; only the leading ``TP_FUNDO`` / ``CNPJ_FUNDO`` /
``DT_COMPTC`` key block is shared.

===========================  =====  ==========================================================
member                       cols   content
===========================  =====  ==========================================================
``compl_fi``                    20  risk/voting/rating/distribution policy (long free text)
``compl_fi_inf``                 6  where/how the fund discloses information
``compl_fi_inf_cotst``           7  where/how information reaches unitholders, and who answers
``compl_fi_prest``               5  service provider description and name
===========================  =====  ==========================================================

Only ``DT_COMPTC`` is a date. ``CNPJ_FUNDO`` is 100% well-formed in every member. ``compl_fi`` has
a **second** CNPJ column, ``CNPJ_AG_RISCO`` (the rating agency), empty in ~1.6% of rows and
well-formed otherwise. No column holds a CPF. Every other column is exact source text.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


_TUPLE_KEY: tuple[str, ...] = ("TP_FUNDO", "CNPJ_FUNDO", "DT_COMPTC")

# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
COMPL_FI = FileContract(
	"Complemento FI",
	"compl_fi",
	(
		*_TUPLE_KEY,
		"PERIODO_MIN_DIVULG_CART",
		"RISCO_CART",
		"VOTO_GESTOR",
		"POLIT_VOTO",
		"TRIBUT_FUNDO_COTST",
		"POLIT_ADM_RISCO",
		"ST_AG_RISCO",
		"CNPJ_AG_RISCO",
		"AG_RISCO",
		"GRAU_RISCO",
		"DISCLAIMER_AG_RISCO",
		"APRES_ADMIN",
		"APRES_GESTOR",
		"DISTRIB_LIGADO",
		"POLIT_DISTRIB",
		"INF_AUTORREGULACAO_ANBIMA",
		"OUTRO_INF",
	),
	("CNPJ_FUNDO", "CNPJ_AG_RISCO"),
)

COMPL_FI_INF = FileContract(
	"Complemento FI — informação",
	"compl_fi_inf",
	(*_TUPLE_KEY, "MEIO_INF", "LOCAL_INF", "FORMA_INF"),
	("CNPJ_FUNDO",),
)

COMPL_FI_INF_COTST = FileContract(
	"Complemento FI — informação ao cotista",
	"compl_fi_inf_cotst",
	(*_TUPLE_KEY, "MEIO_INF_COTST", "DS_RESP_INF_COTST", "LOCAL_INF_COTST", "FORMA_INF_COTST"),
	("CNPJ_FUNDO",),
)

COMPL_FI_PREST = FileContract(
	"Complemento FI — prestador",
	"compl_fi_prest",
	(*_TUPLE_KEY, "DS_SERV_PREST", "NM_PREST_SERV"),
	("CNPJ_FUNDO",),
)
