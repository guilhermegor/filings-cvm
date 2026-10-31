"""Pydantic models for the CVM Informe de Fundo 157 XML standard.

Direction-neutral schema for ``PadraoXMLInf157.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInf157.asp). The ``submission``
section builds these models and serialises them to XML.

**Field order is the XML order.** Each field is the lower-cased tag from the page and sits where
the page's sample file puts it; the writer walks ``model_fields`` in declaration order.

The page carries no decimal field. What it leaves unsaid is decided here and stated on
``docs/submission/inf_fundo_157.md``: the format of ``DT_FIM``, the cardinality of ``COTST`` and
the length of a CPF.
"""

from __future__ import annotations

from functools import partial
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from filings_cvm._internal.config.schemas._fields import validate_person_doc, validated_cnpj
from filings_cvm._internal.utils.xml_fields import (
	check_br_date,
	check_cnpj_shape,
	check_month_year,
	check_xml_text,
)


CnpjField = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]
CompetenceField = Annotated[str, AfterValidator(check_month_year)]
DateField = Annotated[str, AfterValidator(check_br_date)]
# "CPF do cotista, sem pontos e traços": exactly 11 ASCII digits (\A..\z, no trailing newline),
# then the check digits.
CpfField = Annotated[
	str,
	Field(pattern=r"\A[0-9]{11}\z"),
	AfterValidator(partial(validate_person_doc, "PF")),
]
# "Nome do cotista. Máximo de 200 caracteres."
_NAME_MAX = 200
NameField = Annotated[
	str,
	StringConstraints(min_length=1, max_length=_NAME_MAX),
	AfterValidator(check_xml_text),
]


class InfFundo157Block(BaseModel):
	"""Base of every Informe 157 block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class InfFundo157Header(InfFundo157Block):
	"""DESC_FDO_157 — the fund block (exactly one per file)."""

	cod_doc: Literal[55] = 55
	cnpj_fdo_157: CnpjField
	dt_gerac_arq: DateField
	dt_comptc: CompetenceField


class InfFundo157Cotista(InfFundo157Block):
	"""COTST — one shareholder (repeating block)."""

	cpf: CpfField
	nome: NameField
	dt_fim: DateField
	conf: Literal["S", "N"]


class InfFundo157Document(InfFundo157Block):
	"""DOC_ARQ — the whole file: the fund block and its shareholders (``LISTA_COTSTS``).

	``cotistas`` is a tuple, not a list: ``frozen`` blocks reassignment but not in-place
	mutation, so a list could be emptied after validation, behind ``min_length``.
	"""

	header: InfFundo157Header
	cotistas: Annotated[tuple[InfFundo157Cotista, ...], Field(min_length=1)]
