"""Unit tests for the META contracts and readers."""

from pathlib import Path
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
