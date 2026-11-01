"""Unit tests for the Informe Diário V1 submission writer, pinned to the CVM page."""

from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InformeDiarioV1,
	InformeDiarioV1Document,
	InformeDiarioV1Header,
	InformeDiarioV1Inform,
)


CNPJ = "11222333000181"
CODE_ORDER = [
	"CNPJ_FDO",
	"VL_TOTAL",
	"VL_QUOTA",
	"PATRIM_LIQ",
	"CAPTC_DIA",
	"RESG_DIA",
	"NR_COTST",
]


def _inform(**overrides: object) -> InformeDiarioV1Inform:
	"""Build a valid INFORM."""
	fields: dict[str, object] = {
		"cnpj_fdo": CNPJ,
		"vl_total": "1000.509",
		"vl_quota": "1.1234567890129",
		"patrim_liq": "5",
		"captc_dia": "0",
		"resg_dia": "0",
		"nr_cotst": 3,
	}
	fields.update(overrides)
	return InformeDiarioV1Inform(**fields)


def _xml(**overrides: object) -> str:
	"""Export a one-fund document."""
	header = InformeDiarioV1Header(dt_compt="15/01/2005", dt_gerac_arq="16/01/2005")
	doc = InformeDiarioV1Document(header=header, informs=[_inform(**overrides)])
	return InformeDiarioV1().export(doc) or ""


def test_export_tag_order_matches_page() -> None:
	"""Emit INFORM tags in the page's order."""
	assert re.findall(r"<(\w+)>[^<\n]*</", _xml())[3:] == CODE_ORDER


def test_export_header_has_no_versao() -> None:
	"""V1 has no VERSAO tag."""
	assert "VERSAO" not in _xml()


def test_export_declares_namespace_and_encoding() -> None:
	"""Use the urn:infdiario namespace and windows-1252."""
	assert _xml().startswith(
		'<?xml version="1.0" encoding="windows-1252"?>\n<DOC_ARQ xmlns="urn:infdiario">'
	)


def test_export_money_truncated_two_places_comma() -> None:
	"""Truncate money to 2 places with a comma."""
	assert "<VL_TOTAL>1000,50</VL_TOTAL>" in _xml()


def test_export_quota_truncated_twelve_places() -> None:
	"""Truncate VL_QUOTA to 12 places."""
	assert "<VL_QUOTA>1,123456789012</VL_QUOTA>" in _xml()


def test_export_without_cotistas_omits_block() -> None:
	"""Omit LISTA_COTST_SIGNIF when absent."""
	assert "LISTA_COTST_SIGNIF" not in _xml()


def test_export_cotista_participation_four_places() -> None:
	"""Render PR_COTST with 4 places."""
	cotista = {"tp_pessoa": "PJ", "cpf_cnpj_cotst": CNPJ, "pr_cotst": "25.5"}
	assert "<PR_COTST>25,5000</PR_COTST>" in _xml(lista_cotst_signif=[cotista])


@pytest.fixture
def written(tmp_path: Path) -> tuple[Path, str | None]:
	"""Export to a file; return the target and the export's return value."""
	header = InformeDiarioV1Header(dt_compt="15/01/2005", dt_gerac_arq="16/01/2005")
	doc = InformeDiarioV1Document(header=header, informs=[_inform()])
	target = tmp_path / "out.xml"
	return target, InformeDiarioV1().export(doc, str(target))


def test_export_to_file_returns_none(written: tuple[Path, str | None]) -> None:
	"""Return None when writing to a file."""
	assert written[1] is None


def test_export_to_file_writes_document(written: tuple[Path, str | None]) -> None:
	"""Write the XML document to the target."""
	assert b"<DOC_ARQ" in written[0].read_bytes()


def test_export_to_file_leaves_no_temp_files(written: tuple[Path, str | None]) -> None:
	"""Leave only the target in the directory."""
	assert [p.name for p in written[0].parent.iterdir()] == ["out.xml"]


def test_inform_invalid_cnpj_rejected() -> None:
	"""Reject a CNPJ with bad check digits."""
	with pytest.raises(ValidationError):
		_inform(cnpj_fdo="11222333000182")


def test_inform_negative_cotistas_rejected() -> None:
	"""Reject a negative NR_COTST."""
	with pytest.raises(ValidationError):
		_inform(nr_cotst=-1)


def test_header_impossible_date_rejected() -> None:
	"""Reject 31/02."""
	with pytest.raises(ValidationError):
		InformeDiarioV1Header(dt_compt="31/02/2005", dt_gerac_arq="16/01/2005")


def test_header_wrong_cod_doc_rejected() -> None:
	"""Reject COD_DOC other than 1."""
	with pytest.raises(ValidationError):
		InformeDiarioV1Header(cod_doc=2, dt_compt="15/01/2005", dt_gerac_arq="16/01/2005")


def test_document_over_100_funds_rejected() -> None:
	"""Reject more than 100 funds."""
	header = InformeDiarioV1Header(dt_compt="15/01/2005", dt_gerac_arq="16/01/2005")
	with pytest.raises(ValidationError):
		InformeDiarioV1Document(header=header, informs=[_inform()] * 101)
