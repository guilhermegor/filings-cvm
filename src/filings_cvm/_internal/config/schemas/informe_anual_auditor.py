"""Pydantic models for the CVM Informe Anual de Auditor XML standard.

Direction-neutral schema for ``PadraoXMLAuditorAnual.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAuditorAnual.asp). The
``submission`` section builds these models and serialises them to XML.

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and
names each element ``<FIELD_NAME.upper()>``; a ``lista_*`` field is a container whose repeated
element is the name without the prefix (``lista_ender`` -> ``<LISTA_ENDER><ENDER>``).

What the page leaves unsaid is decided here and stated on
``docs/submission/informe_anual_auditor.md``. Money and percentages carry the two decimal
places the page states; the entity-name length and a few optionality choices are this library's
assumptions.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
	AfterValidator,
	BaseModel,
	BeforeValidator,
	ConfigDict,
	Field,
	StringConstraints,
	ValidationInfo,
	field_validator,
	model_validator,
)

from filings_cvm._internal.config.schemas._fields import validate_person_doc, validated_cnpj
from filings_cvm._internal.utils.rule_check import raise_first
from filings_cvm._internal.utils.xml_fields import (
	check_br_date,
	check_cnpj_shape,
	check_long_digits,
	check_xml_text,
	parse_br_date,
	strict_decimal,
)
from filings_cvm._internal.utils.xml_fields_digits import (
	check_cep,
	check_cpf_shape,
	check_single_email,
)


_MONEY_SCALE = 2
_PERCENT_SCALE = 2
_DIGITS = 18
_PERCENT_MAX = Decimal(100)
# The page: PR_FATURA is reported only "quando for superior a 10%".
_PR_FATURA_FLOOR = Decimal(10)
_LONG_MAX = 9223372036854775807

_MoneyField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_MONEY_SCALE)),
	Field(ge=Decimal(0), max_digits=_DIGITS, decimal_places=_MONEY_SCALE),
]
_PercentField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_PERCENT_SCALE)),
	Field(ge=Decimal(0), le=_PERCENT_MAX, max_digits=_DIGITS, decimal_places=_PERCENT_SCALE),
]
# Share of billing, reported only above 10%.
_BillingShareField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_PERCENT_SCALE)),
	Field(
		gt=_PR_FATURA_FLOOR,
		le=_PERCENT_MAX,
		max_digits=_DIGITS,
		decimal_places=_PERCENT_SCALE,
	),
]

_CountField = Annotated[int, Field(strict=True, ge=0, le=_LONG_MAX)]
_CodeField = Annotated[int, Field(strict=True, ge=1, le=_LONG_MAX)]
_YearField = Annotated[int, Field(strict=True, ge=1900, le=9999)]
_DateField = Annotated[str, AfterValidator(check_br_date)]
_DigitsField = Annotated[str, AfterValidator(check_long_digits)]
_CepField = Annotated[str, AfterValidator(check_cep)]
_CnpjField = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]

_XML_TEXT = AfterValidator(check_xml_text)
_Text18 = Annotated[str, StringConstraints(min_length=1, max_length=18), _XML_TEXT]
_Text30 = Annotated[str, StringConstraints(min_length=1, max_length=30), _XML_TEXT]
_Text100 = Annotated[str, StringConstraints(min_length=1, max_length=100), _XML_TEXT]
_Text200 = Annotated[str, StringConstraints(min_length=1, max_length=200), _XML_TEXT]
_Text500 = Annotated[str, StringConstraints(min_length=1, max_length=500), _XML_TEXT]
_EmailField = Annotated[
	str,
	StringConstraints(min_length=1, max_length=50),
	_XML_TEXT,
	AfterValidator(check_single_email),
]

# Table A upload limits (the page leaves courses and representatives unbounded for upload).
_MAX_ADDRESSES = 1000
_MAX_AUDITED = 8000
_MAX_AFFILIATED = 1000

# Table B — audited-entity types (the 48 codes the page lists).
AUDITED_ENTITY_TYPES = frozenset(
	{
		1, 5, 7, 14, 17, 20, 22, 23, 25, 27, 30, 32, 43, 45, 47, 48, 50, 52, 55, 57, 60, 61, 63,
		67, 69, 70, 72, 73, 74, 75, 77, 80, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95,
		96, 98, 99,
	}
)  # fmt: skip
# Table D — training types.
TRAINING_TYPES = frozenset({1, 2, 3, 4, 5, 6, 999})
# Table C — job types: 1-3 belong to a legal-entity auditor (AIPJ), 4 to a natural person (AIPF).
_PF_JOB = 4
_PJ_JOBS = frozenset({1, 2, 3})


class AuditorBlock(BaseModel):
	"""Base of every block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class AuditorHeader(AuditorBlock):
	"""DS_INFORM — document header."""

	ano_base: _YearField
	dt_gerac_arq: _DateField
	motivo_entreg: Literal[1, 2, 3]


class AuditorIdentity(AuditorBlock):
	"""DS_AUDIT — the auditor."""

	tp_pf_pj: Literal["PF", "PJ"]
	nr_pf_pj: str
	cd_cvm: _CodeField
	ds_nome: _Text100
	ds_email: _EmailField

	@field_validator("nr_pf_pj")
	@classmethod
	def _check_document(cls, value: str, info: ValidationInfo) -> str:
		"""Require a CPF for ``PF`` and a CNPJ for ``PJ`` and return the bare digits.

		Parameters
		----------
		value : str
			The document text, bare or masked.
		info : ValidationInfo
			Carries the already-validated ``tp_pf_pj``.

		Returns
		-------
		str
			The unmasked, check-digit-validated document.

		Raises
		------
		ValueError
			If the shape or the check digits do not match the person type.
		"""
		kind = info.data.get("tp_pf_pj")
		if kind is None:
			return value
		(check_cpf_shape if kind == "PF" else check_cnpj_shape)(value)
		return validate_person_doc(kind, value)


class AuditorAddress(AuditorBlock):
	"""ENDER — head office (1) or branch (2)."""

	tp_ender: Literal[1, 2]
	nm_filial: _Text100 | None = None
	nm_lograd: _Text30
	ds_compl: _Text18 | None = None
	ds_bairro: _Text30
	cd_mun: _CodeField
	nr_cep: _CepField
	nr_ddd_tel: _DigitsField | None = None
	nr_tel: _DigitsField | None = None
	nr_ddd_fax: _DigitsField | None = None
	nr_fax: _DigitsField | None = None

	@model_validator(mode="after")
	def _check_rules(self) -> AuditorAddress:
		"""Enforce branch-name and phone/fax pairing rules.

		Returns
		-------
		AuditorAddress
			The same instance.

		Raises
		------
		ValueError
			If a head office carries a branch name, a branch lacks one, or a DDD lacks its
			number (or the reverse).
		"""
		raise_first(
			[
				(
					self.tp_ender == 1 and self.nm_filial is not None,
					"NM_FILIAL must be omitted for the head office (TP_ENDER=1)",
				),
				(
					self.tp_ender == 2 and self.nm_filial is None,  # noqa: PLR2004
					"NM_FILIAL is required for a branch (TP_ENDER=2)",
				),
				(
					(self.nr_ddd_tel is None) != (self.nr_tel is None),
					"NR_DDD_TEL and NR_TEL must be given together",
				),
				(
					(self.nr_ddd_fax is None) != (self.nr_fax is None),
					"NR_DDD_FAX and NR_FAX must be given together",
				),
			]
		)
		return self


class AuditorRepresentative(AuditorBlock):
	"""RESP — a partner who represents the firm (personal data: CPF)."""

	nr_pf: str
	ds_nome: _Text100
	ds_email: _EmailField

	@field_validator("nr_pf")
	@classmethod
	def _check_cpf(cls, value: str) -> str:
		"""Validate the CPF shape and check digits and return the bare digits.

		Parameters
		----------
		value : str
			The CPF text.

		Returns
		-------
		str
			The unmasked CPF.
		"""
		check_cpf_shape(value)
		return validate_person_doc("PF", value)


class AuditedEntity(AuditorBlock):
	"""ENTID_AUDITA — one audited entity."""

	tp_entid: Annotated[int, Field(strict=True)]
	nr_pj: _CnpjField
	ds_nome: _Text100
	dt_contr: _DateField | None = None
	pr_fatura: _BillingShareField | None = None

	@field_validator("tp_entid")
	@classmethod
	def _check_type(cls, value: int) -> int:
		"""Require a Table B code.

		Parameters
		----------
		value : int
			The entity-type code.

		Returns
		-------
		int
			The same code.

		Raises
		------
		ValueError
			If it is not in Table B (also rejects ``bool``).
		"""
		if isinstance(value, bool) or value not in AUDITED_ENTITY_TYPES:
			raise ValueError("TP_ENTID must be a Table B code")
		return value


class AuditorAnnualBilling(AuditorBlock):
	"""FATURA_ANUAL — audit billing and hours."""

	vl_audit: _MoneyField
	pr_audit: _PercentField
	hh_audit: _CountField


class AuditorStaff(AuditorBlock):
	"""RH — partners and technical staff."""

	qt_socios: _CountField | None = None
	qt_func_tecno: _CountField


class AffiliatedEntity(AuditorBlock):
	"""ENTID_COLIG — an affiliated entity."""

	st_estr: Literal["S", "N"]
	nr_pj: _CnpjField | None = None
	ds_nome: _Text100
	ds_setor_ativd: _Text30

	@model_validator(mode="after")
	def _check_cnpj(self) -> AffiliatedEntity:
		"""Require a CNPJ exactly when the entity is not foreign.

		Returns
		-------
		AffiliatedEntity
			The same instance.

		Raises
		------
		ValueError
			If a foreign entity carries a CNPJ or a national one lacks it.
		"""
		raise_first(
			[
				(
					self.st_estr == "S" and self.nr_pj is not None,
					"NR_PJ must be omitted for a foreign entity (ST_ESTR=S)",
				),
				(
					self.st_estr == "N" and self.nr_pj is None,
					"NR_PJ is required for a national entity (ST_ESTR=N)",
				),
			]
		)
		return self


class TrainingParticipant(AuditorBlock):
	"""TREINA_PESSOA — a person who took the training."""

	ds_nome_pessoa: _Text100
	tp_cargo: Literal[1, 2, 3, 4]


class AuditorTraining(AuditorBlock):
	"""TREINA — one course, seminar or training."""

	ds_nome_treina: _Text100
	tp_treina: Annotated[int, Field(strict=True)]
	ds_treina: _Text200 | None = None
	lista_treina_pessoa: Annotated[list[TrainingParticipant], Field(min_length=1)]

	@field_validator("tp_treina")
	@classmethod
	def _check_type(cls, value: int) -> int:
		"""Require a Table D code.

		Parameters
		----------
		value : int
			The training-type code.

		Returns
		-------
		int
			The same code.

		Raises
		------
		ValueError
			If it is not in Table D (also rejects ``bool``).
		"""
		if isinstance(value, bool) or value not in TRAINING_TYPES:
			raise ValueError("TP_TREINA must be a Table D code")
		return value


class InformeAnualAuditorDocument(AuditorBlock):
	"""DOC_ARQ — a complete Informe Anual de Auditor file (one auditor, one base year)."""

	cod_doc: Literal[23] = 23
	ds_inform: AuditorHeader
	ds_audit: AuditorIdentity
	lista_ender: Annotated[list[AuditorAddress], Field(min_length=1, max_length=_MAX_ADDRESSES)]
	lista_resp: list[AuditorRepresentative] = Field(default_factory=list)
	lista_entid_audita: Annotated[list[AuditedEntity], Field(max_length=_MAX_AUDITED)] = Field(
		default_factory=list
	)
	qt_outra_entid_audita: _CountField
	fatura_anual: AuditorAnnualBilling
	ds_criter_honor: _Text500
	rh: AuditorStaff
	lista_entid_colig: Annotated[list[AffiliatedEntity], Field(max_length=_MAX_AFFILIATED)] = (
		Field(default_factory=list)
	)
	lista_treina: list[AuditorTraining] = Field(default_factory=list)

	@model_validator(mode="after")
	def _check_person_type_rules(self) -> InformeAnualAuditorDocument:
		"""Enforce the blocks that depend on the auditor being PF or PJ, and date coherence.

		Returns
		-------
		InformeAnualAuditorDocument
			The same instance.

		Raises
		------
		ValueError
			If a natural-person auditor has more than one address, representatives or partners;
			a legal-entity auditor lacks a partner count; a job type does not match the person
			type; or the base year is after the file's generation year.
		"""
		is_pf = self.ds_audit.tp_pf_pj == "PF"
		raise_first(
			[
				(
					is_pf and (len(self.lista_ender) != 1 or self.lista_ender[0].tp_ender != 1),
					"a PF auditor sends exactly one address, the head office",
				),
				(is_pf and bool(self.lista_resp), "LISTA_RESP must be omitted for a PF auditor"),
				(
					is_pf and self.rh.qt_socios is not None,
					"QT_SOCIOS must be omitted for a PF auditor",
				),
				(
					not is_pf and self.rh.qt_socios is None,
					"QT_SOCIOS is required for a PJ auditor",
				),
				(
					any(
						(person.tp_cargo == _PF_JOB) != is_pf
						or (not is_pf and person.tp_cargo not in _PJ_JOBS)
						for training in self.lista_treina
						for person in training.lista_treina_pessoa
					),
					"TP_CARGO must be 4 (AIPF) for PF and 1-3 (AIPJ) for PJ",
				),
				(
					self.ds_inform.ano_base > parse_br_date(self.ds_inform.dt_gerac_arq).year,
					"ANO_BASE cannot be after the year of DT_GERAC_ARQ",
				),
			]
		)
		return self
