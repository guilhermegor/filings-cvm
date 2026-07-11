"""Data contracts for the project's input files (config layer).

A contract is **declarative configuration** of an input's expected shape — which columns a
source must carry, which must hold valid CNPJs — *not* data access, so contracts live in
``config`` beside the other declarative config (``inputs.yaml``, ``connection_db``), imported
by the model loaders and the controller boundary.

Convention: **one file per source** under this package (``cadastro.py``, ``orders.py``, …),
each defining a single ``FileContract`` instance; this aggregator re-exports them (plus the
machinery from ``utils.tabular_reader``) so callers import from one place:
``from config.contracts import EXAMPLE_SOURCE, find_file_problems``.

``EXAMPLE_SOURCE`` is a reference instance — copy ``example_source.py`` per real source and
delete the example once your own contracts exist.
"""

from __future__ import annotations

from filings_cvm._internal.config.contracts.cad_fi import CAD_FI
from filings_cvm._internal.config.contracts.cad_fi_hist import (
	CAD_FI_HIST_ADMIN,
	CAD_FI_HIST_AUDITOR,
	CAD_FI_HIST_CLASSE,
	CAD_FI_HIST_CONDOM,
	CAD_FI_HIST_CONTROLADOR,
	CAD_FI_HIST_CUSTODIANTE,
	CAD_FI_HIST_DENOM_COMERC,
	CAD_FI_HIST_DENOM_SOCIAL,
	CAD_FI_HIST_DIRETOR_RESP,
	CAD_FI_HIST_EXCLUSIVO,
	CAD_FI_HIST_EXERC_SOCIAL,
	CAD_FI_HIST_FIC,
	CAD_FI_HIST_GESTOR,
	CAD_FI_HIST_PUBLICO_ALVO,
	CAD_FI_HIST_RENTAB,
	CAD_FI_HIST_SIT,
	CAD_FI_HIST_TAXA_ADM,
	CAD_FI_HIST_TAXA_PERFM,
	CAD_FI_HIST_TRIB_LPRAZO,
)
from filings_cvm._internal.config.contracts.cda_fif import CDA_FIF
from filings_cvm._internal.config.contracts.example_source import EXAMPLE_SOURCE
from filings_cvm._internal.config.contracts.inf_mensal_fidc import (
	INF_MENSAL_FIDC_TAB_I,
	INF_MENSAL_FIDC_TAB_II,
	INF_MENSAL_FIDC_TAB_III,
	INF_MENSAL_FIDC_TAB_IV,
	INF_MENSAL_FIDC_TAB_IX,
	INF_MENSAL_FIDC_TAB_V,
	INF_MENSAL_FIDC_TAB_VI,
	INF_MENSAL_FIDC_TAB_VII,
	INF_MENSAL_FIDC_TAB_X,
	INF_MENSAL_FIDC_TAB_X_1,
	INF_MENSAL_FIDC_TAB_X_1_1,
	INF_MENSAL_FIDC_TAB_X_2,
	INF_MENSAL_FIDC_TAB_X_3,
	INF_MENSAL_FIDC_TAB_X_4,
	INF_MENSAL_FIDC_TAB_X_5,
	INF_MENSAL_FIDC_TAB_X_6,
	INF_MENSAL_FIDC_TAB_X_7,
)
from filings_cvm._internal.config.contracts.informe_diario_fif import INFORME_DIARIO_FIF
from filings_cvm._internal.config.contracts.lamina_carteira_fif import LAMINA_CARTEIRA_FIF
from filings_cvm._internal.config.contracts.lamina_fif import LAMINA_FIF
from filings_cvm._internal.config.contracts.registro_classe import REGISTRO_CLASSE
from filings_cvm._internal.config.contracts.registro_fundo import REGISTRO_FUNDO
from filings_cvm._internal.config.contracts.registro_subclasse import REGISTRO_SUBCLASSE
from filings_cvm._internal.utils.tabular_reader import (
	ContractError,
	FileContract,
	find_file_problems,
)


__all__ = [
	"CAD_FI",
	"CAD_FI_HIST_ADMIN",
	"CAD_FI_HIST_AUDITOR",
	"CAD_FI_HIST_CLASSE",
	"CAD_FI_HIST_CONDOM",
	"CAD_FI_HIST_CONTROLADOR",
	"CAD_FI_HIST_CUSTODIANTE",
	"CAD_FI_HIST_DENOM_COMERC",
	"CAD_FI_HIST_DENOM_SOCIAL",
	"CAD_FI_HIST_DIRETOR_RESP",
	"CAD_FI_HIST_EXCLUSIVO",
	"CAD_FI_HIST_EXERC_SOCIAL",
	"CAD_FI_HIST_FIC",
	"CAD_FI_HIST_GESTOR",
	"CAD_FI_HIST_PUBLICO_ALVO",
	"CAD_FI_HIST_RENTAB",
	"CAD_FI_HIST_SIT",
	"CAD_FI_HIST_TAXA_ADM",
	"CAD_FI_HIST_TAXA_PERFM",
	"CAD_FI_HIST_TRIB_LPRAZO",
	"CDA_FIF",
	"EXAMPLE_SOURCE",
	"INFORME_DIARIO_FIF",
	"INF_MENSAL_FIDC_TAB_I",
	"INF_MENSAL_FIDC_TAB_II",
	"INF_MENSAL_FIDC_TAB_III",
	"INF_MENSAL_FIDC_TAB_IV",
	"INF_MENSAL_FIDC_TAB_IX",
	"INF_MENSAL_FIDC_TAB_V",
	"INF_MENSAL_FIDC_TAB_VI",
	"INF_MENSAL_FIDC_TAB_VII",
	"INF_MENSAL_FIDC_TAB_X",
	"INF_MENSAL_FIDC_TAB_X_1",
	"INF_MENSAL_FIDC_TAB_X_1_1",
	"INF_MENSAL_FIDC_TAB_X_2",
	"INF_MENSAL_FIDC_TAB_X_3",
	"INF_MENSAL_FIDC_TAB_X_4",
	"INF_MENSAL_FIDC_TAB_X_5",
	"INF_MENSAL_FIDC_TAB_X_6",
	"INF_MENSAL_FIDC_TAB_X_7",
	"LAMINA_CARTEIRA_FIF",
	"LAMINA_FIF",
	"REGISTRO_CLASSE",
	"REGISTRO_FUNDO",
	"REGISTRO_SUBCLASSE",
	"ContractError",
	"FileContract",
	"find_file_problems",
]
