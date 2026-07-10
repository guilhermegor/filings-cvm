"""CVM CAD/FI histórico — taxa de performance change-log reader.

The ``cad_fi_hist_taxa_perfm.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
performance fee. ``VL_TAXA_PERFM`` is kept as exact source text (never ``float``). This member
has an opening effective date (``DT_INI_TAXA_PERFM``) but **no** closing date column. See
``_base_cad_fi_hist_reader`` for shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_TAXA_PERFM, FileContract
from filings_cvm.ingestion.fi.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistTaxaPerfmReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *taxa de performance* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_taxa_perfm.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_TAXA_PERFM
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_TAXA_PERFM")
	_LABEL: ClassVar[str] = "taxa de performance"
