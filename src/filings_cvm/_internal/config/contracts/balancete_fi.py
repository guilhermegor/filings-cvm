"""Data contracts for the CVM open-data *Balancete FI* CSV (ingestion).

``balancete_fi_AAAAMM.zip`` (dataset ``FI/DOC/BALANCETE``) ships a single CSV member -- the monthly
accounting trial balance of the investment funds: one row per fund/class x competency month x
account, carrying the account balance. Series ``201501`` to present, one ZIP per month.

⚠️ **The series carries TWO schemas, and the cut is MEASURED, not deduced from the regulation.**
Checked over the published headers (every month sampled 2015-2023, then every month 202302-202312):

===================  ===================  ======  =========================================
regime               months               cols    leading key block
===================  ===================  ======  =========================================
legacy               ``201501``-``202310``     5  ``CNPJ_FUNDO``
fund/class           ``202311``-present        6  ``TP_FUNDO_CLASSE`` + ``CNPJ_FUNDO_CLASSE``
===================  ===================  ======  =========================================

The cut is ``202311``: **one month before** the ``202312`` cut of the Perfil Mensal, so it
cannot be inherited from it (nor named after RCVM 175 -- a name is a claim). The 4 trailing
columns are identical across regimes, but each contract is still pinned to its own published
header (``tests/fixtures/balancete_fi/*_header.csv``).

⚠️ **Not a copy of** :data:`BALANCETE_FIE`: the FIE contract has the same 6 columns as the
fund/class regime here, but belongs to a different dataset; each is pinned to its own source.

⚠️ **The META describes only the fund/class regime** (6 fields, no ``CNPJ_FUNDO``), so it is not
an oracle for the legacy contract.

``VL_SALDO_BALCTE`` (``numeric(23,2)``, negatives present) and ``CD_CONTA_BALCTE`` (``char(8)``)
stay exact source text. Only ``DT_COMPTC`` is a date. Only ``CNPJ_FUNDO[_CLASSE]`` is a CNPJ
column, and it is 100% well-formed in every month measured.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# The 4 columns both regimes share, in published order, after the key block.
_TUPLE_SHARED_TAIL: tuple[str, ...] = (
	"DT_COMPTC",
	"PLANO_CONTA_BALCTE",
	"CD_CONTA_BALCTE",
	"VL_SALDO_BALCTE",
)

# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
BALANCETE_FI = FileContract(
	"Balancete FI",
	"balancete_fi",
	("TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE", *_TUPLE_SHARED_TAIL),
	("CNPJ_FUNDO_CLASSE",),
)

BALANCETE_FI_PRE202311 = FileContract(
	"Balancete FI (pre-202311)",
	"balancete_fi_pre202311",
	("CNPJ_FUNDO", *_TUPLE_SHARED_TAIL),
	("CNPJ_FUNDO",),
)
