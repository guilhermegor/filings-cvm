"""CVM FRE CIA_ABERTA (faixa etária (empregados por local)) — ingestion (leitura) reader.

Age-band counts for employees, grouped by **region** (`Local`).

⚠️ **Aggregate counts, not personal data.** Despite the member name, every row is a **total per
company** and grouping — no individual is identified anywhere in it. The FRE members that do carry
personal data are the administração/pessoas ones.

Three bands: up to 30, 30–50, and above 50. ⚠️ CVM writes them without separators —
`Quantidade_Ate30Anos`, `Quantidade_30a50Anos`, `Quantidade_Acima50Anos` — and the spelling
is preserved verbatim.

`Quantidade_*` columns stay **exact source text** — counts, never a binary float; convert
downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_EMPREGADO_LOCAL_FAIXA_ETARIA,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaEmpregadoLocalFaixaEtariaReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA diversidade member into a typed DataFrame.

	Covers `faixa etária (empregados por local)`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_empregado_local_faixa_etaria"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_EMPREGADO_LOCAL_FAIXA_ETARIA
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "faixa etária (empregados por local)"
