"""Unit tests for the COFI 4016 Balanço writer, record layer and CVM checks."""

from decimal import Decimal
from pathlib import Path

from pydantic import ValidationError
import pytest

from filings_cvm._internal.utils import cofi_records as rec
from filings_cvm._internal.utils.cofi_plan import COFI_PLAN
from filings_cvm.submission import Balanco, BalancoAccount, BalancoDocument, BalancoFund


CNPJ = "11222333000181"


def code(body: str) -> str:
	"""Code."""
	return rec.account_code_with_check_digit(body)


def acc(body: str, total: str, a90: str = "0", b90: str = "0") -> dict:
	"""Acc."""
	return {"conta": code(body), "total": total, "ate_90": a90, "apos_90": b90}


def doc(contas: list[dict], competencia: str = "062026") -> BalancoDocument:
	"""Doc."""
	return BalancoDocument(competencia=competencia, fundos=[{"cnpj": CNPJ, "contas": contas}])


BALANCED = [acc("3999999", "10", "10"), acc("9999999", "10", "10")]


def test_check_digit_matches_every_account_of_the_plan() -> None:
	"""Check digit matches every account of the plan."""
	assert len(COFI_PLAN) == 479
	assert all(rec.is_valid_account_code(c) for c in COFI_PLAN)


def test_check_digit_rejects_bad_shapes() -> None:
	"""Check digit rejects bad shapes."""
	assert not rec.is_valid_account_code("39999994")
	assert not rec.is_valid_account_code("3999999")
	assert not rec.is_valid_account_code("３9999993")
	with pytest.raises(ValueError):
		rec.account_check_digit("12")


def test_every_record_is_71_columns_and_layout_positions() -> None:
	"""Every record is 71 columns and layout positions."""
	lines = Balanco().export(doc(BALANCED)).split("\r\n")[:-1]
	assert [len(x) for x in lines] == [71] * 4
	head = lines[0]
	assert head[:3] == "#C1" and head[3:7] == "4016" and head[7:21] == CNPJ
	assert head[21:29] == " " * 8 and head[29:35] == "062026" and head[35:] == " " * 36
	conta = lines[1]
	assert conta[:10] == "00" + code("3999999") and conta[10:14] == "    "
	assert conta[14:32] == "000000000000001000" and conta[32] == "+"
	assert conta[33:51] == "000000000000001000" and conta[51] == "+"
	assert conta[52:70] == "0" * 18 and conta[70] == "+"
	assert lines[3] == "@1000004" + " " * 63


def test_footer_count_includes_control_records_for_two_funds() -> None:
	"""Footer count includes control records for two funds."""
	d = BalancoDocument(
		competencia="062026",
		fundos=[
			{"cnpj": CNPJ, "contas": BALANCED},
			{"cnpj": "11.444.777/0001-61", "contas": BALANCED},
		],
	)
	lines = Balanco().export(d).split("\r\n")
	assert lines[-2].startswith("@1000007")


def test_accounts_written_in_code_order() -> None:
	"""Accounts written in code order."""
	lines = Balanco().export(doc(list(reversed(BALANCED)))).split("\r\n")
	assert lines[1].startswith("00" + code("3999999"))


def test_negative_amount_on_contra_account_gets_minus_sign() -> None:
	"""Negative amount on contra account gets minus sign."""
	digits, sign = rec.amount_to_digits(Decimal("-1.05"))
	assert (digits, sign) == ("0" * 15 + "105", "-")


def test_amount_truncated_not_rounded_and_float_refused() -> None:
	"""Amount truncated not rounded and float refused."""
	assert BalancoAccount(
		conta=code("3999999"), total="1.999", ate_90=0, apos_90=0
	).total == Decimal("1.99")
	with pytest.raises(ValidationError):
		BalancoAccount(conta=code("3999999"), total=1.5, ate_90=0, apos_90=0)
	with pytest.raises(ValueError):
		rec.amount_to_digits(Decimal("1.005"))
	with pytest.raises(ValueError):
		rec.amount_to_digits(Decimal(10) ** 17)


def test_account_rejects_bad_check_digit() -> None:
	"""Account rejects bad check digit."""
	with pytest.raises(ValidationError):
		BalancoAccount(conta="39999994", total=0, ate_90=0, apos_90=0)


@pytest.mark.parametrize(
	"cnpj", ["11222333000180", "1122233300018", "11222333000181 ", "abcdefghijklmn"]
)
def test_cnpj_rejected(cnpj: str) -> None:
	"""Cnpj rejected."""
	with pytest.raises(ValidationError):
		BalancoFund(
			cnpj=cnpj, contas=[BalancoAccount(conta=code("3999999"), total=0, ate_90=0, apos_90=0)]
		)


@pytest.mark.parametrize("comp", ["132026", "002026", "06202", "0620261", "061800", "６２0２６"])
def test_competence_rejected(comp: str) -> None:
	"""Competence rejected."""
	with pytest.raises(ValidationError):
		doc(BALANCED, competencia=comp)


def fails(contas: list[dict], marker: str, comp: str = "062026") -> None:
	"""Fails."""
	with pytest.raises(ValidationError, match=rf"\[{marker}\]"):
		doc(contas, comp)


def test_d1_unknown_account() -> None:
	"""D1 unknown account."""
	fails([*BALANCED, acc("1999999", "0")], "D1")


def test_d1_account_not_yet_valid_on_competence() -> None:
	"""D1 account not yet valid on competence."""
	fails(BALANCED, "D1", comp="062005")


def test_d4_missing_superior() -> None:
	"""D4 missing superior."""
	fails([*BALANCED, acc("1100000", "0")], "D4")


def test_d5_duplicate() -> None:
	"""D5 duplicate."""
	with pytest.raises(ValidationError, match=r"\[D5\]"):
		doc([*BALANCED, BALANCED[0]])


def test_e1_negative_on_normal_account() -> None:
	"""E1 negative on normal account."""
	fails([acc("3999999", "-10", "-10"), acc("9999999", "-10", "-10")], "E1")


def test_e4_parent_differs_from_children() -> None:
	"""E4 parent differs from children."""
	contas = [
		acc("3999999", "5", "5"),
		acc("1000000", "5", "5"),
		acc("1100000", "3", "3"),
		acc("9999999", "5", "5"),
	]
	fails(contas, "E4")


def test_g3_total_differs_from_group_sum() -> None:
	"""G3 total differs from group sum."""
	fails([acc("3999999", "9", "9"), acc("1000000", "5", "5"), acc("9999999", "9", "9")], "G3")


def test_g1_assets_differ_from_liabilities() -> None:
	"""G1 assets differ from liabilities."""
	fails([acc("3999999", "10", "10"), acc("9999999", "11", "11")], "G1")


def test_g2_missing_total() -> None:
	"""G2 missing total."""
	fails([acc("3999999", "10", "10")], "G2")


def test_e5_compensation_accounts_differ() -> None:
	"""E5 compensation accounts differ."""
	fails([*BALANCED, acc("3000000", "4"), acc("9000000", "5")], "E5")


def test_ex_cc3023_par44() -> None:
	"""Ex cc3023 par44."""
	contas = [*BALANCED, acc("3033000", "4"), acc("3999999", "10", "10")]
	contas = [c for c in contas if c["conta"] != code("3999999")] + [acc("3999999", "10", "10")]
	fails(contas, "EX")


def test_duplicate_fund_and_empty_lists_rejected() -> None:
	"""Duplicate fund and empty lists rejected."""
	with pytest.raises(ValidationError):
		BalancoDocument(
			competencia="062026",
			fundos=[{"cnpj": CNPJ, "contas": BALANCED}, {"cnpj": CNPJ, "contas": BALANCED}],
		)
	with pytest.raises(ValidationError):
		BalancoDocument(competencia="062026", fundos=[])


def test_export_writes_bytes_and_returns_none(tmp_path: Path) -> None:
	"""Export writes bytes and returns none."""
	out = tmp_path / "b.cvm"
	assert Balanco().export(doc(BALANCED), str(out)) is None
	assert out.read_bytes() == Balanco().export(doc(BALANCED)).encode("ascii")


def test_ebcdic_header_identifier(tmp_path: Path) -> None:
	"""Ebcdic header identifier."""
	out = tmp_path / "b.cvm"
	Balanco().export(doc(BALANCED), str(out), encoding="ebcdic")
	assert out.read_bytes()[0] == 0x7B


def test_failed_encoding_does_not_touch_existing_file(tmp_path: Path) -> None:
	"""Failed encoding does not touch existing file."""
	out = tmp_path / "b.cvm"
	out.write_bytes(b"keep")
	with pytest.raises(ValueError):
		rec.write_file("ação", str(out))
	with pytest.raises(ValueError):
		rec.write_file("x", str(out), "utf-16")
	assert out.read_bytes() == b"keep"


def test_record_builders_reject_bad_input() -> None:
	"""Record builders reject bad input."""
	with pytest.raises(ValueError):
		rec.header_record("4016", "123", "062026")
	with pytest.raises(ValueError):
		rec.header_record("4016", CNPJ, "6")
	with pytest.raises(ValueError):
		rec.footer_record(1_000_000)
	with pytest.raises(ValueError):
		rec.numeric_field("12a", 5)
	with pytest.raises(ValueError):
		rec.account_record("39999994", Decimal(0), Decimal(0), Decimal(0))
