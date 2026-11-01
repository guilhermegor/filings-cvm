"""Data contracts for the CVM open-data *Processo Sancionador* ZIP (ingestion).

``processo_sancionador.zip`` (dataset ``PROCESSO/SANCIONADOR``) ships **two members**, declared
here together (the ``cad_coord_oferta.py`` precedent — members of one archive share a module):

- ``processo_sancionador.csv`` — the sanctioning proceedings, one row per ``NUP`` (9 columns).
- ``processo_sancionador_acusado.csv`` — the accused parties of each proceeding (4 columns).

Both are keyed by ``NUP`` (*Número Único de Protocolo*): unique in the first member (581 of 581 in
the measured snapshot), repeated in the second (one row per accused). Their columns are
**generated from and pinned to** the verbatim published headers
(``tests/fixtures/processo_sancionador/*_header.csv``).

A **fixed URL** — CVM overwrites the archive in place, so there is no ``date_ref``. ``Data_*``
columns are dates; ``NUP`` is an identifier and stays text, as does every other column.

⚠️ **No column of either member holds a CNPJ or CPF**, so ``tuple_cnpj_cols`` is empty in both —
a measured decision, not an omission. ``Nome_Acusado`` is personal data (natural and legal persons
are named) but is published without a document number.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
PROCESSO_SANCIONADOR = FileContract(
	"Processo Sancionador",
	"processo_sancionador",
	(
		"NUP",
		"Objeto",
		"Ementa",
		"Data_Abertura",
		"Componente_Organizacional_Instrucao",
		"Fase_Atual",
		"Subfase_Atual",
		"Local_Atual",
		"Data_Ultima_Movimentacao",
	),
	(),
)

PROCESSO_SANCIONADOR_ACUSADO = FileContract(
	"Processo Sancionador — acusados",
	"processo_sancionador_acusado",
	(
		"NUP",
		"Nome_Acusado",
		"Situacao",
		"Data_Situacao",
	),
	(),
)
