"""CVM consistency checks (críticas) of the Balanço that can be decided from the file alone.

The CVM page ``PadraoXMLBalanco.asp`` lists the checks its receiving system applies to a
Balanço (codes ``D1``…``KD``). This module implements the *mechanical* ones as pure
functions over one fund's accounts, so a document that would be refused is rejected before
it is written:

====  =============================================================================
Code  Check
====  =============================================================================
D1    account missing from the COFI plan, or not valid on the competence date
D4    account whose superior account is not in the file ("falta nível superior")
D5    account informed more than once
E1    sign contradicts the nature (normal: not negative; contra: not positive)
E4    an account differs from the sum of its subordinate accounts in the file
E5    compensation accounts ``3.0.x`` and ``9.0.x`` differ
EX    CC 3.023 §44: ``3.0.3.30/40/50`` sum differs from ``1.3.0`` minus ``1.3.3``
G1    total do ativo differs from total do passivo
G2    total do ativo and/or total do passivo missing
G3    total do ativo/passivo differs from the sum of its group accounts
====  =============================================================================

``D7`` (a column left blank) is enforced by the schema, which makes all three amount
columns mandatory; ``KD`` (record order) holds by construction because the writer emits
header, accounts in code order, then footer. ``D2`` (mandatory sub-accounts) is not
decidable from the published plan, which does not mark which breakdowns are obligatory,
and is not implemented.

Scope decisions the page leaves open: E4 compares every one of the three columns; E5,
EX and G1 compare the *total* column, the balance each check names.
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal

from filings_cvm._internal.utils.cofi_plan import COFI_PLAN
from filings_cvm._internal.utils.cofi_records import account_code_with_check_digit
from filings_cvm._internal.utils.typing import type_checker


Amounts = tuple[Decimal, Decimal, Decimal]

_ROOT_PARENT = "00000000"
_TOTAL_COLUMN = 0
ASSETS_TOTAL = account_code_with_check_digit("3999999")
LIABILITIES_TOTAL = account_code_with_check_digit("9999999")
_TOTALS = frozenset({ASSETS_TOTAL, LIABILITIES_TOTAL})
# Compensation pairs named by check E5 (asset side, liability side), as 7-digit bodies.
_COMPENSATION_PAIRS = tuple(
	(account_code_with_check_digit(f"3{n}0000"), account_code_with_check_digit(f"9{n}0000"))
	for n in ("00", "01", "03", "04", "05", "06", "08", "09")
)
_EX_SUMMED = tuple(
	account_code_with_check_digit(body) for body in ("3033000", "3034000", "3035000")
)
_EX_MINUEND = account_code_with_check_digit("1300000")
_EX_SUBTRAHEND = account_code_with_check_digit("1330000")
_COLUMN_NAMES = ("total", "até 90 dias", "após 90 dias")


@type_checker
def _total(accounts: dict[str, Amounts], code: str) -> Decimal:
	"""Return the total column of ``code``, zero when the account is absent.

	Parameters
	----------
	accounts : dict[str, Amounts]
		The fund's accounts by code.
	code : str
		Account code.

	Returns
	-------
	Decimal
		The total-column amount, or zero.
	"""
	return accounts[code][_TOTAL_COLUMN] if code in accounts else Decimal(0)


@type_checker
def _check_plan(code: str, reference: date) -> list[str]:
	"""Apply check D1 to one account.

	Parameters
	----------
	code : str
		Account code.
	reference : date
		Last day of the competence month.

	Returns
	-------
	list[str]
		Zero or one error message.
	"""
	entry = COFI_PLAN.get(code)
	if entry is None:
		return [f"[D1] account {code} is not in the COFI plan"]
	_nature, _parent, start, end = entry
	if start > reference or (end is not None and end < reference):
		return [f"[D1] account {code} is not valid on {reference.isoformat()}"]
	return []


@type_checker
def _check_sign(code: str, amounts: Amounts) -> list[str]:
	"""Apply check E1 to one account.

	Parameters
	----------
	code : str
		Account code (known to be in the plan).
	amounts : Amounts
		The three amount columns.

	Returns
	-------
	list[str]
		One message per column whose sign contradicts the account nature.
	"""
	nature = COFI_PLAN[code][0]
	errors = []
	for name, value in zip(_COLUMN_NAMES, amounts, strict=True):
		if (nature == "N" and value < 0) or (nature == "R" and value > 0):
			errors.append(f"[E1] account {code} ({name}): sign contradicts nature {nature}")
	return errors


@type_checker
def _check_children_sum(accounts: dict[str, Amounts]) -> list[str]:
	"""Apply checks E4 and G3: every account must equal the sum of its children.

	Parameters
	----------
	accounts : dict[str, Amounts]
		The fund's accounts by code (all in the plan).

	Returns
	-------
	list[str]
		One message per column that does not add up.
	"""
	children = defaultdict(list)
	for code in accounts:
		children[COFI_PLAN[code][1]].append(code)
	errors = []
	for parent, codes in children.items():
		if parent not in accounts:
			continue
		check = "G3" if parent in _TOTALS else "E4"
		for column, name in enumerate(_COLUMN_NAMES):
			expected = sum((accounts[code][column] for code in codes), Decimal(0))
			if accounts[parent][column] != expected:
				errors.append(
					f"[{check}] account {parent} ({name}) is {accounts[parent][column]}, "
					f"its subitems add up to {expected}"
				)
	return errors


@type_checker
def _check_totals(accounts: dict[str, Amounts]) -> list[str]:
	"""Apply checks G2, G1, E5 and EX on the total column.

	Parameters
	----------
	accounts : dict[str, Amounts]
		The fund's accounts by code.

	Returns
	-------
	list[str]
		The messages of every failed check.
	"""
	errors = [
		f"[G2] total account {code} is missing"
		for code in (ASSETS_TOTAL, LIABILITIES_TOTAL)
		if code not in accounts
	]
	if not errors and _total(accounts, ASSETS_TOTAL) != _total(accounts, LIABILITIES_TOTAL):
		errors.append("[G1] total do ativo differs from total do passivo")
	errors.extend(
		f"[E5] compensation accounts {asset} and {liability} differ"
		for asset, liability in _COMPENSATION_PAIRS
		if _total(accounts, asset) != _total(accounts, liability)
	)
	summed = sum((_total(accounts, code) for code in _EX_SUMMED), Decimal(0))
	if summed != _total(accounts, _EX_MINUEND) - _total(accounts, _EX_SUBTRAHEND):
		errors.append("[EX] 3.0.3.30/40/50 differ from 1.3.0 minus 1.3.3 (CC 3.023 par. 44)")
	return errors


@type_checker
def check_fund_accounts(accounts: dict[str, Amounts], reference: date) -> list[str]:
	"""Run every mechanical CVM check over one fund's accounts.

	Parameters
	----------
	accounts : dict[str, Amounts]
		The fund's accounts by 8-character code, three amount columns each. Duplicates
		(D5) must be rejected by the caller, which sees the raw list.
	reference : date
		Last day of the competence month, the date the plan validity is judged on.

	Returns
	-------
	list[str]
		Error messages prefixed with the CVM check code; empty when the fund passes.
	"""
	errors: list[str] = []
	for code in accounts:
		errors.extend(_check_plan(code, reference))
	if errors:
		return errors
	for code, amounts in accounts.items():
		errors.extend(_check_sign(code, amounts))
		parent = COFI_PLAN[code][1]
		if parent != _ROOT_PARENT and parent not in accounts:
			errors.append(f"[D4] account {code} is missing its superior account {parent}")
	errors.extend(_check_children_sum(accounts))
	errors.extend(_check_totals(accounts))
	return errors
