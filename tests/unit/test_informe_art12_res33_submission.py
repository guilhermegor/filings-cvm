"""Unit tests for the Informe Art. 12 Res. CVM 33 (escriturador) submission writer.

Tag lists are typed from PadraoXMLPrest.asp, not derived from the writer.
"""

from pathlib import Path
import xml.etree.ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InformeArt12Res33,
	PrestAtivo,
	PrestDados,
	PrestDocument,
	PrestEmissor,
	PrestHeader,
	PrestInform,
)


NS = "{urn:prestserv}"
CNPJ_A = "11222333000181"
CNPJ_B = "11444777000161"


def _ativo(**kw: object) -> PrestAtivo:
	"""Build an ATIVO block."""
	fields: dict[str, object] = {"ativo_escriturado": "A1", "dt_inicio_contrato": "01/02/2020"}
	fields.update(kw)
	return PrestAtivo(**fields)


def _inform(cnpj: str = CNPJ_A, code: int = 41, emissores: tuple | None = None) -> PrestInform:
	"""Build a provider block."""
	if emissores is None:
		emissores = (PrestEmissor(cnpj_emissor=CNPJ_B, ativos=(_ativo(),)),)
	return PrestInform(
		ds_prest=PrestDados(cnpj_escriturador=cnpj, cd_tp_prest=code), emissores=emissores
	)


def _doc(
	compt: str = "09/2025", gerac: str = "03/10/2025", prest: tuple | None = None
) -> PrestDocument:
	"""Build a document."""
	return PrestDocument(
		ds_inform=PrestHeader(dt_compt=compt, dt_gerac_arq=gerac),
		prestadores=prest if prest is not None else (_inform(),),
	)


def _tags(el: ET.Element) -> list[str]:
	"""Child tags without namespace."""
	return [c.tag.removeprefix(NS) for c in el]


def test_xml_full_structure_matches_spec_tag_order() -> None:
	"""Every block appears in the order the page's sample shows."""
	ativo = _ativo(dt_fim_contrato="30/06/2025")
	doc = _doc(
		prest=(
			_inform(
				emissores=(
					PrestEmissor(
						cnpj_emissor=CNPJ_B, ativos=(ativo, _ativo(ativo_escriturado="A4"))
					),
				)
			),
		)
	)
	xml = InformeArt12Res33().export(doc)
	assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>\n')
	root = ET.fromstring(xml.encode("windows-1252"))  # noqa: S314
	assert root.tag == f"{NS}DOC_ARQ"
	assert _tags(root) == ["COD_ARQ", "DS_INFORM", "LISTA_PREST"]
	assert root.find(f"{NS}COD_ARQ").text == "29"
	assert _tags(root.find(f"{NS}DS_INFORM")) == ["DT_COMPT", "DT_GERAC_ARQ"]
	inform = root.find(f"{NS}LISTA_PREST/{NS}INFORM_PREST")
	assert _tags(inform) == ["DS_PREST", "LISTA_EMISSORES"]
	assert _tags(inform.find(f"{NS}DS_PREST")) == ["CNPJ_ESCRITURADOR", "CD_TP_PREST"]
	emissor = inform.find(f"{NS}LISTA_EMISSORES/{NS}EMISSOR")
	assert _tags(emissor) == ["CNPJ_EMISSOR", "ATIVO", "ATIVO"]
	first, second = emissor.findall(f"{NS}ATIVO")
	assert _tags(first) == ["ATIVO_ESCRITURADO", "DT_INICIO_CONTRATO", "DT_FIM_CONTRATO"]
	assert _tags(second) == ["ATIVO_ESCRITURADO", "DT_INICIO_CONTRATO"]
	assert first.find(f"{NS}DT_FIM_CONTRATO").text == "30/06/2025"
	assert root.find(f"{NS}DS_INFORM/{NS}DT_COMPT").text == "09/2025"


def test_cnpj_masked_is_written_bare() -> None:
	"""Points, dashes and slashes are omitted from CNPJ."""
	doc = _doc(prest=(_inform(cnpj="11.222.333/0001-81"),))
	assert f"<CNPJ_ESCRITURADOR>{CNPJ_A}<" in InformeArt12Res33().export(doc)


def test_repeats_providers_and_issuers() -> None:
	"""Provider and issuer blocks repeat."""
	two = (
		PrestEmissor(cnpj_emissor=CNPJ_B, ativos=(_ativo(),)),
		PrestEmissor(cnpj_emissor=CNPJ_A, ativos=(_ativo(),)),
	)
	doc = _doc(prest=(_inform(emissores=two), _inform(cnpj=CNPJ_B)))
	xml = InformeArt12Res33().export(doc)
	assert xml.count("<INFORM_PREST>") == 2
	assert xml.count("<EMISSOR>") == 3


@pytest.mark.parametrize("cnpj", ["11222333000180", " 11222333000181", "11222333000181\n", "1122"])
def test_bad_cnpj_rejected(cnpj: str) -> None:
	"""Wrong digit, stray whitespace/newline and wrong length fail."""
	with pytest.raises(ValidationError):
		PrestEmissor(cnpj_emissor=cnpj, ativos=(_ativo(),))


@pytest.mark.parametrize(
	"value", ["31/02/2025", "1/1/2025", "01/01/0001", "01/01/2025\n", "٠١/01/2025"]
)
def test_bad_dates_rejected(value: str) -> None:
	"""Impossible, unpadded, ancient, newline-trailed and non-ASCII-digit dates fail."""
	with pytest.raises(ValidationError):
		_ativo(dt_inicio_contrato=value)


@pytest.mark.parametrize("value", ["13/2025", "9/2025", "09/1800", "09/2025\n"])
def test_bad_competence_rejected(value: str) -> None:
	"""Competence must be a real MM/AAAA."""
	with pytest.raises(ValidationError):
		PrestHeader(dt_compt=value, dt_gerac_arq="10/10/2025")


def test_generation_before_competence_rejected() -> None:
	"""A file cannot be generated before its competence month."""
	with pytest.raises(ValidationError):
		PrestHeader(dt_compt="09/2025", dt_gerac_arq="31/08/2025")


def test_contract_end_before_start_rejected() -> None:
	"""DT_FIM_CONTRATO must not precede the start."""
	with pytest.raises(ValidationError):
		_ativo(dt_fim_contrato="31/01/2020")


@pytest.mark.parametrize("code", ["A0", "A5", "a1", ""])
def test_bad_ativo_code_rejected(code: str) -> None:
	"""Only Tabela B codes are accepted."""
	with pytest.raises(ValidationError):
		_ativo(ativo_escriturado=code)


def test_provider_type_code_table_a() -> None:
	"""41 always; 42/52/65 only for a competence before 07/2014."""
	assert _doc(prest=(_inform(code=41),))
	for code in (42, 52, 65):
		assert _doc(compt="06/2014", gerac="10/07/2014", prest=(_inform(code=code),))
		with pytest.raises(ValidationError):
			_doc(compt="07/2014", gerac="10/08/2014", prest=(_inform(code=code),))
	with pytest.raises(ValidationError):
		PrestDados(cnpj_escriturador=CNPJ_A, cd_tp_prest=43)
	with pytest.raises(ValidationError):
		PrestDados(cnpj_escriturador=CNPJ_A, cd_tp_prest="41")


def test_cardinality_rules() -> None:
	"""Lists need an entry; no repeated issuer or provider."""
	with pytest.raises(ValidationError):
		PrestEmissor(cnpj_emissor=CNPJ_B, ativos=())
	with pytest.raises(ValidationError):
		_inform(emissores=())
	with pytest.raises(ValidationError):
		_doc(prest=())
	dup = PrestEmissor(cnpj_emissor=CNPJ_B, ativos=(_ativo(),))
	with pytest.raises(ValidationError):
		_inform(emissores=(dup, dup))
	with pytest.raises(ValidationError):
		_doc(prest=(_inform(), _inform()))


def test_unknown_field_rejected() -> None:
	"""Blocks are closed."""
	with pytest.raises(ValidationError):
		PrestHeader(dt_compt="09/2025", dt_gerac_arq="10/10/2025", extra=1)


def test_export_writes_windows_1252_file(tmp_path: Path) -> None:
	"""A file export returns None and holds the declaration."""
	out = tmp_path / "a.xml"
	assert InformeArt12Res33().export(_doc(), output_path=str(out)) is None
	assert out.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def test_failed_export_keeps_existing_file(tmp_path: Path) -> None:
	"""Unencodable text raises before the target is opened."""
	out = tmp_path / "a.xml"
	out.write_bytes(b"keep")
	bad = PrestHeader.model_construct(dt_compt="09/2025", dt_gerac_arq="10/10/2025€中")
	doc = PrestDocument.model_construct(ds_inform=bad, prestadores=(_inform(),))
	with pytest.raises(ValueError, match="windows-1252"):
		InformeArt12Res33().export(doc, output_path=str(out))
	assert out.read_bytes() == b"keep"
