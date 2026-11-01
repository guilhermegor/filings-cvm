"""Unit tests for the COFI 4016 Balanço writer, record layer and CVM checks."""

from collections.abc import Callable
from contextlib import suppress
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


def test_plan_holds_479_accounts() -> None:
	"""Plan holds 479 accounts."""
	assert len(COFI_PLAN) == 479


def test_check_digit_matches_every_account_of_the_plan() -> None:
	"""Check digit matches every account of the plan."""
	assert all(rec.is_valid_account_code(c) for c in COFI_PLAN)


@pytest.mark.parametrize("bad", ["39999994", "3999999", "３9999993"])
def test_check_digit_rejects_bad_shapes(bad: str) -> None:
	"""Check digit rejects bad shapes."""
	assert not rec.is_valid_account_code(bad)


def test_check_digit_needs_seven_digits() -> None:
	"""Check digit needs seven digits."""
	with pytest.raises(ValueError):
		rec.account_check_digit("12")


@pytest.fixture
def lines() -> list[str]:
	"""Return the exported lines of the balanced document."""
	return Balanco().export(doc(BALANCED)).split("\r\n")[:-1]


def test_every_record_is_71_columns(lines: list[str]) -> None:
	"""Every record is 71 columns."""
	assert [len(x) for x in lines] == [71] * 4


def test_header_layout_positions(lines: list[str]) -> None:
	"""Header layout positions."""
	head = lines[0]
	fields = (head[:3], head[3:7], head[7:21], head[21:29], head[29:35], head[35:])
	assert fields == ("#C1", "4016", CNPJ, " " * 8, "062026", " " * 36)


def test_account_layout_positions(lines: list[str]) -> None:
	"""Account layout positions."""
	conta = lines[1]
	one = "000000000000001000"
	fields = (conta[:10], conta[10:14], conta[14:33], conta[33:52], conta[52:71])
	assert fields == ("00" + code("3999999"), "    ", one + "+", one + "+", "0" * 18 + "+")


def test_footer_layout_positions(lines: list[str]) -> None:
	"""Footer layout positions."""
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


def test_amount_truncated_not_rounded() -> None:
	"""Amount truncated not rounded."""
	account = BalancoAccount(conta=code("3999999"), total="1.999", ate_90=0, apos_90=0)
	assert account.total == Decimal("1.99")


def test_float_amount_refused() -> None:
	"""Float amount refused."""
	with pytest.raises(ValidationError):
		BalancoAccount(conta=code("3999999"), total=1.5, ate_90=0, apos_90=0)


@pytest.mark.parametrize("amount", [Decimal("1.005"), Decimal(10) ** 17])
def test_amount_to_digits_refuses_unrepresentable(amount: Decimal) -> None:
	"""Amount to digits refuses unrepresentable."""
	with pytest.raises(ValueError):
		rec.amount_to_digits(amount)


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


def message(contas: list[dict], comp: str = "062026") -> str:
	"""Return the validation error text raised for ``contas``."""
	with pytest.raises(ValidationError) as excinfo:
		doc(contas, comp)
	return str(excinfo.value)


def test_d1_unknown_account() -> None:
	"""D1 unknown account."""
	assert "[D1]" in message([*BALANCED, acc("1999999", "0")])


def test_d1_account_not_yet_valid_on_competence() -> None:
	"""D1 account not yet valid on competence."""
	assert "[D1]" in message(BALANCED, comp="062005")


def test_d4_missing_superior() -> None:
	"""D4 missing superior."""
	assert "[D4]" in message([*BALANCED, acc("1100000", "0")])


def test_d5_duplicate() -> None:
	"""D5 duplicate."""
	with pytest.raises(ValidationError, match=r"\[D5\]"):
		doc([*BALANCED, BALANCED[0]])


def test_e1_negative_on_normal_account() -> None:
	"""E1 negative on normal account."""
	assert "[E1]" in message([acc("3999999", "-10", "-10"), acc("9999999", "-10", "-10")])


def test_e4_parent_differs_from_children() -> None:
	"""E4 parent differs from children."""
	contas = [
		acc("3999999", "5", "5"),
		acc("1000000", "5", "5"),
		acc("1100000", "3", "3"),
		acc("9999999", "5", "5"),
	]
	assert "[E4]" in message(contas)


def test_g3_total_differs_from_group_sum() -> None:
	"""G3 total differs from group sum."""
	contas = [acc("3999999", "9", "9"), acc("1000000", "5", "5"), acc("9999999", "9", "9")]
	assert "[G3]" in message(contas)


def test_g1_assets_differ_from_liabilities() -> None:
	"""G1 assets differ from liabilities."""
	assert "[G1]" in message([acc("3999999", "10", "10"), acc("9999999", "11", "11")])


def test_g2_missing_total() -> None:
	"""G2 missing total."""
	assert "[G2]" in message([acc("3999999", "10", "10")])


def test_e5_compensation_accounts_differ() -> None:
	"""E5 compensation accounts differ."""
	assert "[E5]" in message([*BALANCED, acc("3000000", "4"), acc("9000000", "5")])


def test_ex_cc3023_par44() -> None:
	"""Ex cc3023 par44."""
	contas = [*BALANCED, acc("3033000", "4"), acc("3999999", "10", "10")]
	contas = [c for c in contas if c["conta"] != code("3999999")] + [acc("3999999", "10", "10")]
	assert "[EX]" in message(contas)


def test_duplicate_fund_rejected() -> None:
	"""Duplicate fund rejected."""
	with pytest.raises(ValidationError):
		BalancoDocument(
			competencia="062026",
			fundos=[{"cnpj": CNPJ, "contas": BALANCED}, {"cnpj": CNPJ, "contas": BALANCED}],
		)


def test_empty_fund_list_rejected() -> None:
	"""Empty fund list rejected."""
	with pytest.raises(ValidationError):
		BalancoDocument(competencia="062026", fundos=[])


def test_export_with_path_returns_none(tmp_path: Path) -> None:
	"""Export with path returns none."""
	assert Balanco().export(doc(BALANCED), str(tmp_path / "b.cvm")) is None


def test_export_writes_the_ascii_bytes(tmp_path: Path) -> None:
	"""Export writes the ascii bytes."""
	out = tmp_path / "b.cvm"
	Balanco().export(doc(BALANCED), str(out))
	assert out.read_bytes() == Balanco().export(doc(BALANCED)).encode("ascii")


def test_ebcdic_header_identifier(tmp_path: Path) -> None:
	"""Ebcdic header identifier."""
	out = tmp_path / "b.cvm"
	Balanco().export(doc(BALANCED), str(out), encoding="ebcdic")
	assert out.read_bytes()[0] == 0x7B


@pytest.mark.parametrize(("content", "encoding"), [("ação", "ascii"), ("x", "utf-16")])
def test_failed_encoding_refused(tmp_path: Path, content: str, encoding: str) -> None:
	"""Failed encoding refused."""
	with pytest.raises(ValueError):
		rec.write_file(content, str(tmp_path / "b.cvm"), encoding)


def test_failed_encoding_does_not_touch_existing_file(tmp_path: Path) -> None:
	"""Failed encoding does not touch existing file."""
	out = tmp_path / "b.cvm"
	out.write_bytes(b"keep")
	with suppress(ValueError):  # the refusal itself is covered by the test above
		rec.write_file("ação", str(out))
	assert out.read_bytes() == b"keep"


@pytest.mark.parametrize(
	"build",
	[
		lambda: rec.header_record("4016", "123", "062026"),
		lambda: rec.header_record("4016", CNPJ, "6"),
		lambda: rec.footer_record(1_000_000),
		lambda: rec.numeric_field("12a", 5),
		lambda: rec.account_record("39999994", Decimal(0), Decimal(0), Decimal(0)),
	],
	ids=["cnpj", "competence", "footer", "digits", "account"],
)
def test_record_builders_reject_bad_input(build: Callable[[], str]) -> None:
	"""Record builders reject bad input."""
	with pytest.raises(ValueError):
		build()
