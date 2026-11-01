"""Unit tests for the Informe Anual de Auditor submission writer.

Tag lists are typed from the CVM page (PadraoXMLAuditorAnual.asp), not derived from the schema.
CPFs below are the well-known synthetic test numbers, never real people.
"""

import contextlib
from decimal import Decimal
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET  # noqa: S405  # parses our own test output

from pydantic import ValidationError
import pytest

from filings_cvm._internal.config.schemas.informe_anual_auditor import (
	AUDITED_ENTITY_TYPES,
	TRAINING_TYPES,
)
from filings_cvm.submission import (
	AffiliatedEntity,
	AuditedEntity,
	AuditorAddress,
	AuditorAnnualBilling,
	AuditorHeader,
	AuditorIdentity,
	AuditorRepresentative,
	AuditorStaff,
	AuditorTraining,
	InformeAnualAuditor,
	InformeAnualAuditorDocument,
	TrainingParticipant,
)


NS = "{urn:audtanual}"
CNPJ_A = "11222333000181"
CNPJ_B = "11444777000161"
CPF = "11144477735"


def _address(**kw: Any) -> AuditorAddress:  # noqa: ANN401
	base: dict[str, Any] = {
		"tp_ender": 1,
		"nm_lograd": "Rua Exemplo",
		"ds_bairro": "Centro",
		"cd_mun": 3550308,
		"nr_cep": "01001000",
	}
	base.update(kw)
	return AuditorAddress(**base)


def _doc(pf: bool = False, **kw: Any) -> InformeAnualAuditorDocument:  # noqa: ANN401
	base: dict[str, Any] = {
		"ds_inform": AuditorHeader(ano_base=2024, dt_gerac_arq="15/04/2025", motivo_entreg=1),
		"ds_audit": AuditorIdentity(
			tp_pf_pj="PF" if pf else "PJ",
			nr_pf_pj=CPF if pf else CNPJ_A,
			cd_cvm=123,
			ds_nome="Auditor Exemplo",
			ds_email="a@exemplo.com.br",
		),
		"lista_ender": [_address()],
		"qt_outra_entid_audita": 3,
		"fatura_anual": AuditorAnnualBilling(vl_audit="1000.50", pr_audit="80", hh_audit=900),
		"ds_criter_honor": "Horas trabalhadas.",
		"rh": AuditorStaff(qt_func_tecno=10)
		if pf
		else AuditorStaff(qt_socios=2, qt_func_tecno=10),
	}
	base.update(kw)
	return InformeAnualAuditorDocument(**base)


def _full_pj() -> InformeAnualAuditorDocument:
	return _doc(
		lista_ender=[
			_address(
				ds_compl="Sala 1",
				nr_ddd_tel="11",
				nr_tel="30000000",
				nr_ddd_fax="11",
				nr_fax="30000001",
			),
			_address(tp_ender=2, nm_filial="Filial RJ"),
		],
		lista_resp=[
			AuditorRepresentative(nr_pf="111.444.777-35", ds_nome="Socio", ds_email="s@e.com.br")
		],
		lista_entid_audita=[
			AuditedEntity(
				tp_entid=1,
				nr_pj=CNPJ_B,
				ds_nome="Cia Auditada",
				dt_contr="01/02/2024",
				pr_fatura="12.345",
			)
		],
		lista_entid_colig=[
			AffiliatedEntity(st_estr="N", nr_pj=CNPJ_B, ds_nome="Colig", ds_setor_ativd="Bancos"),
			AffiliatedEntity(st_estr="S", ds_nome="Foreign", ds_setor_ativd="Seguros"),
		],
		lista_treina=[
			AuditorTraining(
				ds_nome_treina="Curso",
				tp_treina=1,
				ds_treina="Descricao",
				lista_treina_pessoa=[TrainingParticipant(ds_nome_pessoa="Ana", tp_cargo=1)],
			)
		],
	)


def _tags(el: ET.Element) -> list[str]:
	return [c.tag.removeprefix(NS) for c in el]


def _at(root: ET.Element, path: str) -> ET.Element:
	"""Find ``A/B[2]/C`` below ``root`` (namespace added to every segment)."""
	found = root.find("/".join(f"{NS}{seg}" for seg in path.split("/")))
	return found  # type: ignore[return-value]


def _xml(doc: InformeAnualAuditorDocument) -> str:
	return InformeAnualAuditor().export(doc) or ""


def _root(doc: InformeAnualAuditorDocument) -> ET.Element:
	xml = InformeAnualAuditor().export(doc)
	assert xml is not None
	return ET.fromstring(xml.encode("windows-1252"))  # noqa: S314


def _id(**kw: Any) -> AuditorIdentity:  # noqa: ANN401
	base: dict[str, Any] = {
		"tp_pf_pj": "PJ",
		"nr_pf_pj": CNPJ_A,
		"cd_cvm": 1,
		"ds_nome": "N",
		"ds_email": "a@b.com",
	}
	return AuditorIdentity(**{**base, **kw})


def _header(**kw: Any) -> AuditorHeader:  # noqa: ANN401
	base: dict[str, Any] = {"ano_base": 2024, "dt_gerac_arq": "15/04/2025", "motivo_entreg": 1}
	return AuditorHeader(**{**base, **kw})


def _entity(**kw: Any) -> AuditedEntity:  # noqa: ANN401
	base: dict[str, Any] = {"tp_entid": 1, "nr_pj": CNPJ_B, "ds_nome": "N"}
	return AuditedEntity(**{**base, **kw})


def _billing(**kw: Any) -> AuditorAnnualBilling:  # noqa: ANN401
	base: dict[str, Any] = {"vl_audit": "1", "pr_audit": "1", "hh_audit": 1}
	return AuditorAnnualBilling(**{**base, **kw})


def _affiliated(**kw: Any) -> AffiliatedEntity:  # noqa: ANN401
	base: dict[str, Any] = {"st_estr": "S", "ds_nome": "N", "ds_setor_ativd": "S"}
	return AffiliatedEntity(**{**base, **kw})


def _training(**kw: Any) -> AuditorTraining:  # noqa: ANN401
	person = TrainingParticipant(ds_nome_pessoa="P", tp_cargo=1)
	base: dict[str, Any] = {
		"ds_nome_treina": "C",
		"tp_treina": 1,
		"lista_treina_pessoa": [person],
	}
	return AuditorTraining(**{**base, **kw})


def _pf_training(cargo: int) -> AuditorTraining:
	return _training(lista_treina_pessoa=[TrainingParticipant(ds_nome_pessoa="P", tp_cargo=cargo)])


_ADDRESS_TAGS = [
	"TP_ENDER", "NM_LOGRAD", "DS_COMPL", "DS_BAIRRO", "CD_MUN", "NR_CEP",
	"NR_DDD_TEL", "NR_TEL", "NR_DDD_FAX", "NR_FAX",
]  # fmt: skip


@pytest.mark.parametrize(
	("path", "expected"),
	[
		(".", ["COD_DOC", "INFORM_AUDIT"]),
		(
			"INFORM_AUDIT",
			[
				"DS_INFORM",
				"DS_AUDIT",
				"LISTA_ENDER",
				"LISTA_RESP",
				"LISTA_ENTID_AUDITA",
				"QT_OUTRA_ENTID_AUDITA",
				"FATURA_ANUAL",
				"DS_CRITER_HONOR",
				"RH",
				"LISTA_ENTID_COLIG",
				"LISTA_TREINA",
			],
		),
		("INFORM_AUDIT/DS_INFORM", ["ANO_BASE", "DT_GERAC_ARQ", "MOTIVO_ENTREG"]),
		("INFORM_AUDIT/DS_AUDIT", ["TP_PF_PJ", "NR_PF_PJ", "CD_CVM", "DS_NOME", "DS_EMAIL"]),
		("INFORM_AUDIT/LISTA_ENDER", ["ENDER", "ENDER"]),
		("INFORM_AUDIT/LISTA_ENDER/ENDER[1]", _ADDRESS_TAGS),
		(
			"INFORM_AUDIT/LISTA_ENDER/ENDER[2]",
			["TP_ENDER", "NM_FILIAL", "NM_LOGRAD", "DS_BAIRRO", "CD_MUN", "NR_CEP"],
		),
		("INFORM_AUDIT/LISTA_RESP/RESP", ["NR_PF", "DS_NOME", "DS_EMAIL"]),
		(
			"INFORM_AUDIT/LISTA_ENTID_AUDITA/ENTID_AUDITA",
			["TP_ENTID", "NR_PJ", "DS_NOME", "DT_CONTR", "PR_FATURA"],
		),
		("INFORM_AUDIT/FATURA_ANUAL", ["VL_AUDIT", "PR_AUDIT", "HH_AUDIT"]),
		("INFORM_AUDIT/RH", ["QT_SOCIOS", "QT_FUNC_TECNO"]),
		(
			"INFORM_AUDIT/LISTA_ENTID_COLIG/ENTID_COLIG[1]",
			["ST_ESTR", "NR_PJ", "DS_NOME", "DS_SETOR_ATIVD"],
		),
		(
			"INFORM_AUDIT/LISTA_ENTID_COLIG/ENTID_COLIG[2]",
			["ST_ESTR", "DS_NOME", "DS_SETOR_ATIVD"],
		),
		(
			"INFORM_AUDIT/LISTA_TREINA/TREINA",
			["DS_NOME_TREINA", "TP_TREINA", "DS_TREINA", "LISTA_TREINA_PESSOA"],
		),
		("INFORM_AUDIT/LISTA_TREINA/TREINA/LISTA_TREINA_PESSOA", ["TREINA_PESSOA"]),
		(
			"INFORM_AUDIT/LISTA_TREINA/TREINA/LISTA_TREINA_PESSOA/TREINA_PESSOA",
			["DS_NOME_PESSOA", "TP_CARGO"],
		),
	],
)
def test_full_pj_block_tags_follow_spec_order(path: str, expected: list[str]) -> None:
	"""Every block lists its fields in the page's order."""
	root = _root(_full_pj())
	assert _tags(root if path == "." else _at(root, path)) == expected  # noqa: PLR2004


def test_root_is_namespaced_doc_arq() -> None:
	"""The root is DOC_ARQ in the urn:audtanual namespace."""
	assert _root(_full_pj()).tag == f"{NS}DOC_ARQ"


def test_cod_doc_is_23() -> None:
	"""COD_DOC is 23."""
	assert _at(_root(_full_pj()), "COD_DOC").text == "23"


def test_declares_windows_1252() -> None:
	"""The XML declaration names windows-1252."""
	assert _xml(_full_pj()).startswith('<?xml version="1.0" encoding="windows-1252"?>')


@pytest.mark.parametrize(
	"fragment",
	[
		f"<NR_PF_PJ>{CNPJ_A}</NR_PF_PJ>",
		f"<NR_PF>{CPF}</NR_PF>",
		"<VL_AUDIT>1000,50</VL_AUDIT>",
		"<PR_FATURA>12,34</PR_FATURA>",
		"<DT_CONTR>01/02/2024</DT_CONTR>",
	],
)
def test_values_are_bare_comma_decimal_and_truncated(fragment: str) -> None:
	"""Documents are bare digits, decimals use a comma and are truncated, not rounded."""
	assert fragment in _xml(_full_pj())


def test_minimal_pj_omits_optional_containers() -> None:
	"""Without reps, trainings: LISTA_RESP and LISTA_TREINA are omitted; others stay."""
	inform = _root(_doc())[1]
	assert _tags(inform) == [
		"DS_INFORM", "DS_AUDIT", "LISTA_ENDER", "LISTA_ENTID_AUDITA",
		"QT_OUTRA_ENTID_AUDITA", "FATURA_ANUAL", "DS_CRITER_HONOR", "RH", "LISTA_ENTID_COLIG",
	]  # fmt: skip


def test_pf_document_omits_representatives() -> None:
	"""A PF auditor sends no LISTA_RESP."""
	assert "LISTA_RESP" not in _tags(_root(_doc(pf=True))[1])


def test_pf_document_omits_partner_count() -> None:
	"""A PF auditor's RH carries only QT_FUNC_TECNO."""
	assert _tags(_at(_root(_doc(pf=True)), "INFORM_AUDIT/RH")) == ["QT_FUNC_TECNO"]


def test_pf_accepts_aipf_job() -> None:
	"""A PF auditor may list AIPF (cargo 4) trainings."""
	doc = _doc(pf=True, lista_treina=[_pf_training(4)])
	assert len(doc.lista_treina) == 1


@pytest.mark.parametrize(
	"overrides",
	[
		{"lista_ender": [_address(), _address()]},
		{"lista_ender": [_address(tp_ender=2, nm_filial="F")]},
		{"lista_resp": [AuditorRepresentative(nr_pf=CPF, ds_nome="S", ds_email="s@e.com")]},
		{"rh": AuditorStaff(qt_socios=1, qt_func_tecno=1)},
		{"lista_treina": [_training()]},
	],
)
def test_pf_rejects_pj_only_blocks(overrides: dict[str, Any]) -> None:
	"""Each PJ-only block is refused for a PF auditor."""
	with pytest.raises(ValidationError):
		_doc(pf=True, **overrides)


def test_pj_requires_partner_count() -> None:
	"""A PJ auditor needs QT_SOCIOS."""
	with pytest.raises(ValidationError, match="QT_SOCIOS is required"):
		_doc(rh=AuditorStaff(qt_func_tecno=1))


def test_pj_rejects_aipf_job() -> None:
	"""A PJ auditor cannot list cargo 4."""
	with pytest.raises(ValidationError, match="TP_CARGO"):
		_doc(lista_treina=[_pf_training(4)])


@pytest.mark.parametrize(
	"kw",
	[
		{"tp_pf_pj": "PF"},
		{"nr_pf_pj": CPF},
		{"tp_pf_pj": "PF", "nr_pf_pj": "11144477734"},
		{"nr_pf_pj": "11222333000182"},
		{"tp_pf_pj": "PF", "nr_pf_pj": "111.444.777-35\n"},
		{"nr_pf_pj": " 11222333000181"},
		{"cd_cvm": 0},
		{"ds_email": "a@b.com, c@d.com"},
		{"ds_nome": "x" * 101},
		{"ds_email": "a@" + "b" * 50 + ".c"},
	],
)
def test_identity_rejects(kw: dict[str, Any]) -> None:
	"""CPF/CNPJ must match the type, have valid digits and a sane shape."""
	with pytest.raises(ValidationError):
		_id(**kw)


def test_identity_unmasks_cpf() -> None:
	"""A masked CPF is stored as bare digits."""
	assert _id(tp_pf_pj="PF", nr_pf_pj="111.444.777-35").nr_pf_pj == CPF


@pytest.mark.parametrize(
	"kw",
	[
		{"dt_gerac_arq": "31/02/2025"},
		{"dt_gerac_arq": "1/2/2025"},
		{"motivo_entreg": 4},
		{"ano_base": "2024"},
		{"ano_base": 24},
	],
)
def test_header_rejects(kw: dict[str, Any]) -> None:
	"""Impossible dates, bad motive and malformed years are refused."""
	with pytest.raises(ValidationError):
		_header(**kw)


def test_base_year_after_file_year_refused() -> None:
	"""ANO_BASE cannot be after the year of DT_GERAC_ARQ."""
	with pytest.raises(ValidationError, match="ANO_BASE"):
		_doc(ds_inform=_header(ano_base=2026, motivo_entreg=2))


@pytest.mark.parametrize(
	"kw",
	[
		{"nm_filial": "X"},
		{"tp_ender": 2},
		{"nr_ddd_tel": "11"},
		{"nr_fax": "123"},
		{"nr_cep": "1001000"},
		{"nr_cep": "0100100a"},
		{"nr_tel": "0123"},
		{"nm_lograd": "x" * 31},
		{"ds_compl": "x" * 19},
		{"ds_bairro": "x" * 31},
		{"cd_mun": 0},
	],
)
def test_address_rejects(kw: dict[str, Any]) -> None:
	"""Branch name, phone pairing, CEP shape and field lengths."""
	with pytest.raises(ValidationError):
		_address(**kw)


def test_address_keeps_valid_cep() -> None:
	"""A well-formed CEP is kept."""
	assert _address(nr_cep="01001000").nr_cep == "01001000"


def test_document_requires_an_address() -> None:
	"""LISTA_ENDER needs at least one address."""
	with pytest.raises(ValidationError):
		_doc(lista_ender=[])


@pytest.mark.parametrize(
	"kw",
	[
		{"tp_entid": 2},
		{"tp_entid": True},
		{"pr_fatura": "10"},
		{"pr_fatura": "100.01"},
		{"pr_fatura": 12.5},
		{"dt_contr": "30/02/2024"},
		{"nr_pj": "11.222.333/0001-8"},
		{"nr_pj": "11222333000182"},
		{"ds_nome": ""},
	],
)
def test_entity_rejects(kw: dict[str, Any]) -> None:
	"""Table B codes, 10 percent floor, CNPJ shape and impossible contract date."""
	with pytest.raises(ValidationError):
		_entity(**kw)


def test_table_b_has_48_codes() -> None:
	"""The page lists 48 entity types."""
	assert len(AUDITED_ENTITY_TYPES) == 48  # noqa: PLR2004


def test_entity_accepts_share_just_above_floor() -> None:
	"""10.01 is the smallest reportable share."""
	assert _entity(pr_fatura="10.01").pr_fatura == Decimal("10.01")


@pytest.mark.parametrize(
	"kw",
	[
		{"vl_audit": 1.5},
		{"vl_audit": "-1"},
		{"vl_audit": True},
		{"pr_audit": "100.01"},
		{"hh_audit": -1},
		{"hh_audit": 1.0},
		{"hh_audit": True},
	],
)
def test_billing_rejects(kw: dict[str, Any]) -> None:
	"""No floats, no negatives, no percentage above 100, integer hours."""
	with pytest.raises(ValidationError):
		_billing(**kw)


def test_billing_truncates() -> None:
	"""Excess decimals are truncated, not rounded."""
	assert _billing(vl_audit=Decimal("0.999")).vl_audit == Decimal("0.99")


@pytest.mark.parametrize(
	"overrides",
	[{"qt_outra_entid_audita": -1}, {"ds_criter_honor": "x" * 501}],
)
def test_document_scalar_limits(overrides: dict[str, Any]) -> None:
	"""Negative counts and over-long criteria text are refused."""
	with pytest.raises(ValidationError):
		_doc(**overrides)


@pytest.mark.parametrize(
	"kw",
	[
		{"st_estr": "S", "nr_pj": CNPJ_B},
		{"st_estr": "N"},
		{"st_estr": "s"},
		{"ds_setor_ativd": "x" * 31},
	],
)
def test_affiliated_rejects(kw: dict[str, Any]) -> None:
	"""NR_PJ present exactly when the entity is national; sector length bounded."""
	with pytest.raises(ValidationError):
		_affiliated(**kw)


def test_training_types_are_table_d() -> None:
	"""Table D codes."""
	assert {1, 2, 3, 4, 5, 6, 999} == TRAINING_TYPES


@pytest.mark.parametrize(
	"kw",
	[
		{"tp_treina": 7},
		{"lista_treina_pessoa": []},
		{"ds_treina": "x" * 201},
		{"ds_nome_treina": "x" * 101},
	],
)
def test_training_rejects(kw: dict[str, Any]) -> None:
	"""Table D codes, at least one person, lengths."""
	with pytest.raises(ValidationError):
		_training(**kw)


def test_participant_rejects_unknown_job() -> None:
	"""Cargo 5 does not exist."""
	with pytest.raises(ValidationError):
		TrainingParticipant(ds_nome_pessoa="P", tp_cargo=5)


@pytest.mark.parametrize("cpf", ["11144477734", "1114447773", "111.444.777-35 "])
def test_representative_cpf_checked(cpf: str) -> None:
	"""A CPF with wrong check digits or shape is refused."""
	with pytest.raises(ValidationError):
		AuditorRepresentative(nr_pf=cpf, ds_nome="S", ds_email="s@e.com")


@pytest.mark.parametrize("text", ["a\x00b", "  ", "\u4e2d"])
def test_text_must_be_xml_and_cp1252_safe(text: str) -> None:
	"""Control chars, blank and non-cp1252 text are refused at validation."""
	with pytest.raises(ValidationError):
		_address(nm_lograd=text)


def test_unknown_field_refused() -> None:
	"""Blocks are closed."""
	with pytest.raises(ValidationError):
		AuditorStaff(qt_func_tecno=1, extra=1)  # type: ignore[call-arg]


def test_models_frozen() -> None:
	"""Blocks are immutable."""
	with pytest.raises(ValidationError):
		_doc().__setattr__("qt_outra_entid_audita", 1)


def test_table_limits() -> None:
	"""Upload limits from Table A."""
	with pytest.raises(ValidationError):
		_doc(lista_ender=[_address(tp_ender=2, nm_filial="F")] * 1001)


def test_export_returns_none_when_writing_file(tmp_path: Path) -> None:
	"""Export returns None when it writes a file."""
	doc = _doc(ds_criter_honor="Critério ação")
	assert InformeAnualAuditor().export(doc, output_path=str(tmp_path / "a.xml")) is None


def test_export_writes_cp1252_bytes(tmp_path: Path) -> None:
	"""The file is windows-1252 bytes."""
	out = tmp_path / "a.xml"
	InformeAnualAuditor().export(_doc(ds_criter_honor="Critério ação"), output_path=str(out))
	assert "Critério ação".encode("windows-1252") in out.read_bytes()


def test_failed_export_raises_before_opening_target(tmp_path: Path) -> None:
	"""A non-cp1252 char (validation bypassed) raises."""
	doc = _doc().model_copy(update={"ds_criter_honor": "\u4e2d"})
	with pytest.raises(ValueError, match="cannot be serialised"):
		InformeAnualAuditor().export(doc, output_path=str(tmp_path / "a.xml"))


def test_failed_export_leaves_existing_file_intact(tmp_path: Path) -> None:
	"""The existing file survives a failed export."""
	out = tmp_path / "a.xml"
	out.write_bytes(b"keep")
	doc = _doc().model_copy(update={"ds_criter_honor": "\u4e2d"})
	with contextlib.suppress(ValueError):
		InformeAnualAuditor().export(doc, output_path=str(out))
	assert out.read_bytes() == b"keep"
