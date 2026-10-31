"""Unit tests for the Balancete (COFI 4010) fixed-width writer."""

from decimal import Decimal
from pathlib import Path

from pydantic import ValidationError
import pytest

from filings_cvm._internal.utils.cofi_records import RECORD_LEN, footer_record
from filings_cvm.submission import (
	Balancete,
	BalanceteConta,
	BalanceteDocument,
	BalanceteFundo,
)


CNPJ = "11222333000181"
CNPJ2 = "11444777000161"


def _conta(cod: str = "1110000009", total: object = "12.34", **kw: object) -> BalanceteConta:
	"""Build an account."""
	return BalanceteConta(cod_conta=cod, vl_total=total, **kw)


def _doc(*fundos: BalanceteFundo, competence: str = "012025") -> BalanceteDocument:
	"""Build a document."""
	return BalanceteDocument(competence=competence, fundos=list(fundos) or [_fundo()])


def _fundo(cnpj: str = CNPJ, *contas: BalanceteConta) -> BalanceteFundo:
	"""Build a fund."""
	return BalanceteFundo(cnpj_fdo=cnpj, contas=list(contas) or [_conta()])


def _lines(doc: BalanceteDocument) -> list[str]:
	"""Export and split into records."""
	out = Balancete().export(doc)
	assert out is not None
	assert out.endswith("\r\n")
	return out.split("\r\n")[:-1]


def test_header_layout_matches_spec_positions() -> None:
	"""Header layout matches spec positions."""
	header = _lines(_doc())[0]
	assert len(header) == RECORD_LEN
	assert header[0:3] == "#C1"  # pos 1-3
	assert header[3:7] == "4010"  # pos 4-7
	assert header[7:21] == CNPJ  # pos 8-21
	assert header[21:29] == " " * 8  # pos 22-29 filler
	assert header[29:35] == "012025"  # pos 30-35
	assert header[35:] == " " * 36  # pos 36-71 filler


def test_account_layout_matches_spec_positions() -> None:
	"""Account layout matches spec positions."""
	doc = _doc(_fundo(CNPJ, _conta(total="12.34", vl_ate_90="-1.5", vl_apos_90="0")))
	acct = _lines(doc)[1]
	assert len(acct) == RECORD_LEN
	assert acct[0:10] == "1110000009"
	assert acct[10:14] == " " * 4
	assert acct[14:32] == "000000000000001234"
	assert acct[32] == "+"
	assert acct[33:51] == "000000000000000150"
	assert acct[51] == "-"
	assert acct[52:70] == "0" * 18
	assert acct[70] == "+"


def test_footer_counts_every_record_and_multiple_funds() -> None:
	"""Footer counts every record and multiple funds."""
	doc = _doc(_fundo(CNPJ, _conta(), _conta("1120000008")), _fundo(CNPJ2))
	lines = _lines(doc)
	assert len(lines) == 6
	footer = lines[-1]
	assert footer[0:2] == "@1"
	assert footer[2:8] == "000006"
	assert footer[8:] == " " * 63
	assert [ln[0] for ln in lines].count("#") == 2


def test_amount_truncates_toward_zero_and_negative_sign() -> None:
	"""Amount truncates toward zero and negative sign."""
	acct = _lines(_doc(_fundo(CNPJ, _conta(total="-0.999"))))[1]
	assert acct[14:32] == "000000000000000099"
	assert acct[32] == "-"


def test_zero_amount_is_positive() -> None:
	"""Zero amount is positive."""
	acct = _lines(_doc(_fundo(CNPJ, _conta(total="-0.001"))))[1]
	assert acct[14:33] == "0" * 18 + "+"


@pytest.mark.parametrize("bad", [1.5, True, "abc", "NaN", "1e30", "10000000000000000"])
def test_bad_amounts_rejected(bad: object) -> None:
	"""Bad amounts rejected."""
	with pytest.raises(ValidationError):
		_conta(total=bad)


def test_max_amount_fits() -> None:
	"""Max amount fits."""
	acct = _lines(_doc(_fundo(CNPJ, _conta(total=Decimal("9999999999999999.99")))))[1]
	assert acct[14:32] == "9" * 18


@pytest.mark.parametrize(
	"bad", ["1.1.1.00.00-9", "111000000", "11100000091", "11100000０9", "abcdefghij", "", 5]
)
def test_bad_account_code_rejected(bad: object) -> None:
	"""Bad account code rejected."""
	with pytest.raises(ValidationError):
		_conta(bad)  # type: ignore[arg-type]


def test_duplicate_account_rejected() -> None:
	"""Duplicate account rejected."""
	with pytest.raises(ValidationError):
		_fundo(CNPJ, _conta(), _conta())


def test_empty_accounts_and_funds_rejected() -> None:
	"""Empty accounts and funds rejected."""
	with pytest.raises(ValidationError):
		BalanceteFundo(cnpj_fdo=CNPJ, contas=[])
	with pytest.raises(ValidationError):
		BalanceteDocument(competence="012025", fundos=[])


@pytest.mark.parametrize(
	"bad", ["002025", "132025", "12025", "0120250", "01-2025", "０12025", 202501]
)
def test_bad_competence_rejected(bad: object) -> None:
	"""Bad competence rejected."""
	with pytest.raises(ValidationError):
		BalanceteDocument(competence=bad, fundos=[_fundo()])  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", ["11222333000180", "123", "abcdefghijklmn", 11222333000181])
def test_bad_cnpj_rejected(bad: object) -> None:
	"""Bad cnpj rejected."""
	with pytest.raises(ValidationError):
		BalanceteFundo(cnpj_fdo=bad, contas=[_conta()])  # type: ignore[arg-type]


def test_masked_cnpj_stored_bare() -> None:
	"""Masked cnpj stored bare."""
	assert BalanceteFundo(cnpj_fdo="11.222.333/0001-81", contas=[_conta()]).cnpj_fdo == CNPJ


def test_duplicate_fund_rejected() -> None:
	"""Duplicate fund rejected."""
	with pytest.raises(ValidationError):
		_doc(_fundo(CNPJ), _fundo(CNPJ))


def test_footer_count_bounds() -> None:
	"""Footer count bounds."""
	with pytest.raises(ValueError):
		footer_record(1_000_000)
	with pytest.raises(ValueError):
		footer_record(0)


def test_export_writes_file(tmp_path: Path) -> None:
	"""Export writes file."""
	target = tmp_path / "b.cvm"
	assert Balancete().export(_doc(), str(target)) is None
	assert target.read_bytes().decode("ascii") == Balancete().export(_doc())


def test_unencodable_content_does_not_wipe_existing_file(tmp_path: Path) -> None:
	"""Unencodable content does not wipe existing file."""
	# Account codes are digit-only, so force a non-ASCII char past validation.
	doc = _doc()
	object.__setattr__(doc.fundos[0].contas[0], "cod_conta", "é" * 10)
	target = tmp_path / "b.cvm"
	target.write_bytes(b"keep")
	with pytest.raises(UnicodeEncodeError):
		Balancete().export(doc, str(target))
	assert target.read_bytes() == b"keep"
