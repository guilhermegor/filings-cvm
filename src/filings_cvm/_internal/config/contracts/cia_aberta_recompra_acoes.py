"""Data contracts for the CVM open-data *RECOMPRA_ACOES* CSVs (ingestion) — all 3 members.

`cia_aberta_recompra_acoes.zip` (dataset `CIA_ABERTA/EVENTOS/RECOMPRA_ACOES`) is the registry of
**share buy-back programmes**: the programme itself (11 columns, 1.916 rows), the brokers engaged
in it (3 columns, 4.269 rows) and the counts per share type and class (5 columns, 2.381 rows). All
three join on `ID_Programa`, which is unique in the registry and repeats in the satellites.

Every column list is **generated from the real headers**, not transcribed, and pinned verbatim to
`tests/fixtures/cia_aberta_recompra_acoes/`.

⚠️⚠️ **`quantidades` declares NO CNPJ column** — the member genuinely has none, identifying only
the programme it belongs to. The empty `tuple_cnpj_cols` is a measured fact, not an omission; the
sibling members declare `CNPJ_Companhia` and `CNPJ_Intermediario` respectively, both 100% valid.

⚠️ **This dataset is a snapshot** (fixed URL, no year), so its readers take no `date_ref`, and its
columns are **CamelCase**, unlike the `CNPJ_CIA` / `DT_REFER` of the `DOC` datasets in the
same root.

⚠️ Several columns arrive **partially empty** — `Classe_Acao` in 2.322 of 2.381 rows (ordinary
shares have no class), and `Tipo_Operacao`, `Motivo`, `Finalidade_Compra` and both
`Quantidade_Acoes_*` in the registry. Blank stays blank, never a placeholder or a zero.

`ID_Programa` and the `Quantidade_*` columns are identifiers and counts, so they stay exact text;
see `bin/check_dtypes.py`.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.

CIA_ABERTA_RECOMPRA_ACOES = FileContract(
	"RECOMPRA_ACOES — programas de recompra",
	"cia_aberta_recompra_acoes",
	(
		"ID_Programa",
		"CNPJ_Companhia",
		"Nome_Companhia",
		"Data_Deliberacao",
		"Data_Final_Prazo",
		"Situacao",
		"Tipo_Operacao",
		"Motivo",
		"Finalidade_Compra",
		"Quantidade_Acoes_Ordinarias",
		"Quantidade_Acoes_Preferenciais",
	),
	("CNPJ_Companhia",),
)

CIA_ABERTA_RECOMPRA_ACOES_INTERMEDIARIOS = FileContract(
	"RECOMPRA_ACOES — intermediários do programa",
	"cia_aberta_recompra_acoes_intermediarios",
	(
		"ID_Programa",
		"CNPJ_Intermediario",
		"Intermediario",
	),
	("CNPJ_Intermediario",),
)

CIA_ABERTA_RECOMPRA_ACOES_QUANTIDADES = FileContract(
	"RECOMPRA_ACOES — quantidades por tipo e classe de ação",
	"cia_aberta_recompra_acoes_quantidades",
	(
		"ID_Programa",
		"Tipo_Acao",
		"Classe_Acao",
		"Quantidade_Circulacao",
		"Quantidade_Operacao",
	),
	(),
)
