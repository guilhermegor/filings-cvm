#!/usr/bin/env python
"""Weekly, non-blocking contract-drift detector — META + real-header oracles.

CVM can change a dataset's schema *after* we have shipped its ``FileContract``. Nothing at PR
time can see that: the pinned-header fixtures (issue #96) prove a contract matched what CVM
published **the day it was written**, but only a job that fetches CVM again can notice a change
made since. This script fetches both oracles CVM publishes, compares them to every contract, and —
on any divergence — **opens (or updates) a single tracking issue**. It never fails the build: a
CVM outage and a real drift would be indistinguishable in a red check, and a red check must never
gate a PR or a release (issue #98). See ``.github/workflows/contract-drift.yaml``.

Two oracles, deliberately complementary:

* **Real artifact header** (:func:`real_header_drift`) — the columns a successful reader read
  returns, in **source order**, before the provenance tail. Authoritative for both the column
  *set* and its *order*, but only available for a period CVM has already published.
* **META** (:func:`meta_name_drift`) — the dataset's declared field names. META sits at a fixed
  URL that is always fetchable (even when the current period's artifact is not yet published), but
  CVM **truncates field names at exactly 50 characters** and does not preserve column order, so it
  is a name-*set* oracle compared on the 50-char prefix.

**Wiring is explicit, never derived.** Which readers a META describes is declared in
:data:`_META_MEMBERS`, and the contract of a reader that does not expose a ``_CONTRACT`` classvar
is declared in :data:`_UNEXPOSED_CONTRACTS`. Deriving either from names would be wrong: ``cad_fi``
and ``cad_fi_hist`` share a stem but are different datasets (the 19 ``cad_fi_hist_*`` readers
prefix-match *both*), and ``registro_fundo_classe``'s members are ``registro_fundo`` /
``registro_classe`` / ``registro_subclasse`` — no prefix relation at all. A structural test
(``tests/unit/test_check_contract_drift.py``) asserts the wiring stays complete, so a new reader
cannot be silently forgotten.

**Language.** Machine/maintainer-facing surface — English, like every other ``bin/`` script here.
"""

from __future__ import annotations

from datetime import date, timedelta
import inspect
import json
import os
import sys
from typing import TYPE_CHECKING, Any
import urllib.request

from filings_cvm._internal.config.contracts.balancete_fie import BALANCETE_FIE
from filings_cvm._internal.config.contracts.balanco_fie import BALANCO_FIE
from filings_cvm._internal.config.contracts.cad_emissor_cepac import CAD_EMISSOR_CEPAC
from filings_cvm._internal.config.contracts.cad_fi import CAD_FI
from filings_cvm._internal.config.contracts.cda_fif import CDA_FIF
from filings_cvm._internal.config.contracts.dfin_cra import DFIN_CRA
from filings_cvm._internal.config.contracts.dfin_cri import DFIN_CRI
from filings_cvm._internal.config.contracts.dfin_fii import DFIN_FII
from filings_cvm._internal.config.contracts.inf_quadrimestral_fip import INF_QUADRIMESTRAL_FIP
from filings_cvm._internal.config.contracts.inf_trimestral_fip import INF_TRIMESTRAL_FIP
from filings_cvm._internal.config.contracts.informe_diario_fif import INFORME_DIARIO_FIF
from filings_cvm._internal.config.contracts.lamina_carteira_fif import LAMINA_CARTEIRA_FIF
from filings_cvm._internal.config.contracts.lamina_fif import LAMINA_FIF
from filings_cvm._internal.config.contracts.medidas_mes_fie import MEDIDAS_MES_FIE
from filings_cvm._internal.config.contracts.registro_classe import REGISTRO_CLASSE
from filings_cvm._internal.config.contracts.registro_fundo import REGISTRO_FUNDO
from filings_cvm._internal.config.contracts.registro_subclasse import REGISTRO_SUBCLASSE
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
import filings_cvm.ingestion as ingestion
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


if TYPE_CHECKING:
	import pandas as pd


# GitHub API host — host-only so no fetchable URL literal trips the check-urls hook; paths are
# concatenated. Same convention as bin/reconcile_merged_prs.py.
_GH_API = "https://api.github.com"

# The single tracking issue is found again each run by this label plus a hidden body marker, so
# the job updates one issue instead of opening a new one every week.
_ISSUE_LABEL = "contract-drift"
_ISSUE_MARKER = "<!-- contract-drift-bot -->"
_ISSUE_TITLE = "Deriva de contrato detectada (META/header × contracts)"

# CVM truncates every META field name at exactly 50 characters (the real header carries names up
# to 60). Proven 8/8 on INF_MENSAL_CRA. META names are compared on this prefix, never repaired.
_META_NAME_MAX_LEN = 50

# Contracts of the readers that hold their contract inline instead of a ``_CONTRACT`` classvar
# (the single-member flat/registro/snapshot readers). Declared here so the drift job can reach
# every reader's contract; the multi-member readers expose ``_CONTRACT`` and are read from the
# class directly. Keyed by class name, resolved against ``ingestion.__all__``.
_UNEXPOSED_CONTRACTS: dict[str, FileContract] = {
	"BalanceteFieReader": BALANCETE_FIE,
	"BalancoFieReader": BALANCO_FIE,
	"CadastroEmissorCepacReader": CAD_EMISSOR_CEPAC,
	"CadastroFiReader": CAD_FI,
	"CdaReader": CDA_FIF,
	"DfinCraReader": DFIN_CRA,
	"DfinCriReader": DFIN_CRI,
	"DfinFiiReader": DFIN_FII,
	"InfQuadrimestralFipReader": INF_QUADRIMESTRAL_FIP,
	"InfTrimestralFipReader": INF_TRIMESTRAL_FIP,
	"InformeDiarioReader": INFORME_DIARIO_FIF,
	"LaminaCarteiraReader": LAMINA_CARTEIRA_FIF,
	"LaminaReader": LAMINA_FIF,
	"MedidasMesFieReader": MEDIDAS_MES_FIE,
	"RegistroClasseReader": REGISTRO_CLASSE,
	"RegistroFundoReader": REGISTRO_FUNDO,
	"RegistroSubclasseReader": REGISTRO_SUBCLASSE,
}

# Which readers each META dataset describes. Explicit because the mapping is not derivable from
# names — see the module docstring (the cad_fi / cad_fi_hist / registro traps). Keyed by class
# name; both sides resolve against ``ingestion.__all__``.
_META_MEMBERS: dict[str, tuple[str, ...]] = {
	"MetaAgenteAutonReader": ("AgenteAutonPfReader", "AgenteAutonPjReader"),
	"MetaAgenteFiducReader": ("AgenteFiducPfReader", "AgenteFiducPjReader"),
	"MetaAuditorReader": ("AuditorPfReader", "AuditorPjReader"),
	"MetaBalanceteFieReader": ("BalanceteFieReader",),
	"MetaBalancoFieReader": ("BalancoFieReader",),
	"MetaCadEmissorCepacReader": ("CadastroEmissorCepacReader",),
	"MetaCadFiHistReader": (
		"CadastroFiHistAdminReader",
		"CadastroFiHistAuditorReader",
		"CadastroFiHistClasseReader",
		"CadastroFiHistCondomReader",
		"CadastroFiHistControladorReader",
		"CadastroFiHistCustodianteReader",
		"CadastroFiHistDenomComercReader",
		"CadastroFiHistDenomSocialReader",
		"CadastroFiHistDiretorRespReader",
		"CadastroFiHistExclusivoReader",
		"CadastroFiHistExercSocialReader",
		"CadastroFiHistFicReader",
		"CadastroFiHistGestorReader",
		"CadastroFiHistPublicoAlvoReader",
		"CadastroFiHistRentabReader",
		"CadastroFiHistSitReader",
		"CadastroFiHistTaxaAdmReader",
		"CadastroFiHistTaxaPerfmReader",
		"CadastroFiHistTribLprazoReader",
	),
	"MetaCadastroFiReader": ("CadastroFiReader",),
	"MetaCdaReader": ("CdaReader",),
	"MetaDfinCraReader": ("DfinCraReader",),
	"MetaDfinCriReader": ("DfinCriReader",),
	"MetaDfinFiiReader": ("DfinFiiReader",),
	"MetaInfAnualFiiReader": (
		"InfAnualFiiAtivoAdquiridoReader",
		"InfAnualFiiAtivoTransacaoReader",
		"InfAnualFiiAtivoValorContabilReader",
		"InfAnualFiiComplementoReader",
		"InfAnualFiiDiretorResponsavelReader",
		"InfAnualFiiDistribuicaoCotistasReader",
		"InfAnualFiiExperienciaProfissionalReader",
		"InfAnualFiiGeralReader",
		"InfAnualFiiPrestadorServicoReader",
		"InfAnualFiiProcessoReader",
		"InfAnualFiiProcessoSemelhanteReader",
		"InfAnualFiiRepresentanteCotistaReader",
	),
	"MetaInfMensalCraReader": (
		"InfMensalCraAtivoPassivoReader",
		"InfMensalCraCedenteDevedorReader",
		"InfMensalCraClasseReader",
		"InfMensalCraDerivativosReader",
		"InfMensalCraDesembolsoReader",
		"InfMensalCraDireitosCreditoriosReader",
		"InfMensalCraFluxoCaixaReader",
		"InfMensalCraGeralReader",
	),
	"MetaInfMensalCriReader": (
		"InfMensalCriGeralReader",
		"InfMensalCriAtivoPassivoReader",
		"InfMensalCriClasseReader",
		"InfMensalCriCreditosReader",
		"InfMensalCriCarteiraReader",
		"InfMensalCriCarteiraModificacaoReader",
		"InfMensalCriDesembolsoReader",
		"InfMensalCriFluxoCaixaReader",
		"InfMensalCriDerivativosReader",
		"InfMensalCriCedenteDevedorReader",
		"InfMensalCriResponsavelReader",
	),
	"MetaInfMensalFiagroReader": ("InfMensalFiagroReader", "InfMensalFiagroSubclasseReader"),
	"MetaInfMensalFidcReader": (
		"InfMensalFidcTabIReader",
		"InfMensalFidcTabIIReader",
		"InfMensalFidcTabIIIReader",
		"InfMensalFidcTabIVReader",
		"InfMensalFidcTabVReader",
		"InfMensalFidcTabVIReader",
		"InfMensalFidcTabVIIReader",
		"InfMensalFidcTabIXReader",
		"InfMensalFidcTabXReader",
		"InfMensalFidcTabX1Reader",
		"InfMensalFidcTabX11Reader",
		"InfMensalFidcTabX2Reader",
		"InfMensalFidcTabX3Reader",
		"InfMensalFidcTabX4Reader",
		"InfMensalFidcTabX5Reader",
		"InfMensalFidcTabX6Reader",
		"InfMensalFidcTabX7Reader",
	),
	"MetaInfMensalFiiReader": (
		"InfMensalFiiAtivoPassivoReader",
		"InfMensalFiiComplementoReader",
		"InfMensalFiiGeralReader",
	),
	"MetaInfMensalOtsReader": (
		"InfMensalOtsAtivoPassivoReader",
		"InfMensalOtsCedenteDevedorReader",
		"InfMensalOtsClasseReader",
		"InfMensalOtsDerivativosReader",
		"InfMensalOtsDesembolsoReader",
		"InfMensalOtsDireitosCreditoriosReader",
		"InfMensalOtsFluxoCaixaReader",
		"InfMensalOtsGeralReader",
	),
	"MetaInfQuadrimestralFipReader": ("InfQuadrimestralFipReader",),
	"MetaInfTrimestralFiiReader": (
		"InfTrimestralFiiAlienacaoImovelReader",
		"InfTrimestralFiiAlienacaoTerrenoReader",
		"InfTrimestralFiiAquisicaoImovelReader",
		"InfTrimestralFiiAquisicaoTerrenoReader",
		"InfTrimestralFiiAtivoGarantiaRentabilidadeReader",
		"InfTrimestralFiiAtivoReader",
		"InfTrimestralFiiComplementoReader",
		"InfTrimestralFiiDireitoReader",
		"InfTrimestralFiiGeralReader",
		"InfTrimestralFiiImovelDesempenhoReader",
		"InfTrimestralFiiImovelReader",
		"InfTrimestralFiiImovelRendaAcabadoContratoReader",
		"InfTrimestralFiiImovelRendaAcabadoInquilinoReader",
		"InfTrimestralFiiRentabilidadeEfetivaReader",
		"InfTrimestralFiiResultadoContabilFinanceiroReader",
		"InfTrimestralFiiTerrenoReader",
	),
	"MetaInfTrimestralFipReader": ("InfTrimestralFipReader",),
	"MetaInformeDiarioReader": ("InformeDiarioReader",),
	"MetaInvnrRepresReader": ("InvnrRepresPfReader", "InvnrRepresPjReader"),
	"MetaLaminaReader": ("LaminaReader", "LaminaCarteiraReader"),
	"MetaMedidasMesFieReader": ("MedidasMesFieReader",),
	"MetaRegistroReader": (
		"RegistroFundoReader",
		"RegistroClasseReader",
		"RegistroSubclasseReader",
	),
}

# Datasets whose columns/members we cover **partially, on purpose** — so a source column or META
# field the contract does not list is *expected*, not drift. The extra-column direction of both
# oracles is suppressed for these (a **required** column gone from the source is still reported).
# Keyed by META reader name (the dataset's identity). ``tuple_required`` means "must contain at
# least these", not "exactly these": a subset contract requires only the key columns, and a
# dataset's META describes every member — including ones we have not implemented yet. This set is
# grounded in the first live run (issue #115): every dataset here produced only expected
# extra-column noise, never a required-column loss.
_PARTIAL_DATASETS: dict[str, str] = {
	# CdaReader requires only the four key columns of a ~60-column file — a deliberate subset.
	"MetaCdaReader": "subset contract — requires only the key columns of a ~60-column file",
	# The Lamina META describes the whole dataset, including the rentab members not implemented
	# yet, whose fields therefore show as uncovered until those readers land.
	"MetaLaminaReader": "partial member coverage — rentab_ano/rentab_mes not implemented yet",
}

# Reverse map: reader class name -> its dataset's META reader name. Lets the per-member header
# check learn whether its dataset is partial. Derived from _META_MEMBERS so the two cannot drift.
_READER_TO_META: dict[str, str] = {
	str_reader: str_meta
	for str_meta, tuple_readers in _META_MEMBERS.items()
	for str_reader in tuple_readers
}


# ---------------------------------------------------------------------------------------------
# Pure oracles (no network) — the two comparisons, unit-tested exhaustively.
# ---------------------------------------------------------------------------------------------


def real_header_drift(
	str_label: str,
	tuple_contract: tuple[str, ...],
	tuple_real: tuple[str, ...],
	bool_report_extra: bool = True,
) -> list[str]:
	"""Compare a contract's columns against the real artifact header.

	The real header is what a successful reader read returns (its source columns, in source order,
	before the provenance columns). Catches a column CVM added, removed, or reordered.

	Parameters
	----------
	str_label : str
		Human-readable dataset/member label, prefixed onto each problem for the issue body.
	tuple_contract : tuple of str
		The contract's ``tuple_required`` — the columns (and order) we recorded.
	tuple_real : tuple of str
		The columns CVM's artifact actually carries now, in source order.
	bool_report_extra : bool, optional
		Whether to report a real-header column the contract does not list. ``True`` (default) for a
		**full-column** contract (an extra column means CVM added one — real signal). ``False`` for
		a **partial-coverage** dataset, whose contract deliberately lists only a subset of the
		header (see :data:`_PARTIAL_DATASETS`), so an unlisted column is expected, not drift. A
		**required** column gone from the header is always reported, either way.

	Returns
	-------
	list of str
		One message per drift found; empty when the header matches the contract (subject to
		``bool_report_extra``).
	"""
	list_problems: list[str] = []
	set_contract, set_real = set(tuple_contract), set(tuple_real)
	for str_col in tuple_contract:
		if str_col not in set_real:
			list_problems.append(
				f"{str_label}: contract column {str_col!r} is gone from the real header"
			)
	if bool_report_extra:
		for str_col in tuple_real:
			if str_col not in set_contract:
				list_problems.append(
					f"{str_label}: real header carries {str_col!r}, absent from the contract"
				)
	if set_contract == set_real and tuple_contract != tuple_real:
		list_problems.append(
			f"{str_label}: column order differs between the contract and the real header"
		)
	return list_problems


def meta_name_drift(
	str_label: str,
	tuple_contract: tuple[str, ...],
	frozenset_meta: frozenset[str],
	bool_report_extra: bool = True,
) -> list[str]:
	"""Compare a contract's columns against META field names, truncation-aware.

	CVM truncates META field names at 50 characters, so a contract column is matched on its 50-char
	prefix — never by "repairing" the META name into a string CVM never actually published.
	Order is **not** compared (META does not preserve it); this is a name-set oracle only.

	Parameters
	----------
	str_label : str
		Human-readable dataset label, prefixed onto each problem for the issue body.
	tuple_contract : tuple of str
		The dataset's contract columns (across all its members, deduplicated).
	frozenset_meta : frozenset of str
		The field names CVM's META declares now (already 50-char truncated, verbatim).
	bool_report_extra : bool, optional
		Whether to report a META field no contract column covers. ``True`` (default) for a dataset
		we cover in full. ``False`` for a **partial-coverage** dataset (see
		:data:`_PARTIAL_DATASETS`) — one whose contract is a deliberate subset (only the key
		columns) or whose META describes sibling members we do not implement yet — so an uncovered
		field is expected, not drift. A contract column absent from META is always reported.

	Returns
	-------
	list of str
		One message per drift found; empty when META and the contract columns reconcile (subject to
		``bool_report_extra``).
	"""
	list_problems: list[str] = []
	set_contract_prefixes = {str_col[:_META_NAME_MAX_LEN] for str_col in tuple_contract}
	if bool_report_extra:
		for str_field in sorted(frozenset_meta):
			if str_field not in set_contract_prefixes:
				list_problems.append(
					f"{str_label}: META declares field {str_field!r}, matched by no "
					f"contract column (CVM added or renamed a field?)"
				)
	for str_col in tuple_contract:
		if str_col[:_META_NAME_MAX_LEN] not in frozenset_meta:
			list_problems.append(
				f"{str_label}: contract column {str_col!r} is not in META "
				f"(CVM removed or renamed a field?)"
			)
	return list_problems


# ---------------------------------------------------------------------------------------------
# Registry access (no network) — resolve reader classes and their contracts.
# ---------------------------------------------------------------------------------------------


def contract_of(cls_reader: type[IngestionReader]) -> FileContract:
	"""Return the contract a reader enforces, whether classvar-exposed or inline-declared.

	Parameters
	----------
	cls_reader : type[IngestionReader]
		The reader class.

	Returns
	-------
	FileContract
		Its ``_CONTRACT`` classvar when present, else its entry in :data:`_UNEXPOSED_CONTRACTS`.
	"""
	cls_contract = getattr(cls_reader, "_CONTRACT", None)
	if cls_contract is not None:
		return cls_contract
	return _UNEXPOSED_CONTRACTS[cls_reader.__name__]


def _resolve(str_name: str) -> type[IngestionReader]:
	"""Resolve a reader class name against the public ingestion API."""
	return getattr(ingestion, str_name)


def real_readers() -> tuple[type[IngestionReader], ...]:
	"""Every public non-META reader, discovered from ``ingestion.__all__``."""
	return tuple(
		cls
		for cls in (getattr(ingestion, str_name) for str_name in ingestion.__all__)
		if inspect.isclass(cls)
		and issubclass(cls, IngestionReader)
		and not issubclass(cls, BaseMetaReader)
	)


def real_columns(df_read: pd.DataFrame) -> tuple[str, ...]:
	"""Return the source columns of a read frame — everything before the provenance tail.

	Parameters
	----------
	df_read : pandas.DataFrame
		A frame returned by a reader's ``read``; its last columns are the provenance columns.

	Returns
	-------
	tuple of str
		The source columns, in source order.
	"""
	int_n = len(FileContract.PROVENANCE_COLUMNS)
	return tuple(df_read.columns[:-int_n])


# ---------------------------------------------------------------------------------------------
# Online checks — one read per member (network); tolerant of an unpublished period.
# ---------------------------------------------------------------------------------------------

# Reference dates probed when a reader needs one, newest first: this month, the last few months
# (covers month-partitioned dumps whose current file is not yet published), then the last few
# years (covers year-partitioned dumps, whose past year is complete).
_PROBE_OFFSETS_DAYS = (0, 31, 62, 93, 365, 730, 1095)

# This is a best-effort weekly probe, so readers are built to **fail fast** instead of using the
# patient production retry policy. Probing an unpublished period is an EXPECTED 404, not a
# transient error, and burning the default ~24 s of backoff on every such probe (across ~110
# readers × several probe dates) is what made the first run take ~40 min. One attempt: a 404 (or a
# real blip) skips the dataset this week, and next week's run catches anything that was transient.
_DRIFT_RETRY_POLICY: RetryPolicy = RetryPolicy(int_max_attempts=1)


def _probe_dates() -> tuple[date, ...]:
	"""Candidate reference dates to try, newest first."""
	dt_today = date.today()
	return tuple(dt_today - timedelta(days=int_days) for int_days in _PROBE_OFFSETS_DAYS)


def check_real_header(cls_reader: type[IngestionReader], int_timeout_s: int = 60) -> list[str]:
	"""Fetch a reader's real header and compare it to the reader's contract.

	Tries recent reference dates until one is published. A :class:`ContractError` means CVM changed
	a required column (drift); a download failure means the period is not published yet (tolerated,
	an older date is tried). If no probed period is available at all, the dataset is skipped — an
	unpublished artifact is not drift.

	Parameters
	----------
	cls_reader : type[IngestionReader]
		The reader class to probe.
	int_timeout_s : int, optional
		Socket timeout forwarded to ``read``, by default 60.

	Returns
	-------
	list of str
		Drift messages (empty when the header matches or the artifact is unavailable).
	"""
	cls_contract = contract_of(cls_reader)
	bool_dated = "date_ref" in inspect.signature(cls_reader.__init__).parameters
	list_dates: tuple[date | None, ...] = _probe_dates() if bool_dated else (None,)

	for date_ref in list_dates:
		cls_instance = (
			cls_reader(date_ref=date_ref, retry_policy=_DRIFT_RETRY_POLICY)
			if bool_dated
			else cls_reader(retry_policy=_DRIFT_RETRY_POLICY)
		)
		try:
			df_read = cls_instance.read(int_timeout_s=int_timeout_s)
		except ContractError as cls_exc:
			return [f"{cls_contract.str_name}: read failed its contract — {cls_exc}"]
		except OSError:
			continue  # period not published (or transient) — try an older one
		bool_report_extra = _READER_TO_META.get(cls_reader.__name__) not in _PARTIAL_DATASETS
		return real_header_drift(
			cls_contract.str_name,
			cls_contract.tuple_required,
			real_columns(df_read),
			bool_report_extra=bool_report_extra,
		)
	return []  # no probed period available — not drift


def check_meta(
	cls_meta: type[BaseMetaReader],
	tuple_members: tuple[type[IngestionReader], ...],
	int_timeout_s: int = 60,
) -> list[str]:
	"""Fetch a dataset's META and reconcile its field names with its members' contract columns.

	The comparison is at the **dataset** level: the META field set against the union of every
	member contract's columns (deduplicated, order preserved). Per-member column moves are caught
	by :func:`check_real_header`; this always-available oracle catches a field CVM added to or
	removed from the declared spec.

	Parameters
	----------
	cls_meta : type[BaseMetaReader]
		The META reader for the dataset.
	tuple_members : tuple of type[IngestionReader]
		The dataset's member readers, whose contracts define the expected columns.
	int_timeout_s : int, optional
		Socket timeout forwarded to ``read``, by default 60.

	Returns
	-------
	list of str
		Drift messages (empty when META reconciles, or when META is unavailable).
	"""
	str_label = cls_meta.__name__.removeprefix("Meta").removesuffix("Reader")
	try:
		df_meta = cls_meta(retry_policy=_DRIFT_RETRY_POLICY).read(int_timeout_s=int_timeout_s)
	except OSError:
		return []  # META unavailable (transient) — not drift
	frozenset_fields = frozenset(df_meta["field"].astype(str))

	list_cols: list[str] = []
	set_seen: set[str] = set()
	for cls_member in tuple_members:
		for str_col in contract_of(cls_member).tuple_required:
			if str_col not in set_seen:
				set_seen.add(str_col)
				list_cols.append(str_col)
	bool_report_extra = cls_meta.__name__ not in _PARTIAL_DATASETS
	return meta_name_drift(
		str_label, tuple(list_cols), frozenset_fields, bool_report_extra=bool_report_extra
	)


def collect_drift(int_timeout_s: int = 60) -> list[str]:
	"""Run both oracles over every dataset and return every drift message found.

	One read per member re-downloads a shared multi-member archive once per member; acceptable for
	a weekly, non-blocking job. A single dataset's failure is caught and skipped so one bad dataset
	never sinks the whole sweep.

	Parameters
	----------
	int_timeout_s : int, optional
		Socket timeout forwarded to every read, by default 60.

	Returns
	-------
	list of str
		Every drift message, across every dataset.
	"""
	list_problems: list[str] = []
	for str_meta, tuple_names in _META_MEMBERS.items():
		tuple_members = tuple(_resolve(str_name) for str_name in tuple_names)
		try:
			list_problems.extend(check_meta(_resolve(str_meta), tuple_members, int_timeout_s))
		except Exception as cls_exc:  # noqa: BLE001 — one dataset must never sink the sweep
			print(f"META check errored for {str_meta}: {cls_exc}", file=sys.stderr)
		for cls_member in tuple_members:
			try:
				list_problems.extend(check_real_header(cls_member, int_timeout_s))
			except Exception as cls_exc:  # noqa: BLE001 — one member must never sink the sweep
				print(
					f"header check errored for {cls_member.__name__}: {cls_exc}", file=sys.stderr
				)  # noqa: E501
	return list_problems


# ---------------------------------------------------------------------------------------------
# Issue upsert (network) — one tracking issue, found again by label + marker.
# ---------------------------------------------------------------------------------------------


def build_issue_body(list_problems: list[str]) -> str:
	"""Render the drift messages into the tracking issue's body (with the dedupe marker).

	Parameters
	----------
	list_problems : list of str
		The drift messages.

	Returns
	-------
	str
		Markdown body carrying the hidden marker used to find this issue again.
	"""
	str_lines = "\n".join(f"- {str_problem}" for str_problem in list_problems)
	return (
		f"{_ISSUE_MARKER}\n\n"
		f"O job semanal de deriva de contrato encontrou **{len(list_problems)}** divergência(s) "
		f"entre o que a CVM publica hoje (META + header real) e os `FileContract` do repo.\n\n"
		f"{str_lines}\n\n"
		f"Cada item é META (nome, ciente do truncamento em 50 chars) ou header real (nome + "
		f"ordem) contra `tuple_required`. Corrija o contrato afetado (contracts pinados ao "
		f"header real, issue #96) e feche esta issue — o job a reabre se a deriva persistir.\n"
	)


def _api(str_method: str, str_url: str, dict_body: dict | None = None) -> Any:  # noqa: ANN401
	"""Call the GitHub API with the workflow token and decode the JSON reply.

	Parameters
	----------
	str_method : str
		HTTP method.
	str_url : str
		Absolute API URL.
	dict_body : dict, optional
		JSON payload, when the method takes one.

	Returns
	-------
	Any
		The decoded JSON (an object or an array, per the endpoint).
	"""
	bytes_body = None if dict_body is None else json.dumps(dict_body).encode()
	cls_request = urllib.request.Request(str_url, data=bytes_body, method=str_method)  # noqa: S310
	cls_request.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
	cls_request.add_header("Accept", "application/vnd.github+json")
	cls_request.add_header("Content-Type", "application/json")
	with urllib.request.urlopen(cls_request) as cls_response:  # noqa: S310
		return json.loads(cls_response.read() or "null")


def find_open_drift_issue(list_issues: list[dict]) -> int | None:
	"""Return the number of the existing open drift issue, if any.

	Parameters
	----------
	list_issues : list of dict
		Open issues carrying the drift label, each ``{"number": int, "body": str, ...}``.

	Returns
	-------
	int or None
		The first issue whose body carries the marker, or ``None``.
	"""
	for dict_issue in list_issues:
		if _ISSUE_MARKER in (dict_issue.get("body") or ""):
			return dict_issue["number"]
	return None


def upsert_issue(str_api: str, list_problems: list[str]) -> None:
	"""Open the tracking issue, or update it in place if it already exists.

	Parameters
	----------
	str_api : str
		The ``.../repos/{owner}/{name}`` API base.
	list_problems : list of str
		The drift messages to report.
	"""
	str_body = build_issue_body(list_problems)
	list_open = _api("GET", f"{str_api}/issues?state=open&labels={_ISSUE_LABEL}&per_page=100")
	int_existing = find_open_drift_issue(list_open)
	if int_existing is not None:
		_api("PATCH", f"{str_api}/issues/{int_existing}", {"body": str_body})
		print(f"updated drift issue #{int_existing}", file=sys.stderr)
		return
	_api(
		"POST",
		f"{str_api}/issues",
		{"title": _ISSUE_TITLE, "body": str_body, "labels": [_ISSUE_LABEL]},
	)
	print("opened a new drift issue", file=sys.stderr)


def main() -> int:
	"""Run the sweep; open/update the tracking issue on drift. Always exits 0 (non-blocking).

	Returns
	-------
	int
		Always ``0`` — drift is reported as an issue, never as a failed check.
	"""
	list_problems = collect_drift()
	if not list_problems:
		print("no contract drift detected")
		return 0

	print(f"contract drift detected: {len(list_problems)} problem(s)")
	for str_problem in list_problems:
		print(f"  - {str_problem}")

	str_repo = os.environ.get("GITHUB_REPOSITORY")
	if str_repo:
		upsert_issue(f"{_GH_API}/repos/{str_repo}", list_problems)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
