"""Unit tests for ``bin/check_contract_drift.py`` — the weekly contract-drift oracles.

Loaded by path (``bin/`` is not an importable package), the same way
``test_check_backlog_ledger.py`` loads its target. The pure comparison functions carry all the
logic and take no network — the online orchestration is a thin seam around them.
"""

import importlib.util
import inspect
from pathlib import Path

import pandas as pd
import pytest

from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
import filings_cvm.ingestion as ingestion
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


_PATH = Path(__file__).resolve().parents[2] / "bin" / "check_contract_drift.py"
_SPEC = importlib.util.spec_from_file_location("check_contract_drift", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
ccd = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ccd)


def _reader_classes() -> list[type]:
	"""Every public reader discovered from the ingestion API."""
	return [
		cls
		for cls in (getattr(ingestion, name) for name in ingestion.__all__)
		if inspect.isclass(cls) and issubclass(cls, IngestionReader)
	]


def _fake_reader(
	contract: FileContract,
	frame: pd.DataFrame | None = None,
	error: Exception | None = None,
	dated: bool = False,
	name: str = "_Fake",
) -> type:
	"""Build a stand-in reader class: no network, returns a preset frame or raises a preset error.

	``dated`` gives the constructor a ``date_ref`` parameter, so ``check_real_header`` treats it as
	a period-partitioned reader and probes reference dates. ``name`` sets the class name, which the
	partial-dataset lookups key on.
	"""

	def read(self: object, int_timeout_s: int = 60) -> pd.DataFrame:
		if error is not None:
			raise error
		assert frame is not None
		return frame

	if dated:

		def __init__(self: object, date_ref: object = None, retry_policy: object = None) -> None:
			type(self)._last_retry_policy = retry_policy

	else:

		def __init__(self: object, retry_policy: object = None) -> None:
			type(self)._last_retry_policy = retry_policy

	return type(
		name,
		(),
		{
			"_CONTRACT": contract,
			"_last_retry_policy": None,
			"__init__": __init__,
			"read": read,
		},
	)


# ---- real_header_drift: contract columns vs the real artifact header (order preserved) --------


def test_real_header_matching_columns_report_no_drift() -> None:
	"""Identical columns in identical order → no drift."""
	assert ccd.real_header_drift("X", ("A", "B", "C"), ("A", "B", "C")) == []


def test_real_header_flags_a_column_cvm_added() -> None:
	"""A column present in the real header but absent from the contract is drift."""
	list_problems = ccd.real_header_drift("X", ("A", "B"), ("A", "B", "C"))

	assert len(list_problems) == 1
	assert "'C'" in list_problems[0]


def test_real_header_flags_a_column_cvm_removed() -> None:
	"""A contract column no longer in the real header is drift."""
	list_problems = ccd.real_header_drift("X", ("A", "B", "C"), ("A", "B"))

	assert len(list_problems) == 1
	assert "'C'" in list_problems[0]


def test_real_header_flags_a_reordering_with_the_same_column_set() -> None:
	"""Same columns, different order → drift (order is compared against the real header)."""
	list_problems = ccd.real_header_drift("X", ("A", "B", "C"), ("A", "C", "B"))

	assert len(list_problems) == 1
	assert "order" in list_problems[0].lower()


# ---- meta_name_drift: contract columns vs META field names (truncation-aware) -----------------


def test_meta_names_matching_within_fifty_chars_report_no_drift() -> None:
	"""Field names that match report no drift."""
	assert ccd.meta_name_drift("X", ("A", "B"), frozenset({"A", "B"})) == []


def test_meta_names_are_compared_truncated_to_fifty_chars() -> None:
	"""CVM truncates META names at 50 chars — a longer contract column matches on its prefix."""
	str_long = "Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal"  # 60 chars
	str_meta = str_long[:50]

	assert ccd.meta_name_drift("X", (str_long,), frozenset({str_meta})) == []


def test_meta_names_flag_a_field_no_contract_column_covers() -> None:
	"""A META field matched by no contract column (past truncation) is drift."""
	list_problems = ccd.meta_name_drift("X", ("A",), frozenset({"A", "B"}))

	assert len(list_problems) == 1
	assert "'B'" in list_problems[0]


def test_meta_names_flag_a_contract_column_absent_from_meta() -> None:
	"""A contract column whose truncated name is in no META field is drift."""
	list_problems = ccd.meta_name_drift("X", ("A", "B"), frozenset({"A"}))

	assert len(list_problems) == 1
	assert "'B'" in list_problems[0]


# ---- partial-coverage suppression of the extra-column direction -------------------------------


def test_real_header_extra_column_suppressed_when_report_extra_false() -> None:
	"""A partial contract (subset of the header) does not flag the columns it doesn't require."""
	assert ccd.real_header_drift("X", ("A", "B"), ("A", "B", "C"), bool_report_extra=False) == []


def test_real_header_missing_required_still_flagged_when_report_extra_false() -> None:
	"""Even for a partial contract, a REQUIRED column gone from the header is still drift."""
	list_problems = ccd.real_header_drift("X", ("A", "B"), ("A",), bool_report_extra=False)

	assert len(list_problems) == 1
	assert "'B'" in list_problems[0]


def test_meta_extra_field_suppressed_when_report_extra_false() -> None:
	"""A partial dataset does not flag META fields it deliberately doesn't cover."""
	assert ccd.meta_name_drift("X", ("A",), frozenset({"A", "B"}), bool_report_extra=False) == []


def test_meta_missing_required_still_flagged_when_report_extra_false() -> None:
	"""Even for a partial dataset, a contract column absent from META is still reported."""
	list_problems = ccd.meta_name_drift("X", ("A", "B"), frozenset({"A"}), bool_report_extra=False)

	assert len(list_problems) == 1
	assert "'B'" in list_problems[0]


# ---- contract resolution + frame helpers ------------------------------------------------------

_CONTRACT = FileContract(
	str_name="X", str_source_key="x", tuple_required=("A", "B"), tuple_cnpj_cols=()
)


def test_contract_of_reads_the_classvar_when_present() -> None:
	"""A reader exposing ``_CONTRACT`` resolves to it directly."""
	cls_reader = type("_WithClassvar", (), {"_CONTRACT": _CONTRACT})

	assert ccd.contract_of(cls_reader) is _CONTRACT


def test_contract_of_falls_back_to_the_unexposed_map() -> None:
	"""A single reader without ``_CONTRACT`` resolves via the explicit map, keyed by class name."""
	cls_reader = type("DfinCraReader", (), {})  # name is a key in _UNEXPOSED_CONTRACTS

	assert ccd.contract_of(cls_reader) is ccd._UNEXPOSED_CONTRACTS["DfinCraReader"]


def test_real_columns_strips_the_provenance_tail() -> None:
	"""The source columns are everything before the six provenance columns."""
	df_read = pd.DataFrame(columns=["A", "B", *FileContract.PROVENANCE_COLUMNS])

	assert ccd.real_columns(df_read) == ("A", "B")


# ---- online checks (fakes, no network) --------------------------------------------------------


def test_check_real_header_reports_no_drift_when_the_header_matches() -> None:
	"""A real header equal to the contract columns is clean."""
	df_read = pd.DataFrame(columns=["A", "B", *FileContract.PROVENANCE_COLUMNS])
	cls_reader = _fake_reader(_CONTRACT, frame=df_read)

	assert ccd.check_real_header(cls_reader) == []


def test_check_real_header_flags_a_column_cvm_added() -> None:
	"""A column in the real header but not the contract is flagged."""
	df_read = pd.DataFrame(columns=["A", "B", "C", *FileContract.PROVENANCE_COLUMNS])
	cls_reader = _fake_reader(_CONTRACT, frame=df_read)

	list_problems = ccd.check_real_header(cls_reader)

	assert len(list_problems) == 1
	assert "'C'" in list_problems[0]


def test_check_real_header_reports_a_contract_error_as_drift() -> None:
	"""A ContractError (CVM dropped a required column) is reported, not swallowed."""
	cls_reader = _fake_reader(_CONTRACT, error=ContractError(["missing column"]))

	list_problems = ccd.check_real_header(cls_reader)

	assert len(list_problems) == 1
	assert "contract" in list_problems[0].lower()


def test_check_real_header_tolerates_an_unpublished_period() -> None:
	"""A dated reader whose every probed period 404s is skipped, not flagged as drift."""
	cls_reader = _fake_reader(_CONTRACT, error=OSError("404"), dated=True)

	assert ccd.check_real_header(cls_reader) == []


def test_check_meta_reconciles_the_union_of_member_columns() -> None:
	"""META fields are compared against the union of every member contract's columns."""
	df_meta = pd.DataFrame({"section": ["s"], "field": ["A"]})  # META omits B
	cls_meta = _fake_reader(_CONTRACT, frame=df_meta)
	cls_member = type("_Member", (), {"_CONTRACT": _CONTRACT})

	list_problems = ccd.check_meta(cls_meta, (cls_member,))

	assert len(list_problems) == 1
	assert "'B'" in list_problems[0]


def test_check_meta_tolerates_unavailable_meta() -> None:
	"""A META download failure is not drift."""
	cls_meta = _fake_reader(_CONTRACT, error=OSError("timeout"))
	cls_member = type("_Member", (), {"_CONTRACT": _CONTRACT})

	assert ccd.check_meta(cls_meta, (cls_member,)) == []


def test_drift_retry_policy_is_single_attempt() -> None:
	"""The drift probe fails fast — one attempt, no patient backoff on an expected 404."""
	assert ccd._DRIFT_RETRY_POLICY.int_max_attempts == 1


def test_check_real_header_builds_the_reader_with_the_fast_fail_policy() -> None:
	"""A probed reader is constructed with the drift fail-fast policy, not the patient default."""
	df_read = pd.DataFrame(columns=["A", "B", *FileContract.PROVENANCE_COLUMNS])
	cls_reader = _fake_reader(_CONTRACT, frame=df_read, dated=True)

	ccd.check_real_header(cls_reader)

	assert cls_reader._last_retry_policy is ccd._DRIFT_RETRY_POLICY


def test_check_meta_builds_the_reader_with_the_fast_fail_policy() -> None:
	"""The META reader is likewise constructed with the fail-fast policy."""
	df_meta = pd.DataFrame({"section": ["s"], "field": ["A"]})
	cls_meta = _fake_reader(_CONTRACT, frame=df_meta)
	cls_member = type("_Member", (), {"_CONTRACT": _CONTRACT})

	ccd.check_meta(cls_meta, (cls_member,))

	assert cls_meta._last_retry_policy is ccd._DRIFT_RETRY_POLICY


def test_check_meta_suppresses_extra_for_a_partial_dataset(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A partial dataset does not report a META field it deliberately doesn't cover."""
	df_meta = pd.DataFrame({"section": ["s", "s"], "field": ["A", "B"]})  # META has extra B
	cls_meta = _fake_reader(_CONTRACT, frame=df_meta, name="MetaFooReader")
	monkeypatch.setitem(ccd._PARTIAL_DATASETS, "MetaFooReader", "test partial")
	cls_member = type("_Member", (), {"_CONTRACT": _CONTRACT})

	assert ccd.check_meta(cls_meta, (cls_member,)) == []


def test_check_meta_partial_still_flags_a_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Even a partial dataset reports a contract column absent from META (load-bearing)."""
	df_meta = pd.DataFrame({"section": ["s"], "field": ["A"]})  # contract is (A, B); META lacks B
	cls_meta = _fake_reader(_CONTRACT, frame=df_meta, name="MetaFooReader")
	monkeypatch.setitem(ccd._PARTIAL_DATASETS, "MetaFooReader", "test partial")
	cls_member = type("_Member", (), {"_CONTRACT": _CONTRACT})

	list_problems = ccd.check_meta(cls_meta, (cls_member,))

	assert len(list_problems) == 1
	assert "'B'" in list_problems[0]


def test_check_real_header_suppresses_extra_for_a_partial_dataset(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A partial dataset's reader does not flag a header column its subset contract omits."""
	df_read = pd.DataFrame(columns=["A", "B", "C", *FileContract.PROVENANCE_COLUMNS])  # extra C
	cls_reader = _fake_reader(_CONTRACT, frame=df_read, name="FooReader")
	monkeypatch.setitem(ccd._READER_TO_META, "FooReader", "MetaFooReader")
	monkeypatch.setitem(ccd._PARTIAL_DATASETS, "MetaFooReader", "test partial")

	assert ccd.check_real_header(cls_reader) == []


# ---- issue upsert logic (no network) ----------------------------------------------------------


def test_find_open_drift_issue_matches_the_marker() -> None:
	"""The tracking issue is recognised by its hidden body marker."""
	list_issues = [
		{"number": 1, "body": "unrelated"},
		{"number": 2, "body": f"{ccd._ISSUE_MARKER}\nstuff"},
	]

	assert ccd.find_open_drift_issue(list_issues) == 2


def test_find_open_drift_issue_returns_none_without_the_marker() -> None:
	"""No marker anywhere → nothing to update (a fresh issue will be opened)."""
	assert ccd.find_open_drift_issue([{"number": 1, "body": "unrelated"}]) is None


def test_build_issue_body_carries_the_marker_and_the_count() -> None:
	"""The body carries the dedupe marker and the number of problems."""
	str_body = ccd.build_issue_body(["a: x", "b: y"])

	assert ccd._ISSUE_MARKER in str_body
	assert "**2**" in str_body


# ---- structural: the explicit registry stays complete -----------------------------------------


def test_every_meta_reader_is_a_key_in_the_registry() -> None:
	"""No META reader may be added without wiring it into ``_META_MEMBERS``."""
	set_meta = {cls.__name__ for cls in _reader_classes() if issubclass(cls, BaseMetaReader)}

	assert set_meta == set(ccd._META_MEMBERS)


def test_every_real_reader_is_covered_by_exactly_one_dataset() -> None:
	"""Every non-META reader appears under exactly one META's members (no gaps, no overlaps)."""
	list_members = [name for names in ccd._META_MEMBERS.values() for name in names]
	set_real = {cls.__name__ for cls in _reader_classes() if not issubclass(cls, BaseMetaReader)}

	assert len(list_members) == len(set(list_members)), "a reader is listed under two datasets"
	assert set(list_members) == set_real


def test_every_registry_name_resolves_to_a_reader() -> None:
	"""Every class name in the registry resolves to a real reader on the public API."""
	list_names = list(ccd._META_MEMBERS) + [
		name for names in ccd._META_MEMBERS.values() for name in names
	]
	for str_name in list_names:
		cls = getattr(ingestion, str_name, None)
		assert inspect.isclass(cls) and issubclass(cls, IngestionReader), str_name


def test_contract_of_resolves_for_every_real_reader() -> None:
	"""Every non-META reader has a reachable contract (classvar or the unexposed map)."""
	for cls in _reader_classes():
		if issubclass(cls, BaseMetaReader):
			continue
		assert isinstance(ccd.contract_of(cls), FileContract), cls.__name__


def test_every_partial_dataset_is_a_real_meta_reader() -> None:
	"""Each ``_PARTIAL_DATASETS`` key is a META reader in the registry (a typo can't hide here)."""
	assert set(ccd._PARTIAL_DATASETS) <= set(ccd._META_MEMBERS)


def test_reader_to_meta_is_the_exact_inverse_of_the_registry() -> None:
	"""``_READER_TO_META`` maps every member reader to its dataset — derived, never restated."""
	dict_expected = {
		str_reader: str_meta
		for str_meta, tuple_readers in ccd._META_MEMBERS.items()
		for str_reader in tuple_readers
	}

	assert dict_expected == ccd._READER_TO_META
