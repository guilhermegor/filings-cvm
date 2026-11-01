"""Pydantic models for the CVM Atualização do Cadastro de Ativos XML (``COD_DOC=2``).

Direction-neutral schema mirroring the submission XML described at
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAtivos.asp
(root ``DOC_ARQ`` > ``DESC_MERC`` + ``ATIVOS`` > repeated ``ROW_ATIVO``; no XML namespace).
Field names, order and cardinalities come from that page.

Rules enforced from the page: ``ACAO`` is ``I``/``A``/``R``; ``TP_ATIV`` is a Table 1 code;
``TP_EMP_EMISSORA`` a Table 2 code; dates are ``DD/MM/AAAA``; at most 1000 ``ROW_ATIVO`` per
file; the asset is identified by ``CD_ATIV`` + ``TP_ATIV`` + ``DT_INICIO_VIGEN``, so those are
always required, while the description and issuer fields are required only for an inclusion or
alteration (the page calls them "opcional para remoção de ativo"). The page states no sizes.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import (
	AfterValidator,
	BaseModel,
	Field,
	StrictInt,
	field_validator,
	model_validator,
)

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.utils.typing import type_checker
from filings_cvm._internal.utils.xml_fields import check_br_date, check_cnpj_shape


# The page also allows an unmasked CNPJ with its leading zeros omitted ("Ex.: 100").
_CNPJ_ZERO_STRIPPED_RE = re.compile(r"[0-9]{1,13}")
# C0 controls other than tab/LF/CR are not legal XML 1.0; tab/LF/CR are banned in tokens here.
_BAD_CHAR_RE = re.compile(r"[\x00-\x1f]")

# Table 1 - Tipos de Ativos (codes 16 and 25-46 are not listed by the page).
ASSET_TYPE_CODES = frozenset({*range(1, 16), *range(17, 25), 47, 48, 49})
# Table 2 - Tipos de Empresas Emissoras (the page lists "01"; no leading zeros are allowed).
ISSUER_TYPE_CODES = frozenset({0, 1, 45, 67})


@type_checker
def _check_text(value: str) -> str:
	"""Require non-blank single-line text encodable in windows-1252.

	Parameters
	----------
	value : str
		Candidate text.

	Returns
	-------
	str
		The same value.

	Raises
	------
	ValueError
		If blank, holding a control character, or not encodable in windows-1252.
	"""
	if not value.strip():
		raise ValueError("text must not be empty or blank")
	if _BAD_CHAR_RE.search(value):
		raise ValueError("text must not hold a control character, tab or line break")
	try:
		value.encode("windows-1252")
	except UnicodeEncodeError as exc:
		raise ValueError(f"character {value[exc.start]!r} is not windows-1252") from exc
	return value


@type_checker
def _validated_cnpj_input(value: str) -> str:
	"""Check a CNPJ's written shape, then its check digits, returning it bare.

	Shape runs first because the library's unmasking drops every non-alphanumeric character,
	so a stray space, newline or ``.0`` tail would otherwise be silently repaired.

	Parameters
	----------
	value : str
		Masked, bare, or bare with leading zeros omitted.

	Returns
	-------
	str
		Bare 14-character CNPJ.
	"""
	if not _CNPJ_ZERO_STRIPPED_RE.fullmatch(value):
		check_cnpj_shape(value)
	return validated_cnpj(value)


Text = Annotated[str, AfterValidator(_check_text)]
DateBr = Annotated[str, AfterValidator(check_br_date)]


class CadastroAtivosHeader(BaseModel):
	"""DESC_MERC — trading-venue block (one per file)."""

	cod_doc: Literal[2] = 2
	cnpj_merc: str
	dt_gerac_arq: DateBr

	@field_validator("cnpj_merc")
	@classmethod
	def _check_cnpj_merc(cls, v: str) -> str:
		"""Validate the venue CNPJ and store it bare.

		Parameters
		----------
		v : str
			CNPJ in any shape.

		Returns
		-------
		str
			Bare CNPJ.
		"""
		return _validated_cnpj_input(v)


class CadastroAtivosRow(BaseModel):
	"""ROW_ATIVO — one inclusion (I), alteration (A) or removal (R) of an asset."""

	acao: Literal["I", "A", "R"]
	cd_ativ: Text
	ds_ativ: Text | None = None
	tp_ativ: StrictInt
	cnpj_emp_emissora: str | None = None
	tp_emp_emissora: StrictInt | None = None
	nm_emp_emissora: Text | None = None
	ds_isin: Text | None = None
	dt_inicio_vigen: DateBr
	dt_fim_vigen: DateBr | None = None
	dt_inicio_susp: DateBr | None = None
	dt_fim_susp: DateBr | None = None

	@field_validator("tp_ativ")
	@classmethod
	def _check_tp_ativ(cls, v: int) -> int:
		"""Require a Table 1 asset-type code.

		Parameters
		----------
		v : int
			Asset-type code.

		Returns
		-------
		int
			The same code.

		Raises
		------
		ValueError
			If the code is not in Table 1.
		"""
		if v not in ASSET_TYPE_CODES:
			raise ValueError(f"tp_ativ {v} is not a Table 1 code")
		return v

	@field_validator("tp_emp_emissora")
	@classmethod
	def _check_tp_emp(cls, v: int | None) -> int | None:
		"""Require a Table 2 issuer-type code when given.

		Parameters
		----------
		v : Optional[int]
			Issuer-type code.

		Returns
		-------
		Optional[int]
			The same code.

		Raises
		------
		ValueError
			If the code is not in Table 2.
		"""
		if v is not None and v not in ISSUER_TYPE_CODES:
			raise ValueError(f"tp_emp_emissora {v} is not a Table 2 code")
		return v

	@field_validator("cnpj_emp_emissora")
	@classmethod
	def _check_cnpj_emp(cls, v: str | None) -> str | None:
		"""Validate the issuer CNPJ when given and store it bare.

		Parameters
		----------
		v : Optional[str]
			CNPJ in any shape.

		Returns
		-------
		Optional[str]
			Bare CNPJ.
		"""
		return None if v is None else _validated_cnpj_input(v)

	@model_validator(mode="after")
	def _check_required_for_acao(self) -> CadastroAtivosRow:
		"""Require the descriptive and issuer fields unless the action is a removal.

		Returns
		-------
		CadastroAtivosRow
			The validated row.

		Raises
		------
		ValueError
			If an inclusion or alteration omits a field the page makes mandatory.
		"""
		if self.acao == "R":
			return self
		required = (
			"ds_ativ",
			"cnpj_emp_emissora",
			"tp_emp_emissora",
			"nm_emp_emissora",
			"ds_isin",
		)
		missing = [name for name in required if getattr(self, name) is None]
		if missing:
			raise ValueError(f"acao {self.acao!r} requires: {', '.join(missing)}")
		return self


class CadastroAtivosDocument(BaseModel):
	"""DOC_ARQ — complete Atualização do Cadastro de Ativos document (up to 1000 rows)."""

	header: CadastroAtivosHeader
	rows: list[CadastroAtivosRow] = Field(min_length=1, max_length=1000)
