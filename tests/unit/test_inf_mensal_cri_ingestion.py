"""Unit tests for the CVM Informe Mensal CRI (INF_MENSAL_CRI) ingestion readers.

The download boundary is patched, so nothing here touches the network (the autouse socket guard in
``conftest`` makes that structural anyway).

⚠️ **The most important test in this file is `test_contract_matches_the_published_header`** — it is
the only one whose expected value is **not** ours. Every other assertion here is, at bottom,
a tautology: fixtures are built from ``_CONTRACT.tuple_required``, so a wrong contract would make
them all pass on wrong data. Not hypothetical — CRI's 11 members share seven section names with
CRA/OTS, and copying a sibling's contracts would have shipped wrong ones with the suite all green.
The header fixtures under ``tests/fixtures/inf_mensal_cri/`` are the verbatim header bytes CVM
publishes, so that one test compares the contract against **the source**, not against our belief.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm import (
	InfMensalCriAtivoPassivoReader,
	InfMensalCriCarteiraModificacaoReader,
	InfMensalCriCarteiraReader,
	InfMensalCriCedenteDevedorReader,
	InfMensalCriClasseReader,
	InfMensalCriCreditosReader,
	InfMensalCriDerivativosReader,
	InfMensalCriDesembolsoReader,
	InfMensalCriFluxoCaixaReader,
	InfMensalCriGeralReader,
	InfMensalCriResponsavelReader,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
)


# CNPJ valid under the repo's ASCII-48 mod-11 routine; the contract's CNPJ check accepts it.
VALID_CNPJ = "11.222.333/0001-81"

# Fixed reference YEAR for the fixture; the member names embed it (``…_2025.csv``).
REF = date(2025, 6, 15)
YEAR = "2025"

# The verbatim header bytes as published by CVM — the ONLY oracle in this file we did not author.
PATH_FIXTURES = Path(__file__).parent.parent / "fixtures" / "inf_mensal_cri"

# The whole family. Introspection off the class attributes keeps this list from re-stating the 11
# members/contracts that the readers already declare.
ALL_READERS: tuple[type[IngestionReader], ...] = (
	InfMensalCriGeralReader,
	InfMensalCriAtivoPassivoReader,
	InfMensalCriClasseReader,
	InfMensalCriCreditosReader,
	InfMensalCriCarteiraReader,
	InfMensalCriCarteiraModificacaoReader,
	InfMensalCriDesembolsoReader,
	InfMensalCriFluxoCaixaReader,
	InfMensalCriDerivativosReader,
	InfMensalCriCedenteDevedorReader,
	InfMensalCriResponsavelReader,
)


def _member_name(cls: type[IngestionReader]) -> str:
	"""Return the archive member name for ``cls`` in the fixture reference year."""
	return f"{cls._MEMBER_STEM}_{YEAR}.csv"  # type: ignore[attr-defined]


def _value_for(cls: type[IngestionReader], str_col: str) -> str:
	"""Return a plausible source value for one column of ``cls``'s member."""
	if str_col == "CNPJ_Emissora":
		return VALID_CNPJ
	if str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
		return "2025-01-31"
	return "x"


def _member_csv(cls: type[IngestionReader]) -> str:
	"""Header + one valid row for ``cls``'s member."""
	list_cols = list(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	list_row = [_value_for(cls, c) for c in list_cols]
	return ";".join(list_cols) + "\n" + ";".join(list_row) + "\n"


def _all_members() -> dict[str, str]:
	"""Build the full 11-member fixture archive, one valid row each."""
	return {_member_name(cls): _member_csv(cls) for cls in ALL_READERS}


def _zip_bytes(dict_members: dict[str, str]) -> bytes:
	"""Build an in-memory ZIP holding each ``name → csv text`` member."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		for str_name, str_text in dict_members.items():
			cls_zip.writestr(str_name, str_text.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> list[str]:
	"""Patch the shared base reader's download_file boundary to drop ``payload``."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.securit.doc.inf_mensal_cri."
		"_base_inf_mensal_cri_reader.download_file",
		_fake_download,
	)
	return list_urls


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_contract_matches_the_published_header(cls: type[IngestionReader]) -> None:
	"""Each contract equals the header CVM actually publishes — names AND order.

	**The anti-tautology test.** Every other assertion in this file builds its fixture from
	``tuple_required``, so a wrong contract satisfies them all. Here the expected value comes from
	the verbatim header bytes CVM published, so a contract copied from a sibling dump (CRA/OTS), or
	drifted by a single character, fails immediately and offline.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	str_section = cls._MEMBER_STEM.removeprefix("inf_mensal_cri_")  # type: ignore[attr-defined]
	str_line = (
		(PATH_FIXTURES / f"inf_mensal_cri_{str_section}_header.csv")
		.read_text(encoding="utf-8")
		.strip()
	)

	assert cls._CONTRACT.tuple_required == tuple(str_line.split(";"))  # type: ignore[attr-defined]


def test_cri_asset_class_sections_are_not_the_cra_contracts() -> None:
	"""The asset-class-specific shared sections differ from CRA — guard against a future copy.

	CRI is real-estate; CRA is agro, so the sections that describe the receivables and the
	operation differ. Verified against the pinned headers: ``geral``, ``ativo_passivo``,
	``classe``, ``fluxo_caixa`` and ``derivativos`` all differ from their CRA namesakes.

	⚠️ Two shared sections are **genuinely column-identical** to CRA — ``desembolso`` (22 cols) and
	``cedente_devedor`` (7 cols) — because they are generic structures (payment-aging buckets, and
	the assignor/debtor tuple) with no asset-class content. The coincidence is the source's, proven
	by the pinned-header oracle in ``test_contract_matches_the_published_header``; it is **not** a
	copy error, so those two are deliberately excluded here.
	"""
	from filings_cvm._internal.config import contracts as cls_contracts

	tuple_asset_class = ("geral", "ativo_passivo", "classe", "fluxo_caixa", "derivativos")
	for str_section in tuple_asset_class:
		tuple_cri = getattr(cls_contracts, f"INF_MENSAL_CRI_{str_section.upper()}").tuple_required
		tuple_cra = getattr(cls_contracts, f"INF_MENSAL_CRA_{str_section.upper()}").tuple_required
		assert tuple_cri != tuple_cra, str_section


def test_cri_has_creditos_not_direitos_creditorios() -> None:
	"""CRI's receivables member is ``creditos``; CRA/OTS's ``direitos_creditorios`` has no twin.

	The single most likely copy artefact from a sibling dump, so it is asserted explicitly.
	"""
	from filings_cvm._internal.config import contracts as cls_contracts

	assert hasattr(cls_contracts, "INF_MENSAL_CRI_CREDITOS")
	assert not hasattr(cls_contracts, "INF_MENSAL_CRI_DIREITOS_CREDITORIOS")
	assert {c._MEMBER_STEM for c in ALL_READERS} == {  # type: ignore[attr-defined]
		f"inf_mensal_cri_{s}"
		for s in (
			"geral",
			"ativo_passivo",
			"classe",
			"creditos",
			"carteira",
			"carteira_modificacao",
			"desembolso",
			"fluxo_caixa",
			"derivativos",
			"cedente_devedor",
			"responsavel",
		)
	}


@pytest.mark.parametrize(
	"cls",
	(InfMensalCriCarteiraModificacaoReader, InfMensalCriResponsavelReader),
	ids=lambda c: c.__name__,
)
def test_header_only_member_reads_without_a_cnpj_error(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A structurally sparse member (header, no rows) must read clean, not raise ContractError.

	``carteira_modificacao`` and ``responsavel`` are header-only in the real 2025 file. Declaring
	``CNPJ_Emissora`` a CNPJ column would fail this legitimately empty member (nothing to check),
	so it is excluded from *their* ``tuple_cnpj_cols``, asserted against a header-only archive.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	assert cls._CONTRACT.tuple_cnpj_cols == ()  # type: ignore[attr-defined]
	list_cols = list(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	dict_members = _all_members()
	dict_members[_member_name(cls)] = ";".join(list_cols) + "\n"  # header, no data row
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls(date_ref=REF).read()

	assert len(df_) == 0
	assert list(df_.columns) == list(cls._CONTRACT.output_columns)  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_selects_its_own_member_with_all_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns exactly its member's columns from the shared 11-member archive.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = cls(date_ref=REF).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(cls._CONTRACT.output_columns)  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_coerces_its_date_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Every declared date column of a member becomes a pure ``date`` object.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = cls(date_ref=REF).read()

	for str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
		assert df_[str_col].iloc[0] == date(2025, 1, 31)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_requests_the_yearly_archive(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""``date_ref`` selects the YEAR: the dump is yearly-partitioned despite the monthly report.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch_download(monkeypatch, _zip_bytes(_all_members()))

	cls(date_ref=REF).read()

	assert list_urls == [
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_CRI/DADOS/inf_mensal_cri_2025.zip"
	]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_defaults_to_its_module_retry_policy(cls: type[IngestionReader]) -> None:
	"""Every reader declares the family's default retry policy, overridable per instance.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	assert cls._RETRY_POLICY is _DEFAULT_RETRY_POLICY  # type: ignore[attr-defined]
	assert cls(date_ref=REF)._retry_policy is _DEFAULT_RETRY_POLICY  # type: ignore[attr-defined]


def test_cedente_devedor_accepts_a_cpf_in_the_cnpj_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``cedente_devedor.CNPJ`` may hold a CPF — it must never be validated as a CNPJ.

	The column is a dirty free-text identifier: it holds a CPF when the cedente/devedor is a
	natural person. Declaring it a CNPJ column would make a valid file fail.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls = InfMensalCriCedenteDevedorReader
	list_cols = list(cls._CONTRACT.tuple_required)
	assert "CNPJ" in list_cols
	assert cls._CONTRACT.tuple_cnpj_cols == ("CNPJ_Emissora",)
	dict_members = _all_members()
	for str_dirty in ("04733158904", "0", ",", "027340230001553"):
		list_row = [VALID_CNPJ if c == "CNPJ_Emissora" else _value_for(cls, c) for c in list_cols]
		list_row[list_cols.index("CNPJ")] = str_dirty
		dict_members[_member_name(cls)] = ";".join(list_cols) + "\n" + ";".join(list_row) + "\n"
		_patch_download(monkeypatch, _zip_bytes(dict_members))

		df_ = cls(date_ref=REF).read()

		assert df_["CNPJ"].iloc[0] == str_dirty


def test_classe_does_not_coerce_indice_subordinacao_data_base(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``Indice_Subordinacao_Data_Base`` has "Data" in its name but is a number — keep it ``str``.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	assert "Indice_Subordinacao_Data_Base" in InfMensalCriClasseReader._CONTRACT.tuple_required
	assert "Indice_Subordinacao_Data_Base" not in InfMensalCriClasseReader._DATE_COLS

	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = InfMensalCriClasseReader(date_ref=REF).read()

	assert df_["Indice_Subordinacao_Data_Base"].iloc[0] == "x"


def test_geral_data_ltv_stays_text_and_blank_cnpj_columns_are_not_validated(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``geral.Data_LTV`` is ``varchar`` in CVM's META (100% empty) — keep it ``str``, not a date.

	Also guards the three always-blank ``CNPJ_*``-named columns: they must not be declared CNPJ
	columns, or a valid file would fail the day CVM fills them with free text.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls = InfMensalCriGeralReader
	assert "Data_LTV" in cls._CONTRACT.tuple_required
	assert "Data_LTV" not in cls._DATE_COLS
	assert cls._CONTRACT.tuple_cnpj_cols == ("CNPJ_Emissora",)

	list_cols = list(cls._CONTRACT.tuple_required)
	dict_members = _all_members()
	# A non-empty text value shows Data_LTV is not coerced; the default row fills it with the "x"
	# sentinel via _value_for, so leave it and only blank the three always-empty CNPJ columns.
	list_row = [_value_for(cls, c) for c in list_cols]
	for str_blank in ("CNPJ_Agente_Fiduciario", "CNPJ_Custodiante", "CNPJ_Agencia_Classificadora"):
		assert str_blank in list_cols
		list_row[list_cols.index(str_blank)] = ""
	dict_members[_member_name(cls)] = ";".join(list_cols) + "\n" + ";".join(list_row) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls(date_ref=REF).read()

	assert len(df_) == 1
	assert df_["Data_LTV"].iloc[0] == "x"  # left as source text, never coerced despite the name
