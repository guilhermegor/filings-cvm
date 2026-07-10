"""Unit tests for the provenance-stamping seam.

The seam appends the six provenance columns to a parsed frame. These tests pin the column set
(owned by the contract), their types, the run-scoped values, and that the input frame is never
mutated. ``hash_artifact`` is tested against a temp file.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path

import pandas as pd

from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.tabular_reader import FileContract


_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"
_HASH = "sha256:abc123"
_CONTRACT = FileContract("Cadastro", "cad_fi", ("A", "B"), ())


def _stamped() -> pd.DataFrame:
	"""Stamp a two-column frame with the shared fixtures."""
	return stamp_provenance(
		pd.DataFrame({"A": ["x", "y"], "B": ["1", "2"]}), _URL, _CONTRACT, _HASH
	)


def test_stamp_appends_all_six_columns_after_the_originals() -> None:
	"""The six provenance columns land last, in contract order, after the source columns."""
	df_ = _stamped()

	assert list(df_.columns) == ["A", "B", *FileContract.PROVENANCE_COLUMNS]
	assert list(df_["A"]) == ["x", "y"]


def test_provenance_column_names_come_from_the_contract() -> None:
	"""The names are FileContract.PROVENANCE_COLUMNS, and output_columns names the full shape."""
	assert FileContract.PROVENANCE_COLUMNS == (
		"url",
		"updated_at",
		"source_key",
		"package_version",
		"ingestion_run_id",
		"content_hash",
	)
	assert _CONTRACT.output_columns == ("A", "B", *FileContract.PROVENANCE_COLUMNS)


def test_url_source_key_and_hash_carry_their_values_as_string() -> None:
	"""url, source_key, content_hash are broadcast from their inputs, typed as string."""
	df_ = _stamped()

	assert list(df_["url"]) == [_URL, _URL]
	assert list(df_["source_key"]) == ["cad_fi", "cad_fi"]
	assert list(df_["content_hash"]) == [_HASH, _HASH]
	for str_col in ("url", "source_key", "content_hash", "package_version", "ingestion_run_id"):
		assert df_[str_col].dtype == "string"


def test_updated_at_is_a_single_tz_aware_utc_timestamp() -> None:
	"""updated_at is one tz-aware UTC instant, plausibly now, on every row (kept tz-aware)."""
	before = datetime.now(timezone.utc)
	df_ = _stamped()
	after = datetime.now(timezone.utc)

	sr = df_["updated_at"]
	assert sr.dt.tz is not None
	assert (sr == sr.iloc[0]).all()
	assert before <= sr.iloc[0].to_pydatetime() <= after


def test_ingestion_run_id_is_one_uuid_per_call() -> None:
	"""A single run id is broadcast to every row, and it differs between calls."""
	df_a = _stamped()
	df_b = _stamped()

	sr_run = df_a["ingestion_run_id"]
	assert (sr_run == sr_run.iloc[0]).all()
	assert sr_run.iloc[0] != df_b["ingestion_run_id"].iloc[0]


def test_package_version_is_stamped() -> None:
	"""package_version is a non-empty string (the installed dist version, or the fallback)."""
	df_ = _stamped()

	assert df_["package_version"].iloc[0]


def test_stamp_does_not_mutate_the_input_frame() -> None:
	"""Stamping works on a copy; the caller's frame keeps only its source columns."""
	df_input = pd.DataFrame({"A": ["x"]})

	stamp_provenance(df_input, _URL, _CONTRACT, _HASH)

	assert list(df_input.columns) == ["A"]


def test_hash_artifact_returns_prefixed_sha256(tmp_path: Path) -> None:
	"""hash_artifact returns the sha256 of the bytes, prefixed, and is stable.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided scratch directory.
	"""
	path_file = tmp_path / "artifact.bin"
	bytes_content = b"CVM open-data bytes\n" * 1000
	path_file.write_bytes(bytes_content)

	str_hash = hash_artifact(path_file)

	assert str_hash == f"sha256:{hashlib.sha256(bytes_content).hexdigest()}"
	assert hash_artifact(path_file) == str_hash


def test_hash_artifact_differs_for_different_bytes(tmp_path: Path) -> None:
	"""A one-byte change flips the digest.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided scratch directory.
	"""
	path_a = tmp_path / "a.bin"
	path_b = tmp_path / "b.bin"
	path_a.write_bytes(b"same-prefix-0")
	path_b.write_bytes(b"same-prefix-1")

	assert hash_artifact(path_a) != hash_artifact(path_b)
