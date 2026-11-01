"""Unit tests for the Extrato V2 submission writer (PadraoXMLInfExtratoV2.asp)."""

from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405  # parses our own output in tests

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	Extrato,
	ExtratoDocument,
	ExtratoHeader,
	ExtratoRow,
	ExtratoV2,
	ExtratoV2Document,
	ExtratoV2Header,
)


_NS = "{urn:extr}"
_CNPJ = "11222333000181"
_V2_HEADER_TAGS = ["COD_DOC", "VERSAO", "DT_GERAC_ARQ"]


def _pairs(names: list[str]) -> dict[str, str]:
	return {f"{n}_{s}": v for n in names for s, v in (("min", "1.00"), ("max", "50.00"))}


def _row() -> ExtratoRow:
	tipo = ["instituicoes_financeiras", "companhias_abertas", "fundos_investimento"]
	tipo += ["uniao_federal", "administrador_gestor_pessoas_ligadas", "outros"]
	modalidade = [
		"cotas_fi_555",
		"cotas_fic_555",
		"cotas_fi_555_invest_qualificados",
		"cotas_fic_555_invest_qualificados",
		"cotas_fi_555_invest_profissionais",
		"cotas_fic_555_invest_profissionais",
		"cotas_fii",
		"cotas_fidc",
		"cotas_ficfidc",
		"cotas_fidc_np",
		"cotas_ficfidc_np",
		"cotas_fundos_indice_mercado_etf",
		"cri",
		"titulos_publicos_operacoes",
		"ouro",
		"titulos_emissao_coobrigacao",
		"valores_mobiliarios_alinea",
		"deposito_acoes",
		"debentures",
		"notas_promissorias",
		"operacoes_compromissadas",
		"derivativos",
		"outros",
		"cotas_fmiee",
		"cotas_fip",
		"cotas_ficfip",
	]
	return ExtratoRow(
		cnpj_fdo=_CNPJ,
		forma_condominio={"tipo_condominio": "ABERTO"},
		prazo={"tipo_prazo": "INDETERMINADO"},
		fundo_anbima={"anbima": "N"},
		cod_polit_invest=1,
		max_app_cotas_fundo="10.5",
		resultado_atr_carteira="S",
		fundo_invert_cotas={"tipo_fundo_invert": "N"},
		valor_cota={"atualizado_diariamente": "S"},
		resg_cotas={"carencia_resg_cotas": "N"},
		tx_perfm={"cobra_tx_perfm": "N"},
		tx_ingresso={"cobra_tx_ingresso": "N"},
		tx_saida={"cobra_tx_saida": "N"},
		oper_deriv={"realiz_oper_deriv": "N"},
		oper_patrim_liq={"realiza_oper_patrim_liq": "N"},
		mercado_sem_contraparte_central="N",
		ativ_exter={"invest_exterior": "N"},
		fundo_ativos={"adquira_credito_privado": "N"},
		regulamento_tipo_emissor=_pairs(tipo),
		regulamento_modalidade_ativo=_pairs(modalidade),
	)


def _v2_xml() -> ET.Element:
	doc = ExtratoV2Document(header=ExtratoV2Header(dt_gerac_arq="31/10/2026"), rows=[_row()])
	xml = ExtratoV2().export(doc)
	assert xml is not None
	return ET.fromstring(xml.encode("windows-1252"))  # noqa: S314


def test_v2_header_tags_follow_the_sample_order() -> None:
	"""CAB_INFORM carries COD_DOC, VERSAO, DT_GERAC_ARQ in the page's order."""
	header = _v2_xml()[0]
	assert [c.tag.removeprefix(_NS) for c in header] == _V2_HEADER_TAGS


def test_v2_header_pins_cod_doc_41_and_versao_2() -> None:
	"""The V2 header texts are 41 / 2.0 / the date."""
	assert [c.text for c in _v2_xml()[0]] == ["41", "2.0", "31/10/2026"]


def test_v2_row_tags_equal_the_v3_row_tags() -> None:
	"""The page's V2 and V3 samples list the same row tags in the same order."""
	doc = ExtratoDocument(header=ExtratoHeader(dt_gerac_arq="31/10/2026"), rows=[_row()])
	v3 = ET.fromstring(Extrato().export(doc).encode("windows-1252"))  # noqa: S314
	assert [c.tag for c in _v2_xml()[1][0]] == [c.tag for c in v3[1][0]]


def test_v2_root_is_doc_arq_in_the_extr_namespace() -> None:
	"""The root element is DOC_ARQ in urn:extr."""
	assert _v2_xml().tag == f"{_NS}DOC_ARQ"


@pytest.mark.parametrize("versao", ["3.0", "1.0", "2"])
def test_v2_header_rejects_other_versions(versao: str) -> None:
	"""Only VERSAO 2.0 is accepted."""
	with pytest.raises(ValidationError):
		ExtratoV2Header(dt_gerac_arq="31/10/2026", versao=versao)


def test_v2_header_rejects_an_impossible_date() -> None:
	"""Dates are checked for real."""
	with pytest.raises(ValidationError):
		ExtratoV2Header(dt_gerac_arq="31/02/2026")


def test_v2_document_requires_a_row() -> None:
	"""A file carries at least one fund."""
	with pytest.raises(ValidationError):
		ExtratoV2Document(header=ExtratoV2Header(dt_gerac_arq="31/10/2026"), rows=[])


def _export_to(tmp_path: Path) -> tuple[Path, str | None]:
	out = tmp_path / "extrato.xml"
	doc = ExtratoV2Document(header=ExtratoV2Header(dt_gerac_arq="31/10/2026"), rows=[_row()])
	return out, ExtratoV2().export(doc, output_path=str(out))


def test_v2_export_with_output_path_returns_none(tmp_path: Path) -> None:
	"""With output_path nothing is returned."""
	assert _export_to(tmp_path)[1] is None


def test_v2_export_writes_a_windows_1252_declaration(tmp_path: Path) -> None:
	"""The written file declares windows-1252."""
	assert b"windows-1252" in _export_to(tmp_path)[0].read_bytes()[:60]


def test_v2_export_leaves_no_temp_file_behind(tmp_path: Path) -> None:
	"""The atomic write leaves only the destination in the directory."""
	out = _export_to(tmp_path)[0]
	assert list(tmp_path.iterdir()) == [out]
