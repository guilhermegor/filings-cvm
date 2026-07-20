"""Contracts for the CVM **META** artifacts — one per dataset.

Unlike every other contract here, ``tuple_required`` does **not** describe a CVM artifact's
columns: the META is block text, not a table, so the parsed frame's shape is **ours** and is
identical for all 24 datasets. What genuinely differs is ``str_source_key`` — which is exactly what
``stamp_provenance`` writes onto every row so a datalake can tell two datasets apart when they land
in one bronze table. Hence a factory over a shared tuple rather than 22 hand-copied literals.

Consolidating many contracts in one module follows the ``cad_fi_hist.py`` precedent (19 members of
one archive in one file).

The ``meta_`` prefix on every source key is load-bearing: without it, ``META_DFIN_CRA`` and the
``DfinCraReader``'s own contract would both stamp ``dfin_cra`` and become indistinguishable
downstream — the precise ambiguity ``source_key`` exists to prevent.
"""

from __future__ import annotations

from filings_cvm._internal.utils.meta_parser import RECORD_COLUMNS
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm._internal.utils.typing import type_checker


# The parsed META frame's source columns, in order. Imported from the parser that produces them, so
# the shape has ONE definition and the contract cannot drift from the records it validates.
# The six provenance columns are appended later by `stamp_provenance` and are deliberately NOT here
# (tuple_required validates the parsed source; provenance is added after).
META_COLUMNS: tuple[str, ...] = RECORD_COLUMNS


@type_checker
def _meta_contract(str_dataset: str, str_label: str) -> FileContract:
	"""Build the contract for one dataset's META.

	Parameters
	----------
	str_dataset : str
		The dataset slug (e.g. ``"inf_mensal_cra"``); ``meta_``-prefixed to form the source key.
	str_label : str
		Human-readable label for logs and notifications.

	Returns
	-------
	FileContract
		Contract carrying the shared :data:`META_COLUMNS` and this dataset's unique source key.
	"""
	return FileContract(
		str_name=str_label,
		str_source_key=f"meta_{str_dataset}",
		tuple_required=META_COLUMNS,
		tuple_cnpj_cols=(),
	)


META_INF_DIARIO_FI = _meta_contract("inf_diario_fi", "META — Informe Diário FI")
META_CDA_FI = _meta_contract("cda_fi", "META — CDA FI")
META_LAMINA_FI = _meta_contract("lamina_fi", "META — Lâmina FI")
META_CAD_FI = _meta_contract("cad_fi", "META — Cadastro FI")
META_CAD_FI_HIST = _meta_contract("cad_fi_hist", "META — Cadastro FI histórico")
META_REGISTRO_FUNDO_CLASSE = _meta_contract(
	"registro_fundo_classe", "META — Registro fundo/classe/subclasse"
)
META_INF_MENSAL_FIDC = _meta_contract("inf_mensal_fidc", "META — Informe Mensal FIDC")
META_INF_MENSAL_FII = _meta_contract("inf_mensal_fii", "META — Informe Mensal FII")
META_DFIN_FII = _meta_contract("dfin_fii", "META — DFIN FII")
META_INF_TRIMESTRAL_FII = _meta_contract("inf_trimestral_fii", "META — Informe Trimestral FII")
META_INF_ANUAL_FII = _meta_contract("inf_anual_fii", "META — Informe Anual FII")
META_INF_TRIMESTRAL_FIP = _meta_contract("inf_trimestral_fip", "META — Informe Trimestral FIP")
META_INF_QUADRIMESTRAL_FIP = _meta_contract(
	"inf_quadrimestral_fip", "META — Informe Quadrimestral FIP"
)
META_INF_MENSAL_FIAGRO = _meta_contract("inf_mensal_fiagro", "META — Informe Mensal FIAGRO")
META_BALANCETE_FIE = _meta_contract("balancete_fie", "META — Balancete FIE")
META_BALANCO_FIE = _meta_contract("balanco_fie", "META — Balanço FIE")
META_MEDIDAS_MES_FIE = _meta_contract("medidas_mes_fie", "META — Medidas Mensais FIE")
META_DFIN_CRA = _meta_contract("dfin_cra", "META — DFIN CRA")
META_DFIN_CRI = _meta_contract("dfin_cri", "META — DFIN CRI")
META_INF_MENSAL_OTS = _meta_contract("inf_mensal_ots", "META — Informe Mensal OTS")
META_INF_MENSAL_CRA = _meta_contract("inf_mensal_cra", "META — Informe Mensal CRA")
META_INF_MENSAL_CRI = _meta_contract("inf_mensal_cri", "META — Informe Mensal CRI")
META_CAD_EMISSOR_CEPAC = _meta_contract("cad_emissor_cepac", "META — Cadastro Emissor CEPAC")
META_CAD_AUDITOR = _meta_contract("cad_auditor", "META — Cadastro Auditor")
META_CAD_AGENTE_AUTON = _meta_contract("cad_agente_auton", "META — Cadastro Agente Autônomo")
META_CAD_AGENTE_FIDUC = _meta_contract("cad_agente_fiduc", "META — Cadastro Agente Fiduciário")
META_CAD_INVNR_REPRES = _meta_contract(
	"cad_invnr_repres", "META — Cadastro Representante de Investidor Não Residente"
)
META_CAD_INTERMED = _meta_contract("cad_intermed", "META — Cadastro Intermediário")
