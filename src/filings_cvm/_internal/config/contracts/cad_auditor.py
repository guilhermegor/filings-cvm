"""Data contracts for the CVM open-data *Cadastro de Auditores* (AUDITOR/CAD) dump (ingestion).

`cad_auditor.zip` is a **current-state snapshot** of the registry of independent auditors CVM
supervises — a ZIP of two members, not a monthly dump, and not partitioned by reference month:

- `cad_auditor_pf.csv` — the natural-person (pessoa física) auditors: just a CVM code, the
  auditor's name, and their current situation. **No CPF column** — the registry identifies a
  person auditor by `CD_CVM` and name, so there is no personal identifier to validate here.
- `cad_auditor_pj.csv` — the legal-person (pessoa jurídica) audit firms: the same code and
  situation plus the firm's `CNPJ`, corporate name, and address.

Both contracts declare every column required — a single-layout file, so a column CVM drops or
renames must fail loudly at read time rather than surfacing as a `KeyError` deep in a consumer's
transform. Extra columns are tolerated; missing ones are not. The two column lists are pinned to
the verbatim published headers under `tests/fixtures/cad_auditor/`, the only non-tautological
oracle (see the `pin-contracts-to-a-source-published-oracle` lesson).

`cad_auditor_pj.CNPJ` arrives **masked** (`36.348.092/0001-42`) and is the only CNPJ column; the
`br_identifiers` check accepts the masked form. `cad_auditor_pf` has no CNPJ column, so its
`tuple_cnpj_cols` is empty — an explicit "constrains no CNPJ", not an omission.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_AUDITOR_PF = FileContract(
	"Cadastro de Auditores (AUDITOR) — pessoa física",
	"cad_auditor_pf",
	(
		"CD_CVM",
		"AUDITOR",
		"SIT",
		"DT_INI_SIT",
	),
	(),
)

CAD_AUDITOR_PJ = FileContract(
	"Cadastro de Auditores (AUDITOR) — pessoa jurídica",
	"cad_auditor_pj",
	(
		"CD_CVM",
		"CNPJ",
		"DENOM_SOCIAL",
		"SIT",
		"DT_INI_SIT",
		"TP_ENDER",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"MUN",
		"UF",
		"CEP",
	),
	("CNPJ",),
)
