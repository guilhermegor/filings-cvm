"""CVM **META** for the FI Perfil Mensal dataset (`FI/DOC/PERFIL_MENSAL`).

The spec CVM publishes for `perfil_mensal_fi_AAAAMM.csv` — the declared description, type and size
of each field. A flat `.txt` and the **only** file in the dataset's `META/` directory (measured
from the listing); the three other spellings this portal uses elsewhere all return 404, so the URL
is constant per dataset and never derived.

⚠️ Its 107 fields equal the **post-RCVM 175** header exactly (zero on either side, measured) and
carry no `CNPJ_FUNDO`, so the META is **not** an oracle for the pre-175 106-column contract — that
one is pinned to its own published header instead.

Useful as a type oracle: it declares the five `CENARIO_FPR_*` fields `varchar(150)`, confirming
they are free text despite carrying comma-decimal numbers, and `NR_DIA_CEM_PERC` /
`NR_DIA_CINQU_PERC` `numeric(14,4)` despite the `NR_` prefix that elsewhere marks a count.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_PERFIL_MENSAL_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaPerfilMensalFiReader(BaseMetaReader):
	"""Read the META of the CVM FI Perfil Mensal dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FI/DOC/PERFIL_MENSAL/META/meta_perfil_mensal_fi.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_PERFIL_MENSAL_FI
