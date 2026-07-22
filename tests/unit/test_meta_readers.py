"""Unit tests for the META contracts and readers."""

from pathlib import Path
import re
import shutil
import zipfile

import pytest

from filings_cvm._internal.config.contracts.meta import META_CAD_FI, META_COLUMNS, META_DFIN_CRA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.securit.doc.dfin_cra.meta import MetaDfinCraReader
from filings_cvm.ingestion.securit.doc.inf_mensal_cra.meta import MetaInfMensalCraReader


def test_meta_contracts_share_one_column_tuple() -> None:
	"""The parsed shape is OURS and identical for every dataset — only the source key differs."""
	assert META_DFIN_CRA.tuple_required == META_COLUMNS
	assert META_CAD_FI.tuple_required == META_COLUMNS


def test_meta_source_keys_are_prefixed_and_unique() -> None:
	"""`meta_` prefix keeps a META frame distinct from its own dataset's reader in bronze."""
	assert META_DFIN_CRA.str_source_key == "meta_dfin_cra"
	assert META_CAD_FI.str_source_key == "meta_cad_fi"
	assert META_DFIN_CRA.str_source_key != META_CAD_FI.str_source_key


def test_meta_contracts_declare_no_cnpj_columns() -> None:
	"""META describes fields; it holds no CNPJ values to validate."""
	assert META_DFIN_CRA.tuple_cnpj_cols == ()


_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "meta"


def _fake_download_flat(str_url: str, path_dest: Path, *args: object, **kwargs: object) -> Path:
	shutil.copyfile(_FIXTURES / "meta_dfin_cra.txt", path_dest)
	return path_dest


def _fake_download_zip(str_url: str, path_dest: Path, *args: object, **kwargs: object) -> Path:
	# The container is trivial; the member bytes are the real oracle, so build the ZIP from them.
	with zipfile.ZipFile(path_dest, "w") as cls_zip:
		cls_zip.writestr(
			"meta_inf_mensal_cra_fluxo_caixa.txt",
			(_FIXTURES / "meta_inf_mensal_cra_fluxo_caixa.txt").read_bytes(),
		)
	return path_dest


def test_flat_meta_reader_returns_the_parsed_frame(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A `.txt` META parses to one row per field, section = the dataset."""
	monkeypatch.setattr(
		"filings_cvm.ingestion._base_meta_reader.download_file", _fake_download_flat
	)
	df_ = MetaDfinCraReader().read()
	assert len(df_) == 9
	assert set(df_["section"].unique()) == {"dfin_cra"}


def test_meta_reader_stamps_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Every ingested frame carries the six provenance columns, source_key from the contract."""
	monkeypatch.setattr(
		"filings_cvm.ingestion._base_meta_reader.download_file", _fake_download_flat
	)
	df_ = MetaDfinCraReader().read()
	for str_column in FileContract.PROVENANCE_COLUMNS:
		assert str_column in df_.columns
	assert set(df_["source_key"].unique()) == {"meta_dfin_cra"}


def test_zip_meta_reader_labels_each_member_as_a_section(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A multi-member META zip yields ONE long frame; the member name becomes `section`."""
	monkeypatch.setattr(
		"filings_cvm.ingestion._base_meta_reader.download_file", _fake_download_zip
	)
	df_ = MetaInfMensalCraReader().read()
	assert set(df_["section"].unique()) == {"fluxo_caixa"}
	# The 50-char truncation survives the whole reader path, not just the parser.
	assert "Pagamentos_Classe_Subordinada_Mezanino_Amortizacao" in set(df_["field"])


def test_meta_reader_persists_the_raw_artifact(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""`path_raw` keeps the untouched bytes — the only record of what the spec said that day."""
	monkeypatch.setattr(
		"filings_cvm.ingestion._base_meta_reader.download_file", _fake_download_flat
	)
	MetaDfinCraReader(path_raw=tmp_path).read()
	assert list(tmp_path.glob("meta_dfin_cra.txt"))


def test_meta_reader_output_columns_match_the_contract(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The frame's columns are exactly the contract's declared output shape, in order."""
	monkeypatch.setattr(
		"filings_cvm.ingestion._base_meta_reader.download_file", _fake_download_flat
	)
	df_ = MetaDfinCraReader().read()
	assert tuple(df_.columns) == MetaDfinCraReader._CONTRACT.output_columns


def test_every_meta_reader_is_public_and_declares_its_url() -> None:
	"""Discovery, not a hand list: a new Meta*Reader that forgets a constant fails CI.

	Mirrors `test_reader_retry_policy.py` — the convention is enforced structurally, so it cannot
	rot the way a documented rule does.
	"""
	import filings_cvm

	list_meta = [
		getattr(filings_cvm, str_name)
		for str_name in filings_cvm.__all__
		if str_name.startswith("Meta") and str_name.endswith("Reader")
	]
	assert len(list_meta) == 37
	for cls_reader in list_meta:
		assert cls_reader._META_URL.startswith("https://dados.cvm.gov.br/dados/")
		assert "/META/" in cls_reader._META_URL
		assert cls_reader._CONTRACT.str_source_key.startswith("meta_")
		assert cls_reader._RETRY_POLICY is not None


_PATH_DOC_META = Path(__file__).resolve().parents[2] / "docs" / "ingestion" / "meta.md"

# The three phrasings in which `meta.md` states how many Meta readers there are. Matching an
# explicit set (rather than any bare number) keeps the gate from tripping on the unrelated
# "41 campos" / "19 membros" figures the same page carries.
_RE_DOC_COUNTS = re.compile(r"(\d+) no total|Os (\d+) readers|que os (\d+) compartilham")


def _exported_meta_reader_names() -> set[str]:
	"""Return the Meta readers the package exposes — the only source of truth here."""
	import filings_cvm

	return {
		str_name
		for str_name in filings_cvm.__all__
		if str_name.startswith("Meta") and str_name.endswith("Reader")
	}


def _meta_reader_names_in_docs_roster() -> tuple[str, ...]:
	"""Reader names listed in the roster table of ``docs/ingestion/meta.md``.

	Scoped to the section under the ``## Os N readers`` heading: the page carries a second table
	(the ``meta_cad_fi.txt`` vs ``.zip`` one) whose rows also name readers.
	"""
	list_lines = _PATH_DOC_META.read_text(encoding="utf-8").splitlines()
	int_start = next(
		i for i, s in enumerate(list_lines) if s.startswith("## Os ") and s.endswith(" readers")
	)

	list_names: list[str] = []
	for str_line in list_lines[int_start + 1 :]:
		if str_line.startswith("## "):
			break
		list_cells = [s.strip() for s in str_line.strip().strip("|").split("|")]
		if len(list_cells) == 3 and list_cells[1].startswith("`Meta"):
			list_names.append(list_cells[1].strip("`"))
	return tuple(list_names)


def test_docs_meta_roster_lists_every_exported_reader() -> None:
	"""The published roster is derived from the code, never trusted as prose.

	`docs/ingestion/meta.md` sat at "30 readers" through **seven** consecutive reader PRs while
	`docs/api.md` correctly said 37 — so nothing ever looked inconsistent, because no gate
	compared either page to the package. A new `Meta*Reader` whose row is missing now fails here
	instead of shipping a wrong published page (#155).
	"""
	tuple_documented = _meta_reader_names_in_docs_roster()

	assert set(tuple_documented) == _exported_meta_reader_names()
	assert len(tuple_documented) == len(set(tuple_documented))


def test_docs_meta_reader_counts_match_the_real_total() -> None:
	"""Every "N readers" claim on the page equals the number of readers that exist."""
	int_total = len(_exported_meta_reader_names())
	str_flat = " ".join(_PATH_DOC_META.read_text(encoding="utf-8").split())

	list_found = [
		int(next(s for s in match.groups() if s)) for match in _RE_DOC_COUNTS.finditer(str_flat)
	]

	# A gate that silently matches nothing is worse than no gate at all. Reworded prose must fail
	# loudly right here, rather than quietly stop checking anything.
	assert list_found, "no reader-count claim found in meta.md — did its wording change?"
	assert set(list_found) == {int_total}


def test_meta_source_keys_are_unique_across_every_reader() -> None:
	"""Two datasets sharing a source_key would be indistinguishable in the bronze table."""
	import filings_cvm

	list_keys = [
		getattr(filings_cvm, str_name)._CONTRACT.str_source_key
		for str_name in filings_cvm.__all__
		if str_name.startswith("Meta") and str_name.endswith("Reader")
	]
	assert len(list_keys) == len(set(list_keys))
