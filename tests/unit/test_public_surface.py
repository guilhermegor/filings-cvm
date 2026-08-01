"""Unit tests for the public import surface — the portal roots own the readers (#91).

Before this, `filings_cvm` and `filings_cvm.ingestion` each re-exported every reader into one flat
namespace. At 216 readers that is an undivided wall of names that every new reader widens, so the
surface moved to the division the data already has: the **CVM portal root**
(`dados.cvm.gov.br/dados/<ROOT>/…`). Each macro-section now owns its own names.

These tests pin the shape in **both** directions — what must be reachable, and what must *not* be —
because a half-applied refactor is silent otherwise: leaving one reader re-exported at top level
breaks nothing and no other test would notice.
"""

import importlib

import pytest

from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.introspection import iter_public_readers, iter_root_packages


# One reader per shape, named explicitly: a discovered sample would move with the code and could
# not catch "everything got re-exported again".
SAMPLE_READERS = (
	("cia_aberta", "FreCiaAbertaAuditorReader"),
	("fidc", "InfMensalFidcTabIReader"),
	("fi", "InformeDiarioReader"),
	("securit", "InfMensalCriGeralReader"),
)

SAMPLE_WRITERS = ("InformeDiario", "PerfilMensal")


def test_top_level_all_holds_only_cross_cutting_names() -> None:
	"""The root package exports what belongs to neither section — and nothing else."""
	import filings_cvm

	assert set(filings_cvm.__all__) == {"RetryPolicy", "__version__"}


@pytest.mark.parametrize(("str_root", "str_reader"), SAMPLE_READERS)
def test_reader_is_importable_from_its_portal_root(str_root: str, str_reader: str) -> None:
	"""A reader is reachable from the root package that owns it.

	Parameters
	----------
	str_root : str
		The CVM portal root package the reader belongs to.
	str_reader : str
		The reader's class name.
	"""
	module_root = importlib.import_module(f"filings_cvm.ingestion.{str_root}")

	assert str_reader in module_root.__all__
	assert issubclass(getattr(module_root, str_reader), IngestionReader)


@pytest.mark.parametrize(("str_root", "str_reader"), SAMPLE_READERS)
def test_reader_is_not_importable_from_the_top_level(str_root: str, str_reader: str) -> None:
	"""The flat top-level namespace no longer carries readers — this is the breaking change.

	Parameters
	----------
	str_root : str
		Unused here; kept so the case ids match the positive test above.
	str_reader : str
		The reader's class name.
	"""
	import filings_cvm

	assert not hasattr(filings_cvm, str_reader)
	assert str_reader not in filings_cvm.__all__


@pytest.mark.parametrize(("str_root", "str_reader"), SAMPLE_READERS)
def test_reader_is_not_importable_from_the_ingestion_package(
	str_root: str, str_reader: str
) -> None:
	"""``filings_cvm.ingestion`` groups the roots; it does not re-export their readers.

	Parameters
	----------
	str_root : str
		Unused here; kept so the case ids match the positive test above.
	str_reader : str
		The reader's class name.
	"""
	import filings_cvm.ingestion as ingestion

	assert not hasattr(ingestion, str_reader)
	assert str_reader not in ingestion.__all__


@pytest.mark.parametrize("str_writer", SAMPLE_WRITERS)
def test_writer_is_importable_only_from_the_submission_section(str_writer: str) -> None:
	"""Submission is symmetric with ingestion: its own section owns its names.

	Parameters
	----------
	str_writer : str
		The writer's class name.
	"""
	import filings_cvm
	import filings_cvm.submission as submission

	assert str_writer in submission.__all__
	assert not hasattr(filings_cvm, str_writer)


def test_ingestion_exports_exactly_the_portal_roots() -> None:
	"""``ingestion.__all__`` lists root packages, not readers — the grouping *is* the surface."""
	import filings_cvm.ingestion as ingestion

	dict_roots = iter_root_packages()

	assert set(ingestion.__all__) == set(dict_roots)
	assert len(dict_roots) == 22
	for str_name in ingestion.__all__:
		assert str_name.islower(), f"{str_name} is not a package name"


def test_every_reader_is_reachable_from_exactly_one_root() -> None:
	"""Nothing was lost or duplicated when the flat namespace went away.

	This is the precondition the refactor rests on: 216 readers were reachable flat, and the same
	216 must be reachable through the roots — no orphan, no name owned by two roots.
	"""
	dict_readers = iter_public_readers()

	assert len(dict_readers) == 216
	assert all(issubclass(cls, IngestionReader) for cls in dict_readers.values())
	# iter_public_readers raises on a duplicate name, so reaching here proves single ownership.
	int_summed = sum(len(module.__all__) for module in iter_root_packages().values())
	assert int_summed == len(dict_readers)
