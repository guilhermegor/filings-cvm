"""Unit tests for the Informe Diário V2 writer, pinned to PadraoXMLInfoDiarioNet739."""

import re

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InformeDiarioV2,
	InformeDiarioV2Document,
	InformeDiarioV2Header,
	InformeDiarioV2Inform,
	SignificantShareholder,
)


VALID_CNPJ = "11222333000181"
VALID_CPF = "52998224725"

# Tag order of the sample file on the CVM page (INFORM block).
INFORM_TAGS = [
	"CNPJ_FDO",
	"VL_TOTAL",
	"VL_QUOTA",
	"PATRIM_LIQ",
	"CAPTC_DIA",
	"RESG_DIA",
	"VL_TOTAL_SAI",
	"VL_TOTAL_ATV",
	"NR_COTST",
	"LISTA_COTST_SIGNIF",
]


def _fields(**overrides: object) -> dict[str, object]:
	fields: dict[str, object] = {
		"cnpj_fdo": VALID_CNPJ,
		"vl_total": "1.239",
		"vl_quota": "1.1234567890129",
		"patrim_liq": "0",
		"captc_dia": "0",
		"resg_dia": "0",
		"vl_total_sai": "0",
		"vl_total_atv": "0",
		"nr_cotst": 3,
	}
	fields.update(overrides)
	return fields


def _doc(**overrides: object) -> InformeDiarioV2Document:
	header = InformeDiarioV2Header(dt_compt="15/01/2014", dt_gerac_arq="16/01/2014")
	return InformeDiarioV2Document(
		header=header, informs=[InformeDiarioV2Inform(**_fields(**overrides))]
	)


def _xml(**overrides: object) -> str:
	xml = InformeDiarioV2().export(_doc(**overrides))
	assert xml is not None
	return xml


def test_versao_is_two_point_zero() -> None:
	"""The header carries VERSAO 2.0."""
	assert "<VERSAO>2.0</VERSAO>" in _xml()


def test_header_tag_order() -> None:
	"""CAB_INFORM follows COD_DOC, DT_COMPT, DT_GERAC_ARQ, VERSAO."""
	tags = re.findall(r"<(\w+)>", _xml().split("</CAB_INFORM>")[0])
	assert tags[1:] == ["COD_DOC", "DT_COMPT", "DT_GERAC_ARQ", "VERSAO"]


def test_inform_tag_order() -> None:
	"""INFORM tags follow the page, including the optional shareholder list."""
	cotst = SignificantShareholder(tp_pessoa="PF", cpf_cnpj_cotst=VALID_CPF, pr_cotst="25")
	xml = _xml(lista_cotst_signif=[cotst])
	body = xml.split("<INFORM>")[1].split("</INFORM>")[0]
	top = re.findall(r"^ {8}<(\w+)>", body, flags=re.M)
	assert top == INFORM_TAGS


def test_no_v4_only_tags() -> None:
	"""V4's DATA_PROX_PL and COD_SUBCLASSE do not exist in V2."""
	assert "DATA_PROX_PL" not in _xml()


def test_money_truncated_to_two_places_with_comma() -> None:
	"""Monetary fields keep 2 places, truncated toward zero."""
	assert "<VL_TOTAL>1,23</VL_TOTAL>" in _xml()


def test_quota_keeps_twelve_places() -> None:
	"""VL_QUOTA allows 12 places, truncated."""
	assert "<VL_QUOTA>1,123456789012</VL_QUOTA>" in _xml()


def test_participation_four_places() -> None:
	"""PR_COTST renders 4 places."""
	cotst = SignificantShareholder(tp_pessoa="PJ", cpf_cnpj_cotst=VALID_CNPJ, pr_cotst="20.5")
	assert "<PR_COTST>20,5000</PR_COTST>" in _xml(lista_cotst_signif=[cotst])


def test_invalid_cnpj_rejected() -> None:
	"""A CNPJ with bad check digits is refused."""
	with pytest.raises(ValidationError):
		InformeDiarioV2Inform(**_fields(cnpj_fdo="11222333000182"))


def test_cod_subclasse_not_accepted() -> None:
	"""V2 is keyed by CNPJ_FDO only; the V4 subclass field is not a field here."""
	assert "cod_subclasse" not in InformeDiarioV2Inform.model_fields


def test_more_than_100_funds_rejected() -> None:
	"""The page caps a file at 100 funds."""
	header = InformeDiarioV2Header(dt_compt="15/01/2014", dt_gerac_arq="16/01/2014")
	informs = [InformeDiarioV2Inform(**_fields())] * 101
	with pytest.raises(ValidationError):
		InformeDiarioV2Document(header=header, informs=informs)


def test_wrong_versao_rejected() -> None:
	"""VERSAO is pinned to 2.0."""
	with pytest.raises(ValidationError):
		InformeDiarioV2Header(dt_compt="15/01/2014", dt_gerac_arq="16/01/2014", versao="4.0")


def test_export_to_file_returns_none(tmp_path: object) -> None:
	"""export(output_path) returns None."""
	path = tmp_path / "v2.xml"  # type: ignore[operator]
	assert InformeDiarioV2().export(_doc(), output_path=str(path)) is None


def test_file_written_as_windows_1252(tmp_path: object) -> None:
	"""The written file declares and uses windows-1252."""
	path = tmp_path / "v2.xml"  # type: ignore[operator]
	InformeDiarioV2().export(_doc(), output_path=str(path))
	assert path.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def test_cod_doc_other_than_one_rejected() -> None:
	"""The page fixes COD_DOC at 1 for daily reports."""
	with pytest.raises(ValidationError):
		InformeDiarioV2Header(dt_compt="15/01/2014", dt_gerac_arq="16/01/2014", cod_doc=2)


def test_export_overwrite_preserves_mode(tmp_path: object) -> None:
	"""Overwriting keeps the target's permission bits."""
	path = tmp_path / "v2.xml"  # type: ignore[operator]
	path.write_bytes(b"old")
	path.chmod(0o644)
	InformeDiarioV2().export(_doc(), output_path=str(path))
	assert path.stat().st_mode & 0o777 == 0o644


def test_export_leaves_no_temp_file(tmp_path: object) -> None:
	"""A finished export leaves only the target in the directory."""
	path = tmp_path / "v2.xml"  # type: ignore[operator]
	InformeDiarioV2().export(_doc(), output_path=str(path))
	assert [p.name for p in path.parent.iterdir()] == ["v2.xml"]
