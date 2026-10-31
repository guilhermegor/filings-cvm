"""Unit tests for the Informe Mensal de Investidor Não Residente submission writer."""

from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	Aplicacoes,
	EntradaSaida,
	InrMensal,
	InrMensalDocument,
	InrMensalHeader,
	MovRecursos,
	Participante,
	RecursosEnvMesmoInvest,
	RecursosEnvOutroInvest,
	RecursosMesmoInvest,
	RecursosOutroInvest,
	RecursosRecebMesmoInvest,
	RecursosRecebOutroInvest,
	TransfRecursos,
)


NS = "{urn:infmensal}"
CODE = "12345.123456.654321.1-9"
CODE2 = "12345.123456.654322.0-0"

# Tag lists typed from the page's sample file.
HEADER_TAGS = ["COD_DOC", "VERSAO", "CD_CVM", "DT_COMPT", "DT_GERAC_ARQ"]
TRANSF_TAGS = [
	"VL_INVEST_CARTEIRA_HAVER_NRES",
	"VL_HAVER_NRES_INVEST_CARTEIRA",
	"VL_INVEST_CARTEIRA_ADR",
	"VL_ADR_INVEST_CARTEIRA",
	"VL_INVEST_CARTEIRA_ESTRANG_DIRETA",
	"VL_ESTRANG_DIRETA_INVEST_CARTEIRA",
]


def _transf() -> TransfRecursos:
	"""Build the six transfer amounts."""
	return TransfRecursos(**{t.lower(): i for i, t in enumerate(TRANSF_TAGS)})


def _participant(code: str = CODE, **extra: object) -> Participante:
	"""Build one participant."""
	kwargs: dict[str, object] = {
		"cod_partic": code,
		"entrada_saida": EntradaSaida(vl_entr=10, vl_saida="20"),
		"mov_recursos": MovRecursos(transf_recursos=_transf()),
		"patrim_liq": 500,
	}
	kwargs.update(extra)
	return Participante(**kwargs)


def _doc(*participants: Participante) -> InrMensalDocument:
	"""Build a document."""
	return InrMensalDocument(
		header=InrMensalHeader(cd_cvm="12345", dt_compt="01/2025", dt_gerac_arq="15/02/2025"),
		participantes=list(participants or [_participant()]),
	)


def _root(doc: InrMensalDocument) -> ET.Element:
	"""Export and parse the XML root."""
	return ET.fromstring(InrMensal().export(doc).split("\n", 1)[1])  # noqa: S314


def _tags(element: ET.Element) -> list[str]:
	"""List child tags of an element."""
	return [c.tag.removeprefix(NS) for c in element]


def test_export_header_block_matches_spec_tags() -> None:
	"""Export header block matches spec tags."""
	xml = InrMensal().export(_doc())
	assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>')
	root = ET.fromstring(xml.split("\n", 1)[1])  # noqa: S314
	assert root.tag == f"{NS}DOC_ARQ"
	header = root[0]
	assert header.tag == f"{NS}CAB_INFORM"
	assert _tags(header) == HEADER_TAGS
	assert [c.text for c in header] == ["477", "1.0", "12345", "01/2025", "15/02/2025"]
	assert root[1].tag == f"{NS}LISTA_PARTICIPANTES"


def test_export_minimal_participant_block_tags_and_values() -> None:
	"""Export minimal participant block tags and values."""
	part = _root(_doc())[1][0]
	assert part.tag == f"{NS}PARTICIPANTE"
	assert _tags(part) == ["COD_PARTIC", "ENTRADA_SAIDA", "MOV_RECURSOS", "PATRIM_LIQ"]
	assert part[0].text == CODE
	assert [(c.tag.removeprefix(NS), c.text) for c in part[1]] == [
		("VL_ENTR", "10"),
		("VL_SAIDA", "20"),
	]
	mov = part[2]
	assert _tags(mov) == ["TRANSF_RECURSOS"]
	assert _tags(mov[0]) == TRANSF_TAGS
	assert part[3].text == "500"


def test_export_same_investor_blocks() -> None:
	"""Export same investor blocks."""
	mesmo = RecursosMesmoInvest(
		recursos_receb_mesmo_invest=[
			RecursosRecebMesmoInvest(cd_partic_origem=CODE2, vl_recebido=7)
		],
		recursos_env_mesmo_invest=[RecursosEnvMesmoInvest(cd_partic_dest=CODE2, vl_enviado=8)],
	)
	mov = MovRecursos(transf_recursos=_transf(), recursos_mesmo_invest=mesmo)
	elem = _root(_doc(_participant(mov_recursos=mov)))[1][0][2]
	assert _tags(elem) == ["TRANSF_RECURSOS", "RECURSOS_MESMO_INVEST"]
	container = elem[1]
	assert _tags(container) == ["RECURSOS_RECEB_MESMO_INVEST", "RECURSOS_ENV_MESMO_INVEST"]
	assert _tags(container[0]) == ["CD_PARTIC_ORIGEM", "VL_RECEBIDO"]
	assert _tags(container[1]) == ["CD_PARTIC_DEST", "VL_ENVIADO"]
	assert container[0][0].text == CODE2
	assert container[1][1].text == "8"


def test_export_other_investor_blocks_repeat() -> None:
	"""Export other investor blocks repeat."""
	outro = RecursosOutroInvest(
		recursos_receb_outro_invest=[
			RecursosRecebOutroInvest(cd_partic_origem=CODE, vl_recebido=1),
			RecursosRecebOutroInvest(cd_partic_origem=CODE2, vl_recebido=2),
		],
		recursos_env_outro_invest=[RecursosEnvOutroInvest(cd_partic_dest=CODE2, vl_enviado=3)],
	)
	mov = MovRecursos(transf_recursos=_transf(), recursos_outro_invest=outro)
	container = _root(_doc(_participant(mov_recursos=mov)))[1][0][2][1]
	assert _tags(container) == [
		"RECURSOS_RECEB_OUTRO_INVEST",
		"RECURSOS_RECEB_OUTRO_INVEST",
		"RECURSOS_ENV_OUTRO_INVEST",
	]
	assert _tags(container[2]) == ["CD_PARTIC_DEST", "VL_ENVIADO"]


def test_export_applications_before_net_worth_with_notional_only_for_derivatives() -> None:
	"""Export applications before net worth with notional only for derivatives."""
	apps = [
		Aplicacoes(cd_aplic=1, vl_mercado_aplic=100),
		Aplicacoes(cd_aplic=15, vl_mercado_aplic=-5, vl_nocion_aplic=900),
	]
	part = _root(_doc(_participant(aplicacoes=apps)))[1][0]
	assert _tags(part) == [
		"COD_PARTIC",
		"ENTRADA_SAIDA",
		"MOV_RECURSOS",
		"APLICACOES",
		"APLICACOES",
		"PATRIM_LIQ",
	]
	assert _tags(part[3]) == ["CD_APLIC", "VL_MERCADO_APLIC"]
	assert _tags(part[4]) == ["CD_APLIC", "VL_MERCADO_APLIC", "VL_NOCION_APLIC"]
	assert part[4][1].text == "-5"


def test_export_multiple_participants_in_order() -> None:
	"""Export multiple participants in order."""
	lista = _root(_doc(_participant(CODE), _participant(CODE2)))[1]
	assert [p[0].text for p in lista] == [CODE, CODE2]


def test_export_output_path_writes_cp1252_and_returns_none(tmp_path: Path) -> None:
	"""Export output path writes cp1252 and returns none."""
	target = tmp_path / "inr.xml"
	assert InrMensal().export(_doc(), output_path=str(target)) is None
	assert target.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def test_export_unencodable_text_leaves_existing_file_intact(tmp_path: Path) -> None:
	"""Export unencodable text leaves existing file intact."""
	target = tmp_path / "inr.xml"
	target.write_bytes(b"keep")
	bad = InrMensalHeader.model_construct(
		cod_doc=477, versao="1.0", cd_cvm="12345中", dt_compt="01/2025", dt_gerac_arq="15/02/2025"
	)
	doc = InrMensalDocument.model_construct(header=bad, participantes=[_participant()])
	with pytest.raises(ValueError, match="windows-1252"):
		InrMensal().export(doc, output_path=str(target))
	assert target.read_bytes() == b"keep"


@pytest.mark.parametrize(
	"value", [1.5, 1.0, True, "1.5", "", "1e3", Decimal("1.5"), Decimal("NaN")]
)
def test_amount_rejects_float_bool_and_fractions(value: object) -> None:
	"""Amount rejects float bool and fractions."""
	with pytest.raises(ValidationError):
		EntradaSaida(vl_entr=value, vl_saida=0)


def test_amount_accepts_whole_decimal_and_str() -> None:
	"""Amount accepts whole decimal and str."""
	block = EntradaSaida(vl_entr=Decimal("12"), vl_saida="0007")
	assert (block.vl_entr, block.vl_saida) == (12, 7)


def test_flows_reject_negative_but_market_value_and_net_worth_may_be_negative() -> None:
	"""Flows reject negative but market value and net worth may be negative."""
	with pytest.raises(ValidationError):
		EntradaSaida(vl_entr=-1, vl_saida=0)
	assert Aplicacoes(cd_aplic=2, vl_mercado_aplic=-1).vl_mercado_aplic == -1
	assert _participant(patrim_liq=-9).patrim_liq == -9


@pytest.mark.parametrize("code", [0, 31, True, 1.0])
def test_application_code_must_be_in_table_a(code: object) -> None:
	"""Application code must be in table a."""
	with pytest.raises(ValidationError):
		Aplicacoes(cd_aplic=code, vl_mercado_aplic=1)


@pytest.mark.parametrize("code", [1, 14, 25, 30])
def test_notional_forbidden_outside_derivatives(code: int) -> None:
	"""Notional forbidden outside derivatives."""
	with pytest.raises(ValidationError, match="must be omitted"):
		Aplicacoes(cd_aplic=code, vl_mercado_aplic=1, vl_nocion_aplic=1)


@pytest.mark.parametrize("code", [15, 20, 24])
def test_notional_required_for_derivatives(code: int) -> None:
	"""Notional required for derivatives."""
	with pytest.raises(ValidationError, match="required"):
		Aplicacoes(cd_aplic=code, vl_mercado_aplic=1)


@pytest.mark.parametrize(
	"code",
	[
		"12345.123456.654321.2-9",
		"012345.123456.654321.1-9",
		"12345.123456.654321.1-99",
		"12345.123456.654321.1-9\n",
		"12345.0123456.654321.1-9",
		"12345123456654321 1-9",
		"١٢٣٤٥.123456.654321.1-9",
		"",
	],
)
def test_participant_code_layout_is_strict(code: str) -> None:
	"""Participant code layout is strict."""
	with pytest.raises(ValidationError):
		_participant(code)


@pytest.mark.parametrize("cvm", ["", "012345", "123456", "1234a", "12345\n", "٣"])
def test_cd_cvm_rejects_bad_codes(cvm: str) -> None:
	"""Cd cvm rejects bad codes."""
	with pytest.raises(ValidationError):
		InrMensalHeader(cd_cvm=cvm, dt_compt="01/2025", dt_gerac_arq="15/02/2025")


@pytest.mark.parametrize(
	"value", ["13/2025", "00/2025", "1/2025", "01/1800", "2025/01", "01/2025\n"]
)
def test_competence_must_be_real_month_year(value: str) -> None:
	"""Competence must be real month year."""
	with pytest.raises(ValidationError):
		InrMensalHeader(cd_cvm="1", dt_compt=value, dt_gerac_arq="15/02/2025")


@pytest.mark.parametrize(
	"value", ["31/02/2025", "29/02/2025", "15/02/1800", "2025-02-15", "15/02/2025\n"]
)
def test_generation_date_must_be_real_date(value: str) -> None:
	"""Generation date must be real date."""
	with pytest.raises(ValidationError):
		InrMensalHeader(cd_cvm="1", dt_compt="01/2025", dt_gerac_arq=value)


def test_header_fixed_fields_cannot_change() -> None:
	"""Header fixed fields cannot change."""
	with pytest.raises(ValidationError):
		InrMensalHeader(cod_doc=1, cd_cvm="1", dt_compt="01/2025", dt_gerac_arq="15/02/2025")


def test_empty_optional_containers_are_refused() -> None:
	"""Empty optional containers are refused."""
	with pytest.raises(ValidationError, match="omit"):
		RecursosMesmoInvest()
	with pytest.raises(ValidationError, match="omit"):
		RecursosOutroInvest()


def test_participant_count_and_uniqueness() -> None:
	"""Participant count and uniqueness."""
	header = InrMensalHeader(cd_cvm="1", dt_compt="01/2025", dt_gerac_arq="15/02/2025")
	with pytest.raises(ValidationError):
		InrMensalDocument(header=header, participantes=[])
	with pytest.raises(ValidationError, match="only once"):
		_doc(_participant(CODE), _participant(CODE))
	many = [_participant(f"1.1.{i}.0-0") for i in range(1, 1002)]
	with pytest.raises(ValidationError):
		InrMensalDocument(header=header, participantes=many)
	assert len(InrMensalDocument(header=header, participantes=many[:1000]).participantes) == 1000


def test_unknown_fields_are_rejected() -> None:
	"""Unknown fields are rejected."""
	with pytest.raises(ValidationError):
		EntradaSaida(vl_entr=1, vl_saida=1, extra=1)
