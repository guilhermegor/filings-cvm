"""Unit tests for the Informe Diário submission writer.

Cover the money/validation paths: XML structure, comma-decimal formatting,
ROUND_DOWN truncation, check-digit CNPJ rejection, the CNPJ_FDO xor
COD_SUBCLASSE rule, and the significant-shareholder block.
"""

from pathlib import Path

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InformeDiario,
	InformeDiarioDocument,
	InformeDiarioHeader,
	InformeDiarioInform,
	SignificantShareholder,
)


# A CNPJ whose check digits are valid under the repo's ASCII-48 mod-11 routine.
VALID_CNPJ = "11222333000181"


def _minimal_inform(vl_quota: str = "0", **overrides: object) -> InformeDiarioInform:
	"""Build a minimal valid INFORM exercising only the mandatory fields."""
	fields: dict[str, object] = {
		"cnpj_fdo": VALID_CNPJ,
		"data_prox_pl": "16/01/2025",
		"vl_total": "0",
		"vl_quota": vl_quota,
		"patrim_liq": "0",
		"captc_dia": "0",
		"resg_dia": "0",
		"vl_total_sai": "0",
		"vl_total_atv": "0",
		"nr_cotst": 0,
	}
	fields.update(overrides)
	return InformeDiarioInform(**fields)


def _document(inform: InformeDiarioInform) -> InformeDiarioDocument:
	"""Wrap an informe in a document with a valid header."""
	header = InformeDiarioHeader(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025")
	return InformeDiarioDocument(header=header, informs=[inform])


def test_to_xml_minimal_document_renders_expected_structure() -> None:
	"""to_xml emits the CVM document envelope, the INFORM block, and the fund CNPJ."""
	xml = InformeDiario().to_xml(_document(_minimal_inform()))

	assert xml is not None
	assert 'xmlns="urn:infdiario"' in xml
	assert "<CAB_INFORM>" in xml
	assert "<COD_DOC>1</COD_DOC>" in xml
	assert "<INFORM>" in xml
	assert f"<CNPJ_FDO>{VALID_CNPJ}</CNPJ_FDO>" in xml
	# Monetary fields render with a comma decimal separator at two places.
	assert "<PATRIM_LIQ>0,00</PATRIM_LIQ>" in xml


def test_to_xml_quota_renders_twelve_decimals() -> None:
	"""VL_QUOTA renders with the standard's up-to-12-place scale, comma-separated."""
	xml = InformeDiario().to_xml(_document(_minimal_inform(vl_quota="1.5")))

	assert xml is not None
	assert "<VL_QUOTA>1,500000000000</VL_QUOTA>" in xml


def test_to_xml_truncates_excess_precision_round_down() -> None:
	"""A value with excess precision is truncated toward zero, never rounded up."""
	xml = InformeDiario().to_xml(_document(_minimal_inform(vl_total="10.999")))

	assert xml is not None
	assert "<VL_TOTAL>10,99</VL_TOTAL>" in xml
	assert "11,00" not in xml


def test_invalid_cnpj_is_rejected() -> None:
	"""A CNPJ that fails the check digits raises a validation error."""
	with pytest.raises(ValidationError):
		_minimal_inform(cnpj_fdo="12345678000100")


def test_both_fund_identifiers_is_rejected() -> None:
	"""Providing both CNPJ_FDO and COD_SUBCLASSE violates the xor rule."""
	with pytest.raises(ValidationError):
		_minimal_inform(cod_subclasse="SUB123")


def test_neither_fund_identifier_is_rejected() -> None:
	"""Providing neither CNPJ_FDO nor COD_SUBCLASSE violates the xor rule."""
	with pytest.raises(ValidationError):
		_minimal_inform(cnpj_fdo=None)


def test_subclasse_informe_renders_cod_subclasse() -> None:
	"""A subclass informe carries COD_SUBCLASSE and omits CNPJ_FDO."""
	inform = _minimal_inform(cnpj_fdo=None, cod_subclasse="SUB123")
	xml = InformeDiario().to_xml(_document(inform))

	assert xml is not None
	assert "<COD_SUBCLASSE>SUB123</COD_SUBCLASSE>" in xml
	assert "<CNPJ_FDO>" not in xml


def test_significant_shareholder_block_renders() -> None:
	"""A significant shareholder renders inside LISTA_COTST_SIGNIF with 4-place PR_COTST."""
	cotista = SignificantShareholder(tp_pessoa="PJ", cpf_cnpj_cotst=VALID_CNPJ, pr_cotst="25.5")
	inform = _minimal_inform(nr_cotst=1, lista_cotst_signif=[cotista])
	xml = InformeDiario().to_xml(_document(inform))

	assert xml is not None
	assert "<LISTA_COTST_SIGNIF>" in xml
	assert f"<CPF_CNPJ_COTST>{VALID_CNPJ}</CPF_CNPJ_COTST>" in xml
	assert "<PR_COTST>25,5000</PR_COTST>" in xml


def test_to_xml_writes_file_in_windows_1252(tmp_path: Path) -> None:
	"""With an output path, to_xml returns None and writes a windows-1252 file.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory for the output file.
	"""
	out = tmp_path / "informe_diario.xml"
	result = InformeDiario().to_xml(_document(_minimal_inform()), output_path=str(out))

	assert result is None
	content = out.read_text(encoding="windows-1252")
	assert 'xmlns="urn:infdiario"' in content
	assert f"<CNPJ_FDO>{VALID_CNPJ}</CNPJ_FDO>" in content


def test_to_xml_rejects_wrong_argument_type() -> None:
	"""The TypeChecker metaclass rejects a mistyped argument at call time."""
	with pytest.raises(TypeError):
		InformeDiario().to_xml("not a document")
