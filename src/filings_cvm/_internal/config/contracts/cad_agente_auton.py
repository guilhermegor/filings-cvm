"""Data contracts for the CVM open-data *Cadastro de Agentes Autônomos* (AGENTE_AUTON/CAD).

`cad_agente_auton.zip` is a **current-state snapshot** of the registry of autonomous investment
agents (agentes autônomos de investimento, AAI) CVM supervises — a ZIP of two members, not a
monthly dump, and not partitioned by reference month:

- `cad_agente_auton_pf.csv` — the natural-person (pessoa física) agents: the agent's name, the
  registration/cancellation dates and reason, and the situation. **No CPF** — the registry
  identifies a person agent by `NOME` (which can itself arrive **blank**), so there is no personal
  identifier to validate and no unique key.
- `cad_agente_auton_pj.csv` — the legal-person (pessoa jurídica) agents: the masked `CNPJ`,
  corporate and commercial names, the same dates/reason/situation, the full address, phone, e-mail
  and administrator website.

Both contracts declare every column required — a single-layout file, so a column CVM drops or
renames must fail loudly at read time rather than surfacing as a `KeyError` deep in a consumer's
transform. Extra columns are tolerated; missing ones are not. The two column lists are pinned to
the verbatim published headers under `tests/fixtures/cad_agente_auton/`, the only non-tautological
oracle (see the `pin-contracts-to-a-source-published-oracle` lesson).

⚠️ **Not a copy of the AUDITOR / AGENTE_FIDUC contracts** (the siblings of this mould): AGENTE_AUTON
adds `MOTIVO_CANCEL`, `DENOM_COMERC`, `EMAIL`, `SITE_ADMIN` and uses `DDD` (not `DDD_TEL`). It has
three date columns (`DT_REG`, `DT_CANCEL`, `DT_INI_SIT`); `MOTIVO_CANCEL` is free text, **not** a
date. Copying a sibling would ship the wrong columns with every test green — hence header-pinned
generation.

`cad_agente_auton_pj.CNPJ` arrives **masked** (`49.270.551/0001-64`) and is the only CNPJ column;
the `br_identifiers` check accepts the masked form. `cad_agente_auton_pf` has no CNPJ column, so
`tuple_cnpj_cols` is empty — an explicit "constrains no CNPJ", not an omission.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_AGENTE_AUTON_PF = FileContract(
	"Cadastro de Agentes Autônomos (AGENTE_AUTON) — pessoa física",
	"cad_agente_auton_pf",
	(
		"NOME",
		"DT_REG",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
	),
	(),
)

CAD_AGENTE_AUTON_PJ = FileContract(
	"Cadastro de Agentes Autônomos (AGENTE_AUTON) — pessoa jurídica",
	"cad_agente_auton_pj",
	(
		"CNPJ",
		"DENOM_SOCIAL",
		"DENOM_COMERC",
		"DT_REG",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"TP_ENDER",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"MUN",
		"UF",
		"CEP",
		"DDD",
		"TEL",
		"EMAIL",
		"SITE_ADMIN",
	),
	("CNPJ",),
)
