"""CVM VLMO CIA_ABERTA (movimentações) — ingestion (leitura) reader.

The **content** member of `vlmo_cia_aberta_AAAA.zip` (dataset `CIA_ABERTA/DOC/VLMO`): one row per
movement of securities held by the company, its controller or its controlled entities — the
position and trading disclosure behind each filed document (~63k rows in 2025 against the index's
~5.8k).

Two things worth knowing, both measured against the real 2025 bytes:

- ⚠️ **`Preco_Unitario`, `Volume` and `Quantidade` stay exact source text.** They arrive with 10
  decimal places (`61961072.9999543100`) and the META declares them `decimal`/`decimal`/`bigint`.
  Returning them as text preserves the published digits exactly; a binary float would destroy them
  irreversibly and silently. Convert to `Decimal` downstream if you need arithmetic — never to
  `float` (`bin/check_dtypes.py` enforces this).
- ⚠️ **No personal data**, despite this being an insider-holdings disclosure: `Empresa` is the
  *company* (`Tipo_Empresa` ∈ Companhia / Controlada / Controladora) and `Tipo_Cargo` is a *role
  category*. The individual is never named, and no CPF/CNPJ appears inside `Empresa`.

`Data_Movimentacao` is a date column that arrives **~58% blank** (26,328 of 63,056 rows); blanks
become `NaT` rather than raising.

Download/unzip/parse is inherited from the private `_BaseVlmoReader`.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.vlmo_cia_aberta import VLMO_CIA_ABERTA_CON
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.vlmo._base_vlmo_reader import _BaseVlmoReader


class VlmoCiaAbertaConReader(_BaseVlmoReader):
	"""Read the movements member of the CVM VLMO CIA_ABERTA yearly dump into a typed DataFrame.

	``Data_Movimentacao`` is roughly 58% blank in the real file, so a blank one becomes ``NaT``
	rather than raising.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's VLMO movements (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "vlmo_cia_aberta_con"
	_CONTRACT: ClassVar[FileContract] = VLMO_CIA_ABERTA_CON
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia", "Data_Movimentacao")
	_LABEL: ClassVar[str] = "movimentações"
