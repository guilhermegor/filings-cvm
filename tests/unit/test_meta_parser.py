"""Unit tests for the CVM META block parser.

Pinned to **real CVM bytes** (`tests/fixtures/meta/`): a fixture written by hand would only assert
our own belief. The truncation test is the one that matters — CVM cuts field names at exactly 50
chars, and this parser must hand that back verbatim rather than "repair" it.
"""

from pathlib import Path

from filings_cvm._internal.utils.meta_parser import parse_meta_blocks


_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "meta"


def _read(str_name: str) -> str:
	return (_FIXTURES / str_name).read_bytes().decode("ISO-8859-1")


def test_parse_meta_blocks_returns_one_record_per_field_in_document_order() -> None:
	"""Every `Campo:` block becomes exactly one record, in the order CVM wrote them.

	The order is CVM's own and is **not** the real artifact's column order — verified: the META
	opens with `Data_Entrega` while the `DFIN_CRA` contract opens with `CNPJ_Emissora` (8th here).
	That is exactly why the real header stays the oracle for order; the parser must not re-sort.
	"""
	list_rows = parse_meta_blocks(_read("meta_dfin_cra.txt"), "dfin_cra")
	assert len(list_rows) == 9
	assert list_rows[0]["field"] == "Data_Entrega"
	assert [r["field"] for r in list_rows].index("CNPJ_Emissora") == 7
	assert {r["section"] for r in list_rows} == {"dfin_cra"}


def test_parse_meta_blocks_strips_the_crlf_carriage_return() -> None:
	r"""CVM ships CRLF; no parsed value may keep a trailing `\r`."""
	list_rows = parse_meta_blocks(_read("meta_dfin_cra.txt"), "dfin_cra")
	assert not any("\r" in str_value for dict_row in list_rows for str_value in dict_row.values())


def test_parse_meta_blocks_preserves_cvm_50_char_truncation_verbatim() -> None:
	"""CVM truncates field names at exactly 50 chars — hand it back UNREPAIRED.

	The real header says `Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal` (60 chars);
	the META says the 50-char prefix. "Fixing" it here would fabricate a name CVM never published
	and destroy the oracle. Reconciliation is the consumer's job (#98), truncation-aware.
	"""
	list_rows = parse_meta_blocks(_read("meta_inf_mensal_cra_fluxo_caixa.txt"), "fluxo_caixa")
	set_fields = {dict_row["field"] for dict_row in list_rows}
	assert "Pagamentos_Classe_Subordinada_Mezanino_Amortizacao" in set_fields
	assert "Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal" not in set_fields
	assert max(len(str_f) for str_f in set_fields) == 50


def test_parse_meta_blocks_maps_every_attribute_and_defaults_the_absent_to_empty() -> None:
	"""A varchar block has `size` and no `precision`/`scale`; a numeric block is the reverse."""
	list_rows = parse_meta_blocks(_read("meta_dfin_cra.txt"), "dfin_cra")
	dict_by_field = {dict_row["field"]: dict_row for dict_row in list_rows}
	dict_versao = dict_by_field["Versao"]
	assert dict_versao["data_type"] == "tinyint"
	assert dict_versao["precision"] == "3"
	assert dict_versao["scale"] == "0"
	assert dict_versao["size"] == ""


def test_parse_meta_blocks_returns_empty_for_text_without_blocks() -> None:
	"""Degrade quietly on unexpected content — no exception, no fabricated rows."""
	assert parse_meta_blocks("nothing to see here", "x") == []
