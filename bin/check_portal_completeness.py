#!/usr/bin/env python
"""Weekly, non-blocking portal-completeness detector — issue #111.

CVM's open-data portal publishes datasets we have not implemented yet, and it grows over time. This
job enumerates every published dataset, subtracts the ones we cover, and opens — or updates — a
single tracking issue listing the gap. It automates the manual portal survey (#41) and mirrors the
shape of the contract-drift job (#98): scheduled, deterministic, **never fails CI** — a divergence
is reported as an issue, not a red check.

**Enumeration is deterministic, via the CKAN API — never HTML scraping.** CVM's portal is a CKAN
instance, so ``/api/3/action/package_list`` returns every dataset (package) slug (54 today). That
is stable and machine-readable; scraping the HTML directory index is not.

**Coverage is declared, never derived** (:data:`_IMPLEMENTED_PACKAGES`). A CKAN slug does not map
cleanly to our readers: ``fi-cad`` is one package but three reader families (cadastro, registro,
cad_fi_hist), and CKAN's granularity differs between ``*-cad`` (two path levels) and ``*-doc-*``
(three). Deriving "implemented?" from reader names or URLs is the same failure class the drift job
avoids (``cad_fi`` vs ``cad_fi_hist``). So the packages we cover are listed explicitly here and
kept in step with the ``CLAUDE.md`` catalog; a structural test checks the slugs are well-formed.

**Detection only.** Reporting a gap is cheap and safe pre-1.0; generating a reader is not — a
generated reader touches a ``FileContract`` pinned to the real header, the surface where "tests
green" proves nothing (``pin-contracts-to-a-source-published-oracle``), and ``pr_gate`` never
auto-merges ``src/``. LLM code-gen + auto-PR is a later, human-reviewed, post-1.0 phase, out of
scope here.

**Language.** Machine/maintainer-facing surface — English, like every other ``bin/`` script here.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any
import urllib.request


# GitHub API host — host-only so no fetchable URL literal trips the check-urls hook; paths are
# concatenated. Same convention as bin/check_contract_drift.py.
_GH_API = "https://api.github.com"

# CVM's CKAN dataset index. Host-only base + a concatenated path, for the same reason.
_CKAN_HOST = "https://dados.cvm.gov.br"
_CKAN_PACKAGE_LIST_PATH = "/api/3/action/package_list"

# The single tracking issue is found again each run by this label plus a hidden body marker.
_ISSUE_LABEL = "portal-completeness"
_ISSUE_MARKER = "<!-- portal-completeness-bot -->"
_ISSUE_TITLE = "Datasets do portal da CVM ainda não implementados"

# The CKAN package slugs this library already ingests. **Declared, never derived** — see the module
# docstring. Keep in step with the CLAUDE.md catalog: implementing a portal dataset means adding
# its slug here so it drops off the gap. 21 today.
_IMPLEMENTED_PACKAGES: frozenset[str] = frozenset(
	{
		"emissor_cepac-cad",  # CadastroEmissorCepacReader
		"fi-cad",  # CadastroFiReader + Registro{Fundo,Classe,Subclasse} + CadastroFiHist*
		"fi-doc-cda",  # CdaReader
		"fi-doc-inf_diario",  # InformeDiarioReader
		"fi-doc-lamina",  # LaminaReader + LaminaCarteiraReader (rentab members still pending)
		"fiagro-doc-inf_mensal",  # InfMensalFiagro*
		"fidc-doc-inf_mensal",  # InfMensalFidcTab*
		"fie-doc-balancete",  # BalanceteFieReader
		"fie-doc-balanco",  # BalancoFieReader
		"fie-medidas",  # MedidasMesFieReader
		"fii-doc-dfin",  # DfinFiiReader
		"fii-doc-inf_anual",  # InfAnualFii*
		"fii-doc-inf_mensal",  # InfMensalFii*
		"fii-doc-inf_trimestral",  # InfTrimestralFii*
		"fip-doc-inf_quadrimestral",  # InfQuadrimestralFipReader
		"fip-doc-inf_trimestral",  # InfTrimestralFipReader
		"securit-doc-dfin_cra",  # DfinCraReader
		"securit-doc-dfin_cri",  # DfinCriReader
		"securit-doc-inf_mensal_cra",  # InfMensalCra*
		"securit-doc-inf_mensal_cri",  # InfMensalCri*
		"securit-doc-inf_mensal_ots",  # InfMensalOts*
	}
)


# ---------------------------------------------------------------------------------------------
# Pure logic (no network) — the gap, unit-tested.
# ---------------------------------------------------------------------------------------------


def missing_packages(
	frozenset_published: frozenset[str], frozenset_implemented: frozenset[str]
) -> list[str]:
	"""Return the published packages we have not implemented, sorted.

	Parameters
	----------
	frozenset_published : frozenset of str
		Every dataset slug the portal publishes now.
	frozenset_implemented : frozenset of str
		The slugs this library already ingests.

	Returns
	-------
	list of str
		``published − implemented``, sorted — the tracking backlog.
	"""
	return sorted(frozenset_published - frozenset_implemented)


def build_issue_body(list_missing: list[str], int_published: int) -> str:
	"""Render the missing packages into the tracking issue's body (with the dedupe marker).

	Parameters
	----------
	list_missing : list of str
		The unimplemented package slugs.
	int_published : int
		Total packages the portal publishes (for context in the body).

	Returns
	-------
	str
		Markdown body carrying the hidden marker used to find this issue again.
	"""
	str_lines = "\n".join(f"- `{str_slug}`" for str_slug in list_missing)
	int_implemented = int_published - len(list_missing)
	return (
		f"{_ISSUE_MARKER}\n\n"
		f"O portal de dados abertos da CVM publica **{int_published}** datasets; o pacote "
		f"implementa **{int_implemented}**. Faltam **{len(list_missing)}** (survey do #41):\n\n"
		f"{str_lines}\n\n"
		f"Enumerado via CKAN (`/api/3/action/package_list`). Ao implementar um dataset, adicione "
		f"o seu slug a `_IMPLEMENTED_PACKAGES` em `bin/check_portal_completeness.py` — ele sai da "
		f"lista. O job atualiza esta issue toda semana; só detecção, sem geração de código.\n"
	)


# ---------------------------------------------------------------------------------------------
# Network — fetch the portal index and upsert the tracking issue.
# ---------------------------------------------------------------------------------------------


def fetch_published(int_timeout_s: int = 60) -> frozenset[str]:
	"""Fetch every dataset slug the CVM portal publishes now, via the CKAN API.

	Parameters
	----------
	int_timeout_s : int, optional
		Socket timeout in seconds, by default 60.

	Returns
	-------
	frozenset of str
		The package slugs.

	Raises
	------
	OSError
		If the request fails (network error, non-2xx status, timeout).
	"""
	cls_request = urllib.request.Request(  # noqa: S310
		f"{_CKAN_HOST}{_CKAN_PACKAGE_LIST_PATH}",
		headers={"User-Agent": "filings-cvm portal-completeness bot"},
	)
	with urllib.request.urlopen(cls_request, timeout=int_timeout_s) as cls_response:  # noqa: S310
		dict_payload = json.loads(cls_response.read())
	return frozenset(dict_payload["result"])


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


def find_open_tracking_issue(list_issues: list[dict]) -> int | None:
	"""Return the number of the existing open tracking issue, if any.

	Parameters
	----------
	list_issues : list of dict
		Open issues carrying the label, each ``{"number": int, "body": str, ...}``.

	Returns
	-------
	int or None
		The first issue whose body carries the marker, or ``None``.
	"""
	for dict_issue in list_issues:
		if _ISSUE_MARKER in (dict_issue.get("body") or ""):
			return dict_issue["number"]
	return None


def upsert_issue(str_api: str, list_missing: list[str], int_published: int) -> None:
	"""Open the tracking issue, or update it in place if it already exists.

	Parameters
	----------
	str_api : str
		The ``.../repos/{owner}/{name}`` API base.
	list_missing : list of str
		The unimplemented package slugs.
	int_published : int
		Total packages the portal publishes.
	"""
	str_body = build_issue_body(list_missing, int_published)
	list_open = _api("GET", f"{str_api}/issues?state=open&labels={_ISSUE_LABEL}&per_page=100")
	int_existing = find_open_tracking_issue(list_open)
	if int_existing is not None:
		_api("PATCH", f"{str_api}/issues/{int_existing}", {"body": str_body})
		print(f"updated tracking issue #{int_existing}", file=sys.stderr)
		return
	_api(
		"POST",
		f"{str_api}/issues",
		{"title": _ISSUE_TITLE, "body": str_body, "labels": [_ISSUE_LABEL]},
	)
	print("opened a new tracking issue", file=sys.stderr)


def main() -> int:
	"""Enumerate the portal, report the gap as one issue. Always exits 0 (non-blocking).

	Returns
	-------
	int
		Always ``0`` — the gap is reported as an issue, never as a failed check. A portal outage is
		tolerated (logged, no issue), so a portal outage never opens a spurious "all missing".
	"""
	try:
		frozenset_published = fetch_published()
	except OSError as cls_exc:
		print(f"could not reach the CVM portal, skipping this run: {cls_exc}", file=sys.stderr)
		return 0

	list_missing = missing_packages(frozenset_published, _IMPLEMENTED_PACKAGES)
	if not list_missing:
		print("portal fully implemented — no gap")
		return 0

	print(f"{len(list_missing)} unimplemented package(s) of {len(frozenset_published)} published:")
	for str_slug in list_missing:
		print(f"  - {str_slug}")

	str_repo = os.environ.get("GITHUB_REPOSITORY")
	if str_repo:
		upsert_issue(f"{_GH_API}/repos/{str_repo}", list_missing, len(frozenset_published))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
