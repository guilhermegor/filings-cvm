"""Unit tests for the Informe Anual de Auditor submission writer.

Tag lists are typed from the CVM page (PadraoXMLAuditorAnual.asp), not derived from the schema.
CPFs below are the well-known synthetic test numbers, never real people.
"""

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


def _root(doc: InformeAnualAuditorDocument) -> ET.Element:
	xml = InformeAnualAuditor().export(doc)
	assert xml is not None
	return ET.fromstring(xml.encode("windows-1252"))  # noqa: S314


def test_full_pj_document_emits_every_block_in_spec_order() -> None:
	"""Every block and field appears in the page's order, namespace and COD_DOC 23."""
	root = _root(_full_pj())
	assert root.tag == f"{NS}DOC_ARQ"
	assert _tags(root) == ["COD_DOC", "INFORM_AUDIT"]
	assert root[0].text == "23"
	inform = root[1]
	assert _tags(inform) == [
		"DS_INFORM", "DS_AUDIT", "LISTA_ENDER", "LISTA_RESP", "LISTA_ENTID_AUDITA",
		"QT_OUTRA_ENTID_AUDITA", "FATURA_ANUAL", "DS_CRITER_HONOR", "RH",
		"LISTA_ENTID_COLIG", "LISTA_TREINA",
	]  # fmt: skip
	by = {c.tag.removeprefix(NS): c for c in inform}
	assert _tags(by["DS_INFORM"]) == ["ANO_BASE", "DT_GERAC_ARQ", "MOTIVO_ENTREG"]
	assert _tags(by["DS_AUDIT"]) == ["TP_PF_PJ", "NR_PF_PJ", "CD_CVM", "DS_NOME", "DS_EMAIL"]
	assert _tags(by["LISTA_ENDER"]) == ["ENDER", "ENDER"]
	assert _tags(by["LISTA_ENDER"][0]) == [  # type: ignore[index]
		"TP_ENDER", "NM_LOGRAD", "DS_COMPL", "DS_BAIRRO", "CD_MUN", "NR_CEP",
		"NR_DDD_TEL", "NR_TEL", "NR_DDD_FAX", "NR_FAX",
	]  # fmt: skip
	assert _tags(by["LISTA_ENDER"][1]) == [  # type: ignore[index]
		"TP_ENDER", "NM_FILIAL", "NM_LOGRAD", "DS_BAIRRO", "CD_MUN", "NR_CEP",
	]  # fmt: skip
	assert _tags(by["LISTA_RESP"][0]) == ["NR_PF", "DS_NOME", "DS_EMAIL"]  # type: ignore[index]
	assert _tags(by["LISTA_ENTID_AUDITA"][0]) == [  # type: ignore[index]
		"TP_ENTID", "NR_PJ", "DS_NOME", "DT_CONTR", "PR_FATURA",
	]  # fmt: skip
	assert _tags(by["FATURA_ANUAL"]) == ["VL_AUDIT", "PR_AUDIT", "HH_AUDIT"]
	assert _tags(by["RH"]) == ["QT_SOCIOS", "QT_FUNC_TECNO"]
	assert _tags(by["LISTA_ENTID_COLIG"][0]) == [  # type: ignore[index]
		"ST_ESTR", "NR_PJ", "DS_NOME", "DS_SETOR_ATIVD",
	]  # fmt: skip
	assert _tags(by["LISTA_ENTID_COLIG"][1]) == ["ST_ESTR", "DS_NOME", "DS_SETOR_ATIVD"]  # type: ignore[index]
	treina = by["LISTA_TREINA"][0]  # type: ignore[index]
	assert _tags(treina) == ["DS_NOME_TREINA", "TP_TREINA", "DS_TREINA", "LISTA_TREINA_PESSOA"]
	assert _tags(treina[3]) == ["TREINA_PESSOA"]
	assert _tags(treina[3][0]) == ["DS_NOME_PESSOA", "TP_CARGO"]


def test_values_are_bare_comma_decimal_and_truncated() -> None:
	"""Documents are bare digits, decimals use a comma and are truncated, not rounded."""
	xml = InformeAnualAuditor().export(_full_pj())
	assert xml is not None
	assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>')
	assert f"<NR_PF_PJ>{CNPJ_A}</NR_PF_PJ>" in xml
	assert f"<NR_PF>{CPF}</NR_PF>" in xml
	assert "<VL_AUDIT>1000,50</VL_AUDIT>" in xml
	assert "<PR_FATURA>12,34</PR_FATURA>" in xml
	assert "<DT_CONTR>01/02/2024</DT_CONTR>" in xml


def test_minimal_pj_omits_optional_containers() -> None:
	"""Without reps, trainings: LISTA_RESP and LISTA_TREINA are omitted; others stay."""
	inform = _root(_doc())[1]
	assert _tags(inform) == [
		"DS_INFORM", "DS_AUDIT", "LISTA_ENDER", "LISTA_ENTID_AUDITA",
		"QT_OUTRA_ENTID_AUDITA", "FATURA_ANUAL", "DS_CRITER_HONOR", "RH", "LISTA_ENTID_COLIG",
	]  # fmt: skip


def test_pf_document_rules() -> None:
	"""A PF auditor: one head-office address, no reps, no partners, CPF, AIPF jobs."""
	inform = _root(_doc(pf=True))[1]
	assert "LISTA_RESP" not in _tags(inform)
	assert _tags(inform.find(f"{NS}RH")) == ["QT_FUNC_TECNO"]  # type: ignore[arg-type]
	ok = AuditorTraining(
		ds_nome_treina="C",
		tp_treina=999,
		lista_treina_pessoa=[TrainingParticipant(ds_nome_pessoa="P", tp_cargo=4)],
	)
	_doc(pf=True, lista_treina=[ok])


@pytest.mark.parametrize(
	"overrides",
	[
		{"lista_ender": [_address(), _address()]},
		{"lista_ender": [_address(tp_ender=2, nm_filial="F")]},
		{"lista_resp": [AuditorRepresentative(nr_pf=CPF, ds_nome="S", ds_email="s@e.com")]},
		{"rh": AuditorStaff(qt_socios=1, qt_func_tecno=1)},
		{
			"lista_treina": [
				AuditorTraining(
					ds_nome_treina="C",
					tp_treina=1,
					lista_treina_pessoa=[TrainingParticipant(ds_nome_pessoa="P", tp_cargo=1)],
				)
			]
		},
	],
)
def test_pf_rejects_pj_only_blocks(overrides: dict[str, Any]) -> None:
	"""Each PJ-only block is refused for a PF auditor."""
	with pytest.raises(ValidationError):
		_doc(pf=True, **overrides)


def test_pj_requires_partner_count_and_pj_jobs() -> None:
	"""PJ needs QT_SOCIOS and cargos 1-3 only."""
	with pytest.raises(ValidationError):
		_doc(rh=AuditorStaff(qt_func_tecno=1))
	bad = AuditorTraining(
		ds_nome_treina="C",
		tp_treina=1,
		lista_treina_pessoa=[TrainingParticipant(ds_nome_pessoa="P", tp_cargo=4)],
	)
	with pytest.raises(ValidationError):
		_doc(lista_treina=[bad])


def test_identity_rules() -> None:
	"""CPF/CNPJ must match the type, have valid digits and a sane shape."""
	base: dict[str, Any] = {"cd_cvm": 1, "ds_nome": "N", "ds_email": "a@b.com"}
	for kind, number in [
		("PF", CNPJ_A),
		("PJ", CPF),
		("PF", "11144477734"),
		("PJ", "11222333000182"),
		("PF", "111.444.777-35\n"),
		("PJ", " 11222333000181"),
	]:
		with pytest.raises(ValidationError):
			AuditorIdentity(tp_pf_pj=kind, nr_pf_pj=number, **base)
	assert AuditorIdentity(tp_pf_pj="PF", nr_pf_pj="111.444.777-35", **base).nr_pf_pj == CPF
	with pytest.raises(ValidationError):
		AuditorIdentity(tp_pf_pj="PJ", nr_pf_pj=CNPJ_A, **{**base, "cd_cvm": 0})
	with pytest.raises(ValidationError):
		AuditorIdentity(tp_pf_pj="PJ", nr_pf_pj=CNPJ_A, **{**base, "ds_email": "a@b.com, c@d.com"})
	with pytest.raises(ValidationError):
		AuditorIdentity(tp_pf_pj="PJ", nr_pf_pj=CNPJ_A, **{**base, "ds_nome": "x" * 101})
	with pytest.raises(ValidationError):
		AuditorIdentity(
			tp_pf_pj="PJ", nr_pf_pj=CNPJ_A, **{**base, "ds_email": "a@" + "b" * 50 + ".c"}
		)


def test_header_rules() -> None:
	"""Impossible dates, bad motive and a base year after the file year are refused."""
	for kw in [
		{"dt_gerac_arq": "31/02/2025"},
		{"dt_gerac_arq": "1/2/2025"},
		{"motivo_entreg": 4},
		{"ano_base": "2024"},
		{"ano_base": 24},
	]:
		with pytest.raises(ValidationError):
			AuditorHeader(
				**{"ano_base": 2024, "dt_gerac_arq": "15/04/2025", "motivo_entreg": 1, **kw}
			)
	with pytest.raises(ValidationError):
		_doc(ds_inform=AuditorHeader(ano_base=2026, dt_gerac_arq="15/04/2025", motivo_entreg=2))


def test_address_rules() -> None:
	"""Branch name, phone pairing, CEP shape and field lengths."""
	for kw in [
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
	]:
		with pytest.raises(ValidationError):
			_address(**kw)
	assert _address(nr_cep="01001000").nr_cep == "01001000"
	with pytest.raises(ValidationError):
		_doc(lista_ender=[])


def test_entity_rules() -> None:
	"""Table B codes, 10 percent floor, CNPJ shape and impossible contract date."""
	base: dict[str, Any] = {"tp_entid": 1, "nr_pj": CNPJ_B, "ds_nome": "N"}
	for kw in [
		{"tp_entid": 2},
		{"tp_entid": True},
		{"pr_fatura": "10"},
		{"pr_fatura": "100.01"},
		{"pr_fatura": 12.5},
		{"dt_contr": "30/02/2024"},
		{"nr_pj": "11.222.333/0001-8"},
		{"nr_pj": "11222333000182"},
		{"ds_nome": ""},
	]:
		with pytest.raises(ValidationError):
			AuditedEntity(**{**base, **kw})
	assert len(AUDITED_ENTITY_TYPES) == 48
	assert AuditedEntity(**{**base, "pr_fatura": "10.01"}).pr_fatura == Decimal("10.01")


def test_billing_rules() -> None:
	"""No floats, no negatives, no percentage above 100, integer hours."""
	for kw in [
		{"vl_audit": 1.5},
		{"vl_audit": "-1"},
		{"vl_audit": True},
		{"pr_audit": "100.01"},
		{"hh_audit": -1},
		{"hh_audit": 1.0},
		{"hh_audit": True},
	]:
		with pytest.raises(ValidationError):
			AuditorAnnualBilling(**{"vl_audit": "1", "pr_audit": "1", "hh_audit": 1, **kw})
	assert AuditorAnnualBilling(vl_audit=Decimal("0.999"), pr_audit=1, hh_audit=0).vl_audit == (
		Decimal("0.99")
	)
	with pytest.raises(ValidationError):
		_doc(qt_outra_entid_audita=-1)
	with pytest.raises(ValidationError):
		_doc(ds_criter_honor="x" * 501)


def test_affiliated_rules() -> None:
	"""NR_PJ present exactly when the entity is national; sector length bounded."""
	with pytest.raises(ValidationError):
		AffiliatedEntity(st_estr="S", nr_pj=CNPJ_B, ds_nome="N", ds_setor_ativd="S")
	with pytest.raises(ValidationError):
		AffiliatedEntity(st_estr="N", ds_nome="N", ds_setor_ativd="S")
	with pytest.raises(ValidationError):
		AffiliatedEntity(st_estr="s", ds_nome="N", ds_setor_ativd="S")
	with pytest.raises(ValidationError):
		AffiliatedEntity(st_estr="S", ds_nome="N", ds_setor_ativd="x" * 31)


def test_training_rules() -> None:
	"""Table D codes, at least one person, lengths."""
	person = TrainingParticipant(ds_nome_pessoa="P", tp_cargo=1)
	assert {1, 2, 3, 4, 5, 6, 999} == TRAINING_TYPES
	for kw in [
		{"tp_treina": 7},
		{"lista_treina_pessoa": []},
		{"ds_treina": "x" * 201},
		{"ds_nome_treina": "x" * 101},
	]:
		with pytest.raises(ValidationError):
			AuditorTraining(
				**{"ds_nome_treina": "C", "tp_treina": 1, "lista_treina_pessoa": [person], **kw}
			)
	with pytest.raises(ValidationError):
		TrainingParticipant(ds_nome_pessoa="P", tp_cargo=5)


def test_representative_cpf_checked() -> None:
	"""A CPF with wrong check digits or shape is refused."""
	for cpf in ["11144477734", "1114447773", "111.444.777-35 "]:
		with pytest.raises(ValidationError):
			AuditorRepresentative(nr_pf=cpf, ds_nome="S", ds_email="s@e.com")


def test_text_must_be_xml_and_cp1252_safe() -> None:
	"""Control chars, blank and non-cp1252 text are refused at validation."""
	for text in ["a\x00b", "  ", "中"]:
		with pytest.raises(ValidationError):
			_address(nm_lograd=text)


def test_unknown_field_refused_and_models_frozen() -> None:
	"""Closed, immutable blocks."""
	with pytest.raises(ValidationError):
		AuditorStaff(qt_func_tecno=1, extra=1)  # type: ignore[call-arg]
	with pytest.raises(ValidationError):
		_doc().__setattr__("qt_outra_entid_audita", 1)


def test_table_limits() -> None:
	"""Upload limits from Table A."""
	with pytest.raises(ValidationError):
		_doc(lista_ender=[_address(tp_ender=2, nm_filial="F")] * 1001)


def test_export_writes_cp1252_file(tmp_path: Path) -> None:
	"""The file is windows-1252 bytes and export returns None."""
	out = tmp_path / "a.xml"
	doc = _doc(ds_criter_honor="Critério ação")
	assert InformeAnualAuditor().export(doc, output_path=str(out)) is None
	assert "Critério ação".encode("windows-1252") in out.read_bytes()


def test_failed_export_leaves_existing_file_intact(tmp_path: Path) -> None:
	"""A non-cp1252 char (validation bypassed) raises before the target is opened."""
	out = tmp_path / "a.xml"
	out.write_bytes(b"keep")
	doc = _doc().model_copy(update={"ds_criter_honor": "中"})
	with pytest.raises(ValueError, match="cannot be serialised"):
		InformeAnualAuditor().export(doc, output_path=str(out))
	assert out.read_bytes() == b"keep"
