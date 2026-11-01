"""Unit tests for the Informe Mensal de Investidor Não Residente submission writer."""

from collections.abc import Callable
import contextlib
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


def test_export_starts_with_windows_1252_declaration() -> None:
	"""Export starts with the windows-1252 declaration."""
	assert InrMensal().export(_doc()).startswith('<?xml version="1.0" encoding="windows-1252"?>')


@pytest.mark.parametrize(
	("pick", "expected"),
	[
		(lambda r: r.tag, f"{NS}DOC_ARQ"),
		(lambda r: r[0].tag, f"{NS}CAB_INFORM"),
		(lambda r: _tags(r[0]), HEADER_TAGS),
		(lambda r: [c.text for c in r[0]], ["477", "1.0", "12345", "01/2025", "15/02/2025"]),
		(lambda r: r[1].tag, f"{NS}LISTA_PARTICIPANTES"),
	],
)
def test_export_header_block_matches_spec_tags(pick: Callable, expected: object) -> None:
	"""Export header block matches spec tags."""
	assert pick(_root(_doc())) == expected


@pytest.mark.parametrize(
	("pick", "expected"),
	[
		(lambda p: p.tag, f"{NS}PARTICIPANTE"),
		(lambda p: _tags(p), ["COD_PARTIC", "ENTRADA_SAIDA", "MOV_RECURSOS", "PATRIM_LIQ"]),
		(lambda p: p[0].text, CODE),
		(
			lambda p: [(c.tag.removeprefix(NS), c.text) for c in p[1]],
			[("VL_ENTR", "10"), ("VL_SAIDA", "20")],
		),
		(lambda p: _tags(p[2]), ["TRANSF_RECURSOS"]),
		(lambda p: _tags(p[2][0]), TRANSF_TAGS),
		(lambda p: p[3].text, "500"),
	],
)
def test_export_minimal_participant_block(pick: Callable, expected: object) -> None:
	"""Export minimal participant block tags and values."""
	assert pick(_root(_doc())[1][0]) == expected


def _same_investor_mov() -> ET.Element:
	"""Export a participant with same-investor blocks and return its MOV_RECURSOS."""
	mesmo = RecursosMesmoInvest(
		recursos_receb_mesmo_invest=[
			RecursosRecebMesmoInvest(cd_partic_origem=CODE2, vl_recebido=7)
		],
		recursos_env_mesmo_invest=[RecursosEnvMesmoInvest(cd_partic_dest=CODE2, vl_enviado=8)],
	)
	mov = MovRecursos(transf_recursos=_transf(), recursos_mesmo_invest=mesmo)
	return _root(_doc(_participant(mov_recursos=mov)))[1][0][2]


@pytest.mark.parametrize(
	("pick", "expected"),
	[
		(lambda e: _tags(e), ["TRANSF_RECURSOS", "RECURSOS_MESMO_INVEST"]),
		(
			lambda e: _tags(e[1]),
			["RECURSOS_RECEB_MESMO_INVEST", "RECURSOS_ENV_MESMO_INVEST"],
		),
		(lambda e: _tags(e[1][0]), ["CD_PARTIC_ORIGEM", "VL_RECEBIDO"]),
		(lambda e: _tags(e[1][1]), ["CD_PARTIC_DEST", "VL_ENVIADO"]),
		(lambda e: e[1][0][0].text, CODE2),
		(lambda e: e[1][1][1].text, "8"),
	],
)
def test_export_same_investor_blocks(pick: Callable, expected: object) -> None:
	"""Export same investor blocks."""
	assert pick(_same_investor_mov()) == expected


def _other_investor_container() -> ET.Element:
	"""Export a participant with other-investor blocks and return RECURSOS_OUTRO_INVEST."""
	outro = RecursosOutroInvest(
		recursos_receb_outro_invest=[
			RecursosRecebOutroInvest(cd_partic_origem=CODE, vl_recebido=1),
			RecursosRecebOutroInvest(cd_partic_origem=CODE2, vl_recebido=2),
		],
		recursos_env_outro_invest=[RecursosEnvOutroInvest(cd_partic_dest=CODE2, vl_enviado=3)],
	)
	mov = MovRecursos(transf_recursos=_transf(), recursos_outro_invest=outro)
	return _root(_doc(_participant(mov_recursos=mov)))[1][0][2][1]


@pytest.mark.parametrize(
	("pick", "expected"),
	[
		(
			lambda c: _tags(c),
			[
				"RECURSOS_RECEB_OUTRO_INVEST",
				"RECURSOS_RECEB_OUTRO_INVEST",
				"RECURSOS_ENV_OUTRO_INVEST",
			],
		),
		(lambda c: _tags(c[2]), ["CD_PARTIC_DEST", "VL_ENVIADO"]),
	],
)
def test_export_other_investor_blocks_repeat(pick: Callable, expected: object) -> None:
	"""Export other investor blocks repeat."""
	assert pick(_other_investor_container()) == expected


def _participant_with_applications() -> ET.Element:
	"""Export a participant holding a plain and a derivative application."""
	apps = [
		Aplicacoes(cd_aplic=1, vl_mercado_aplic=100),
		Aplicacoes(cd_aplic=15, vl_mercado_aplic=-5, vl_nocion_aplic=900),
	]
	return _root(_doc(_participant(aplicacoes=apps)))[1][0]


@pytest.mark.parametrize(
	("pick", "expected"),
	[
		(
			lambda p: _tags(p),
			[
				"COD_PARTIC",
				"ENTRADA_SAIDA",
				"MOV_RECURSOS",
				"APLICACOES",
				"APLICACOES",
				"PATRIM_LIQ",
			],
		),
		(lambda p: _tags(p[3]), ["CD_APLIC", "VL_MERCADO_APLIC"]),
		(lambda p: _tags(p[4]), ["CD_APLIC", "VL_MERCADO_APLIC", "VL_NOCION_APLIC"]),
		(lambda p: p[4][1].text, "-5"),
	],
)
def test_export_applications_before_net_worth_with_notional_only_for_derivatives(
	pick: Callable, expected: object
) -> None:
	"""Export applications before net worth with notional only for derivatives."""
	assert pick(_participant_with_applications()) == expected


def test_export_multiple_participants_in_order() -> None:
	"""Export multiple participants in order."""
	lista = _root(_doc(_participant(CODE), _participant(CODE2)))[1]
	assert [p[0].text for p in lista] == [CODE, CODE2]


def test_export_output_path_returns_none(tmp_path: Path) -> None:
	"""Export to a file returns none."""
	assert InrMensal().export(_doc(), output_path=str(tmp_path / "inr.xml")) is None


def test_export_output_path_writes_cp1252_declaration(tmp_path: Path) -> None:
	"""Export to a file writes the windows-1252 declaration."""
	target = tmp_path / "inr.xml"
	InrMensal().export(_doc(), output_path=str(target))
	assert target.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def _unencodable_doc() -> InrMensalDocument:
	"""Build a document whose header text cannot be encoded as windows-1252."""
	bad = InrMensalHeader.model_construct(
		cod_doc=477, versao="1.0", cd_cvm="12345中", dt_compt="01/2025", dt_gerac_arq="15/02/2025"
	)
	return InrMensalDocument.model_construct(header=bad, participantes=[_participant()])


def test_export_unencodable_text_raises_value_error(tmp_path: Path) -> None:
	"""Export unencodable text raises value error."""
	with pytest.raises(ValueError, match="windows-1252"):
		InrMensal().export(_unencodable_doc(), output_path=str(tmp_path / "inr.xml"))


def test_export_unencodable_text_leaves_existing_file_intact(tmp_path: Path) -> None:
	"""Export unencodable text leaves existing file intact."""
	target = tmp_path / "inr.xml"
	target.write_bytes(b"keep")
	with contextlib.suppress(ValueError):
		InrMensal().export(_unencodable_doc(), output_path=str(target))
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


def test_flows_reject_negative() -> None:
	"""Flows reject negative."""
	with pytest.raises(ValidationError):
		EntradaSaida(vl_entr=-1, vl_saida=0)


def test_market_value_may_be_negative() -> None:
	"""Market value may be negative."""
	assert Aplicacoes(cd_aplic=2, vl_mercado_aplic=-1).vl_mercado_aplic == -1


def test_net_worth_may_be_negative() -> None:
	"""Net worth may be negative."""
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


@pytest.mark.parametrize("container", [RecursosMesmoInvest, RecursosOutroInvest])
def test_empty_optional_containers_are_refused(container: type) -> None:
	"""Empty optional containers are refused."""
	with pytest.raises(ValidationError, match="omit"):
		container()


def _header() -> InrMensalHeader:
	"""Build a valid header."""
	return InrMensalHeader(cd_cvm="1", dt_compt="01/2025", dt_gerac_arq="15/02/2025")


def test_document_requires_a_participant() -> None:
	"""Document requires a participant."""
	with pytest.raises(ValidationError):
		InrMensalDocument(header=_header(), participantes=[])


def test_document_rejects_repeated_participant_code() -> None:
	"""Document rejects repeated participant code."""
	with pytest.raises(ValidationError, match="only once"):
		_doc(_participant(CODE), _participant(CODE))


def _participants(count: int) -> list[Participante]:
	"""Build ``count`` participants with distinct codes."""
	return [_participant(f"1.1.{i}.0-0") for i in range(1, count + 1)]


def test_document_rejects_more_than_1000_participants() -> None:
	"""Document rejects more than 1000 participants."""
	with pytest.raises(ValidationError):
		InrMensalDocument(header=_header(), participantes=_participants(1001))


def test_document_accepts_1000_participants() -> None:
	"""Document accepts 1000 participants."""
	doc = InrMensalDocument(header=_header(), participantes=_participants(1000))
	assert len(doc.participantes) == 1000


def test_unknown_fields_are_rejected() -> None:
	"""Unknown fields are rejected."""
	with pytest.raises(ValidationError):
		EntradaSaida(vl_entr=1, vl_saida=1, extra=1)


def test_export_over_ten_megabytes_raises_value_error() -> None:
	"""The page caps a file at 10 MB; an oversized document must not be emitted."""
	apps = [Aplicacoes(cd_aplic=1, vl_mercado_aplic=1)] * 10_000
	doc = _doc(*[_participant(f"1.1.{i}.0-1", aplicacoes=apps) for i in range(1, 13)])
	with pytest.raises(ValueError, match="at most 10 MB"):
		InrMensal().export(doc)
