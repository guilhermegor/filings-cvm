"""Data contract for the CVM open-data *CDA FIF* CSVs (ingestion).

The CDA (Composição e Diversificação das Aplicações) monthly dump `cda_fi_AAAAMM.zip`
holds **several** CSV blocks (BLC_1…BLC_8, one per asset-type layout, plus PL). This
contract declares only the columns **every** block shares — the identifying keys — so the
same contract validates each block before the blocks are consolidated into one frame.
Block-specific columns vary and are kept as text (see `ingestion/cda.py`).

Verified against the real `cda_fi_202504.zip`: all ten members carry exactly these four
columns as their leading fields. `CNPJ_FUNDO_CLASSE` arrives **masked**
(`00.071.477/0001-68`); the contract's CNPJ check unmasks before validating.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CDA_FIF = FileContract(
	"CDA FIF",
	"cda_fif",
	(
		"TP_FUNDO_CLASSE",
		"CNPJ_FUNDO_CLASSE",
		"DENOM_SOCIAL",
		"DT_COMPTC",
	),
	("CNPJ_FUNDO_CLASSE",),
)
