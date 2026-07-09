"""Data contract for the CVM open-data *Lâmina carteira FIF* CSV (ingestion).

The monthly Lâmina dump `lamina_fi_AAAAMM.zip` ships four CSV members; this contract
describes only `lamina_fi_carteira_AAAAMM.csv`, the fund's allocation broken down by
asset type. The other members (the lâmina proper and the two `rentab_*` series) have
their own layouts and belong to their own readers.

Verified against the real `lamina_fi_202504.zip`: the member carries exactly seven
columns, in this order. `CNPJ_FUNDO_CLASSE` arrives **masked** (`00.089.915/0001-15`);
the contract's CNPJ check unmasks before validating.

`ID_SUBCLASSE` is required as a *column* but was empty on every one of the 4,474 rows of
2025-04 — it is the seam by which CVM will identify a class's subclasses. Declaring it
here means its arrival is a value change, not a schema break.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
LAMINA_CARTEIRA_FIF = FileContract(
	"Lâmina carteira FIF",
	"lamina_carteira_fif",
	(
		"TP_FUNDO_CLASSE",
		"CNPJ_FUNDO_CLASSE",
		"ID_SUBCLASSE",
		"DENOM_SOCIAL",
		"DT_COMPTC",
		"TP_ATIVO",
		"PR_PL_ATIVO",
	),
	("CNPJ_FUNDO_CLASSE",),
)
