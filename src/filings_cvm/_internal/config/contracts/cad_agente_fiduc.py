"""Data contracts for the CVM open-data *Cadastro de Agentes Fiduciários* (AGENTE_FIDUC/CAD).

`cad_agente_fiduc.zip` is a **current-state snapshot** of the registry of fiduciary agents CVM
supervises — a ZIP of two members, not a monthly dump, and not partitioned by reference month:

- `cad_agente_fiduc_pf.csv` — the natural-person (pessoa física) agents: the agent's name plus the
  registration/cancellation/situation dates. **No CPF and no `CD_CVM`** — the registry identifies a
  person agent by **name alone**, so there is no personal identifier to validate.
- `cad_agente_fiduc_pj.csv` — the legal-person (pessoa jurídica) agents: the masked `CNPJ`,
  corporate name, the same dates, the full address (incl. `PAIS`) and phone (`DDD_TEL`, `TEL`).

Both contracts declare every column required — a single-layout file, so a column CVM drops or
renames must fail loudly at read time rather than surfacing as a `KeyError` deep in a consumer's
transform. Extra columns are tolerated; missing ones are not. The two column lists are pinned to
the verbatim published headers under `tests/fixtures/cad_agente_fiduc/`, the only non-tautological
oracle (see the `pin-contracts-to-a-source-published-oracle` lesson).

⚠️ **Not a copy of the AUDITOR contract** (the sibling that established this mould): AGENTE_FIDUC
carries **three date columns** (`DT_REG`, `DT_CANCEL`, `DT_INI_SIT`) rather than one, has **no
`CD_CVM`**, and the `pj` member adds `PAIS`/`DDD_TEL`/`TEL`. Copying the sibling would ship the
wrong columns with every test green — hence the header-pinned generation.

`cad_agente_fiduc_pj.CNPJ` arrives **masked** (`00.271.457/0001-30`) and is the only CNPJ column;
`br_identifiers` check accepts the masked form. `cad_agente_fiduc_pf` has no CNPJ column, so its
`tuple_cnpj_cols` is empty — an explicit "constrains no CNPJ", not an omission.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_AGENTE_FIDUC_PF = FileContract(
	"Cadastro de Agentes Fiduciários (AGENTE_FIDUC) — pessoa física",
	"cad_agente_fiduc_pf",
	(
		"AGENTE_FIDUC",
		"DT_REG",
		"DT_CANCEL",
		"SIT",
		"DT_INI_SIT",
	),
	(),
)

CAD_AGENTE_FIDUC_PJ = FileContract(
	"Cadastro de Agentes Fiduciários (AGENTE_FIDUC) — pessoa jurídica",
	"cad_agente_fiduc_pj",
	(
		"CNPJ",
		"DENOM_SOCIAL",
		"DT_REG",
		"DT_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"MUN",
		"UF",
		"PAIS",
		"CEP",
		"DDD_TEL",
		"TEL",
	),
	("CNPJ",),
)
