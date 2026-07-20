"""Data contracts for the CVM open-data *Cadastro de Representantes de INVNR* (INVNR/CAD).

`cad_invnr_repres.zip` is a **current-state snapshot** of the registry of representatives of
non-resident investors (investidores não residentes) CVM supervises — a ZIP of two members, not a
periodic dump, and not partitioned by reference date:

- `cad_invnr_repres_pf.csv` — the natural-person (pessoa física) representatives: the name, the
  registration/cancellation dates and reason, and the situation. **No CPF** — the registry
  identifies a person representative by `NOME`, so there is no personal identifier to validate
  and no unique key.
- `cad_invnr_repres_pj.csv` — the legal-person (pessoa jurídica) representatives: the masked
  `CNPJ`, corporate and commercial names, the same dates/reason/situation, the shareholding
  control, the full address, phone, fax, net worth (and its base date) and e-mail.

Both contracts declare every column required — a single-layout file, so a column CVM drops or
renames must fail loudly at read time rather than surfacing as a `KeyError` deep in a consumer's
transform. Extra columns are tolerated; missing ones are not. The two column lists are pinned to
the verbatim published headers under `tests/fixtures/cad_invnr_repres/`, the only non-tautological
oracle (see the `pin-contracts-to-a-source-published-oracle` lesson).

⚠️ **Not a copy of the AUDITOR / AGENTE_FIDUC / AGENTE_AUTON contracts** (the siblings of this
mould): INVNR adds `CONTROLE_ACIONARIO`, `DDD_FAX`, `FAX`, `VL_PATRIM_LIQ` and `DT_PATRIM_LIQ`,
and uses `DDD_TEL` (not AGENTE_AUTON's `DDD`). The `pj` member therefore has **four** date columns
(`DT_REG`, `DT_CANCEL`, `DT_INI_SIT`, `DT_PATRIM_LIQ`) against the `pf` member's three;
`MOTIVO_CANCEL` is free text (`varchar` in the META), **not** a date. Copying a sibling would ship
the wrong columns with every test green — hence header-pinned generation.

⚠️ **`CEP`, `TEL` and `FAX` are declared `numeric` in the CVM META but are read as text**, like
every other non-date column here. They are identifiers, not quantities: the published `CEP`
already arrives with its leading zero dropped (`1311920` for `01311-920`), and typing it as a
number would consolidate that loss instead of preserving the source bytes.

`cad_invnr_repres_pj.CNPJ` arrives **masked** (`76.621.457/0001-85`) and is the only CNPJ column;
the `br_identifiers` check accepts the masked form. `cad_invnr_repres_pf` has no CNPJ column, so
`tuple_cnpj_cols` is empty — an explicit "constrains no CNPJ", not an omission.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_INVNR_REPRES_PF = FileContract(
	"Cadastro de Representantes de Investidores Não Residentes (INVNR) — pessoa física",
	"cad_invnr_repres_pf",
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

CAD_INVNR_REPRES_PJ = FileContract(
	"Cadastro de Representantes de Investidores Não Residentes (INVNR) — pessoa jurídica",
	"cad_invnr_repres_pj",
	(
		"CNPJ",
		"DENOM_SOCIAL",
		"DENOM_COMERC",
		"DT_REG",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"CONTROLE_ACIONARIO",
		"TP_ENDER",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"MUN",
		"UF",
		"CEP",
		"DDD_TEL",
		"TEL",
		"DDD_FAX",
		"FAX",
		"VL_PATRIM_LIQ",
		"DT_PATRIM_LIQ",
		"EMAIL",
	),
	("CNPJ",),
)
