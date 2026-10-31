"""Unit tests for the Cadastro de Ativos submission writer.

Expectations come from the CVM page PadraoXMLAtivos.asp (tag names and order, Tables 1/2,
I/A/R rules, 1000-row cap), not from the writer.
"""
# ruff: noqa: S314  (parses the writer's own output, not untrusted input)

from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	CadastroAtivos,
	CadastroAtivosDocument,
	CadastroAtivosHeader,
	CadastroAtivosRow,
)


CNPJ = "11.222.333/0001-81"
ROW_ORDER = [
	"ACAO",
	"CD_ATIV",
	"DS_ATIV",
	"TP_ATIV",
	"CNPJ_EMP_EMISSORA",
	"TP_EMP_EMISSORA",
	"NM_EMP_EMISSORA",
	"DS_ISIN",
	"DT_INICIO_VIGEN",
	"DT_FIM_VIGEN",
	"DT_INICIO_SUSP",
	"DT_FIM_SUSP",
]


def _row(**kw: object) -> CadastroAtivosRow:
	"""Build a full inclusion row, overridable."""
	base: dict[str, object] = {
		"acao": "I",
		"cd_ativ": "PETR4",
		"ds_ativ": "Petrobras PN ç",
		"tp_ativ": 2,
		"cnpj_emp_emissora": CNPJ,
		"tp_emp_emissora": 1,
		"nm_emp_emissora": "Petrobras",
		"ds_isin": "BRPETRACNPR6",
		"dt_inicio_vigen": "02/01/2024",
		"dt_fim_vigen": "31/12/2030",
		"dt_inicio_susp": "01/02/2025",
		"dt_fim_susp": "02/02/2025",
	}
	return CadastroAtivosRow(**{**base, **kw})


def _doc(*rows: CadastroAtivosRow) -> CadastroAtivosDocument:
	return CadastroAtivosDocument(
		header=CadastroAtivosHeader(cnpj_merc=CNPJ, dt_gerac_arq="05/04/2024"),
		rows=list(rows),
	)


def test_export_structure_and_order() -> None:
	"""Root, header, no namespace, row tags in the page's order, bare CNPJ."""
	xml = CadastroAtivos().export(_doc(_row()))
	assert xml is not None
	assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>')
	root = ET.fromstring(xml.split("\n", 1)[1])
	assert root.tag == "DOC_ARQ"
	assert [c.tag for c in root] == ["DESC_MERC", "ATIVOS"]
	desc = {c.tag: c.text for c in root[0]}
	assert desc == {"COD_DOC": "2", "CNPJ_MERC": "11222333000181", "DT_GERAC_ARQ": "05/04/2024"}
	assert [c.tag for c in root[1][0]] == ROW_ORDER
	assert root[1][0].findtext("CNPJ_EMP_EMISSORA") == "11222333000181"


def test_removal_omits_optional_fields() -> None:
	"""A removal needs only the identifying fields."""
	row = CadastroAtivosRow(acao="R", cd_ativ="X1", tp_ativ=1, dt_inicio_vigen="01/01/2020")
	root = ET.fromstring((CadastroAtivos().export(_doc(row)) or "").split("\n", 1)[1])
	assert [c.tag for c in root[1][0]] == ["ACAO", "CD_ATIV", "TP_ATIV", "DT_INICIO_VIGEN"]


def test_export_to_file_is_windows_1252(tmp_path: Path) -> None:
	"""Writes cp1252 bytes and returns None."""
	out = tmp_path / "a.xml"
	assert CadastroAtivos().export(_doc(_row()), output_path=str(out)) is None
	assert "ç".encode("windows-1252") in out.read_bytes()


def test_unencodable_export_keeps_previous_file(tmp_path: Path) -> None:
	"""Schema refuses text cp1252 cannot hold, so no file is touched."""
	with pytest.raises(ValidationError):
		_row(ds_ativ="日本")


@pytest.mark.parametrize("missing", ["ds_ativ", "cnpj_emp_emissora", "tp_emp_emissora"])
@pytest.mark.parametrize("acao", ["I", "A"])
def test_inclusion_and_alteration_require_descriptive_fields(acao: str, missing: str) -> None:
	"""I/A reject a missing field the page only makes optional for removal."""
	with pytest.raises(ValidationError):
		_row(acao=acao, **{missing: None})


@pytest.mark.parametrize(
	"kw",
	[
		{"acao": "X"},
		{"tp_ativ": 16},
		{"tp_ativ": 25},
		{"tp_emp_emissora": 2},
		{"dt_inicio_vigen": "2024-01-02"},
		{"dt_fim_vigen": "31/02/2024"},
		{"cnpj_emp_emissora": "11222333000182"},
		{"cd_ativ": " "},
		{"ds_ativ": "a\nb"},
	],
)
def test_invalid_row_values_rejected(kw: dict[str, object]) -> None:
	"""Out-of-table codes, bad dates/CNPJ/text are refused."""
	with pytest.raises(ValidationError):
		_row(**kw)


@pytest.mark.parametrize("code", [1, 15, 17, 24, 47, 49])
def test_table1_codes_accepted(code: int) -> None:
	"""Listed Table 1 codes pass."""
	assert _row(tp_ativ=code).tp_ativ == code


def test_row_cap_is_1000() -> None:
	"""1000 rows fit, 1001 do not, and zero rows are refused."""
	assert len(_doc(*[_row()] * 1000).rows) == 1000
	with pytest.raises(ValidationError):
		_doc(*[_row()] * 1001)
	with pytest.raises(ValidationError):
		_doc()


def test_header_rejects_bad_cod_doc_and_cnpj() -> None:
	"""COD_DOC is fixed at 2 and the venue CNPJ is check-digit validated."""
	with pytest.raises(ValidationError):
		CadastroAtivosHeader(cod_doc=3, cnpj_merc=CNPJ, dt_gerac_arq="05/04/2024")
	with pytest.raises(ValidationError):
		CadastroAtivosHeader(cnpj_merc="123", dt_gerac_arq="05/04/2024")
