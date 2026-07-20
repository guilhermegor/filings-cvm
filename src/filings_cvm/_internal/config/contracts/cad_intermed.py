"""Data contracts for the CVM open-data *Cadastro de Intermediários* (INTERMED/CAD).

`cad_intermed.zip` is a **current-state snapshot** of the registry of market intermediaries
(intermediários) CVM supervises — a ZIP of two members, not a periodic dump, and not partitioned by
reference date. ⚠️ **The two members are not a `pf`/`pj` split** (unlike the AUDITOR /
AGENTE_FIDUC / AGENTE_AUTON / INVNR siblings of this mould): they are the intermediary registry
itself and a table of its responsible officers, both keyed by the intermediary's `CNPJ`:

- `cad_intermed.csv` — the intermediary registry: type of participant, masked `CNPJ`, corporate and
  commercial names, registration/cancellation dates and reason, situation, CVM code, activity
  sector, shareholding control, net worth (and its base date), full address, phone, fax, e-mail and
  website.
- `cad_intermed_resp.csv` — the responsible-officer table: the intermediary's `TP_PARTIC`, `CNPJ`
  and `DENOM_SOCIAL`, its registration date, and each officer's role (`TP_RESP`), name (`RESP`),
  start date (`DT_INI_RESP`) and e-mail (`EMAIL_RESP`).

Both contracts declare every column required — a single-layout file, so a column CVM drops or
renames must fail loudly at read time rather than surfacing as a `KeyError` deep in a consumer's
transform. Extra columns are tolerated; missing ones are not. The two column lists are pinned to
the verbatim published headers under `tests/fixtures/cad_intermed/`, the only non-tautological
oracle (see the `pin-contracts-to-a-source-published-oracle` lesson).

⚠️ **`cad_intermed_resp` carries personal data** — `RESP` (an officer's name) and `EMAIL_RESP` — but
**no CPF column**: it identifies the officer by name within the intermediary's `CNPJ`. So
`tuple_cnpj_cols` on both members is `("CNPJ",)` (the intermediary's masked CNPJ), never a personal
identifier, and the fixtures are header-only (LGPD).

⚠️ **`CEP`, `TEL`, `FAX`, `DDD_TEL`, `DDD_FAX` and `CD_CVM` are declared `numeric`/`char` in the CVM
META but are read as text**, like every other non-date column here. They are identifiers, not
quantities: `DDD_TEL` already arrives with a leading zero (`051`), and typing them as numbers would
consolidate the loss. The date columns are `DT_REG`/`DT_CANCEL`/`DT_INI_SIT`/`DT_PATRIM_LIQ` on the
registry and `DT_REG`/`DT_INI_RESP` on the officer table; `MOTIVO_CANCEL` is free text, not a date.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_INTERMED = FileContract(
	"Cadastro de Intermediários (INTERMED)",
	"cad_intermed",
	(
		"TP_PARTIC",
		"CNPJ",
		"DENOM_SOCIAL",
		"DENOM_COMERC",
		"DT_REG",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"CD_CVM",
		"SETOR_ATIV",
		"CONTROLE_ACIONARIO",
		"VL_PATRIM_LIQ",
		"DT_PATRIM_LIQ",
		"TP_ENDER",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"MUN",
		"UF",
		"PAIS",
		"CEP",
		"DDD_TEL",
		"TEL",
		"DDD_FAX",
		"FAX",
		"EMAIL",
		"SITE_WEB",
	),
	("CNPJ",),
)

CAD_INTERMED_RESP = FileContract(
	"Cadastro de Intermediários (INTERMED) — responsáveis",
	"cad_intermed_resp",
	(
		"TP_PARTIC",
		"CNPJ",
		"DENOM_SOCIAL",
		"DT_REG",
		"TP_RESP",
		"RESP",
		"DT_INI_RESP",
		"EMAIL_RESP",
	),
	("CNPJ",),
)
