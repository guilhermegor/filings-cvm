"""Unit tests for the META contracts and readers."""

from filings_cvm._internal.config.contracts.meta import META_CAD_FI, META_COLUMNS, META_DFIN_CRA


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
