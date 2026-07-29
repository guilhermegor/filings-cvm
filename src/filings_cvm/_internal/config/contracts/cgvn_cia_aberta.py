"""Data contracts for the CVM open-data *CGVN CIA_ABERTA* CSVs (ingestion).

`cgvn_cia_aberta_AAAA.zip` (dataset `CIA_ABERTA/DOC/CGVN`, *Informe sobre o Código Brasileiro de
Governança Corporativa*) ships **two members** — an **index** and its **content**, the VLMO shape:

- `cgvn_cia_aberta_AAAA.csv` (12 cols, 382 rows in 2025) — one row per informe filed, with a
  `Link_Download` returned as text and never followed.
- `cgvn_cia_aberta_praticas_AAAA.csv` (11 cols, **19,980** rows) — one row per recommended
  practice, whether the company adopted it, and its free-text explanation.

Both column lists were **generated from the real 2025 headers**, not transcribed, and are pinned to
`tests/fixtures/cgvn_cia_aberta/` verbatim.

⚠️ **The index here uses the CamelCase convention** (`CNPJ_Companhia` / `Data_Referencia` /
`Nome_Empresarial` / `ID_Documento`) — it does **not** repeat the sibling FCA's uppercase
`CNPJ_CIA` / `DT_REFER` index. FCA was the exception in this sub-root, not the rule, which is why
every dataset is grounded on its own bytes rather than generalised from a neighbour.

⚠️ **`Codigo_CVM` arrives zero-padded** (`001023`), so typing it as text is load-bearing here — an
int cast would silently yield `1023`. `ID_Item` is hierarchical (`1.1.1`) and likewise stays text.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.

CGVN_CIA_ABERTA = FileContract(
	"CGVN CIA_ABERTA — índice dos informes de governança",
	"cgvn_cia_aberta",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"Nome_Empresarial",
		"ID_Documento",
		"Codigo_CVM",
		"Categoria",
		"Data_Entrega",
		"Link_Download",
		"Data_Inicio_Exercicio_Social",
		"Data_Fim_Exercicio_Social",
		"Motivo_Reapresentacao",
	),
	("CNPJ_Companhia",),
)

CGVN_CIA_ABERTA_PRATICAS = FileContract(
	"CGVN CIA_ABERTA — práticas de governança",
	"cgvn_cia_aberta_praticas",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"Nome_Empresarial",
		"ID_Documento",
		"ID_Item",
		"Capitulo",
		"Principio",
		"Pratica_Recomendada",
		"Pratica_Adotada",
		"Explicacao",
	),
	("CNPJ_Companhia",),
)
