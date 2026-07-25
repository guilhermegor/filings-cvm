"""Data contracts for the CVM open-data *VLMO CIA_ABERTA* CSVs (ingestion).

``vlmo_cia_aberta_AAAA.zip`` (dataset ``CIA_ABERTA/DOC/VLMO``, *Valores Mobiliários negociados e
detidos*) ships **two members that are not registry+satellite** — they are an **index** and its
**content**:

- ``vlmo_cia_aberta_AAAA.csv`` (12 cols, ~5.8k rows in 2025) — one row per **document** filed,
  same shape as IPE plus ``Motivo_Reapresentacao``, carrying a ``Link_Download``.
- ``vlmo_cia_aberta_con_AAAA.csv`` (17 cols, ~63k rows in 2025) — one row per **movement** of
  securities held by the company, its controller or its controlled entities.

Both column lists were **generated from the real 2025 headers**, not transcribed, and are pinned
to ``tests/fixtures/vlmo_cia_aberta/`` verbatim.

Three things to keep in mind, all reflected in the readers:

- ⚠️ **The money and quantity columns are the first in the ``cia_aberta/`` root**, and they stay
  **exact text**. ``Preco_Unitario`` and ``Volume`` arrive with **10 decimal places**
  (``61961072.9999543100``) and ``Quantidade`` is a plain integer; the META declares them
  ``decimal``/``decimal``/``bigint``. A binary float would destroy those digits irreversibly and
  silently — the trailing ``…99995`` is upstream float residue that must be returned **as
  published**, never re-rounded. See ``bin/check_dtypes.py``.
- ⚠️ **No personal data, despite being an insider-holdings report.** ``Empresa`` is the *company*
  (``Tipo_Empresa`` ∈ Companhia / Controlada / Controladora) and ``Tipo_Cargo`` is a *role
  category*; the individual is never named, and no CPF/CNPJ appears inside ``Empresa`` (measured).
  So ``tuple_cnpj_cols`` is the company's CNPJ in both — 100% valid, with **none** of IPE's
  all-zeros placeholder.
- ``Data_Movimentacao`` is **~58% blank** (26,328 of 63,056). It is a date column by contract;
  blanks coerce to ``NaT`` rather than raising.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
VLMO_CIA_ABERTA = FileContract(
	"VLMO CIA_ABERTA — índice dos informes de valores mobiliários",
	"vlmo_cia_aberta",
	(
		"CNPJ_Companhia",
		"Nome_Companhia",
		"Data_Referencia",
		"Versao",
		"Codigo_CVM",
		"Categoria",
		"Tipo",
		"Data_Entrega",
		"Tipo_Apresentacao",
		"Motivo_Reapresentacao",
		"Protocolo_Entrega",
		"Link_Download",
	),
	("CNPJ_Companhia",),
)

VLMO_CIA_ABERTA_CON = FileContract(
	"VLMO CIA_ABERTA — movimentações de valores mobiliários",
	"vlmo_cia_aberta_con",
	(
		"CNPJ_Companhia",
		"Nome_Companhia",
		"Data_Referencia",
		"Versao",
		"Tipo_Empresa",
		"Empresa",
		"Tipo_Cargo",
		"Tipo_Movimentacao",
		"Descricao_Movimentacao",
		"Tipo_Operacao",
		"Tipo_Ativo",
		"Caracteristica_Valor_Mobiliario",
		"Intermediario",
		"Data_Movimentacao",
		"Quantidade",
		"Preco_Unitario",
		"Volume",
	),
	("CNPJ_Companhia",),
)
