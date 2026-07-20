"""Data contracts for the CVM open-data *Cadastro de Administradores de Carteira* (ADM_CART/CAD).

`cad_adm_cart.zip` is a **current-state snapshot** of the registry of portfolio managers
(administradores de carteira) CVM supervises — a ZIP of **five** members, not a periodic dump, and
not partitioned by reference date. It is the first five-member root of this mould (the AUDITOR /
AGENTE_FIDUC / AGENTE_AUTON / INVNR / INTERMED siblings all ship two):

- `cad_adm_cart_pf.csv` — the natural-person (pessoa física) managers: the manager's name, the
  registration/cancellation dates and reason, the situation, and the registration category. **No
  CNPJ and no CPF** — the registry identifies a person manager by `ADMIN` (the name) alone.
- `cad_adm_cart_pj.csv` — the legal-person (pessoa jurídica) managers: the masked `CNPJ`, corporate
  and commercial names, the same dates/reason/situation, registration category and sub-category,
  shareholding control, full address, phone, net worth (and its base date), e-mail and website.
- `cad_adm_cart_diretor.csv` — the managing directors: the manager's `CNPJ`, the director's name,
  and whether they are the default director.
- `cad_adm_cart_resp.csv` — the responsible officers: the manager's `CNPJ`, the officer's name and
  their role.
- `cad_adm_cart_socios.csv` — the partners: the manager's `CNPJ` and the partner's name.

Every contract declares all of its columns required — a single-layout file, so a column CVM drops
or renames must fail loudly at read time rather than surfacing as a `KeyError` deep in a consumer's
transform. Extra columns are tolerated; missing ones are not. The five column lists are pinned to
the verbatim published headers under `tests/fixtures/cad_adm_cart/`, the only non-tautological
oracle (see the `pin-contracts-to-a-source-published-oracle` lesson).

⚠️ **Three of the five members carry no date column at all** (`diretor`, `resp`, `socios`) — the
first such shape in this library. Their readers therefore declare `_DATE_COLS = ()`, and every one
of their columns is read as exact source text. The CVM META agrees: those three declare no `date`
field.

⚠️ **`diretor`, `resp` and `socios` carry personal data** — `DIRETOR`, `RESP` and `SOCIOS` are
people's names (`SOCIOS` mixes natural and legal persons) — but **no CPF column**. So
`tuple_cnpj_cols` on those three is `("CNPJ",)` (the *manager's* masked CNPJ), never a personal
identifier, and the fixtures are header-only (LGPD). `cad_adm_cart_pf` has no CNPJ column at all,
so its `tuple_cnpj_cols` is empty — an explicit "constrains no CNPJ", not an omission.

⚠️ **One genuinely malformed CNPJ exists in the source**: `00.010.354/1901-72` appears in `pj` and
`resp` and fails the mod-11 check. Because `tuple_cnpj_cols` requires **at least one** valid CNPJ
in the column (not all of them), both contracts still pass — the bad value is honoured as
published, never patched or filtered.

⚠️ **`CEP` and `TEL` are declared `numeric` in the CVM META but are read as text.** They are
identifiers, not quantities: the published `CEP` already arrives with its leading zero dropped
(`1451010` for `01451-010`), and typing it as a number would consolidate that loss. Note `pj` uses
`DDD` (like AGENTE_AUTON), not INVNR's / INTERMED's `DDD_TEL`.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_ADM_CART_PF = FileContract(
	"Cadastro de Administradores de Carteira (ADM_CART) — pessoa física",
	"cad_adm_cart_pf",
	(
		"ADMIN",
		"DT_REG",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"CATEG_REG",
	),
	(),
)

CAD_ADM_CART_PJ = FileContract(
	"Cadastro de Administradores de Carteira (ADM_CART) — pessoa jurídica",
	"cad_adm_cart_pj",
	(
		"CNPJ",
		"DENOM_SOCIAL",
		"DENOM_COMERC",
		"DT_REG",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"CATEG_REG",
		"SUBCATEG_REG",
		"CONTROLE_ACIONARIO",
		"TP_ENDER",
		"LOGRADOURO",
		"COMPL",
		"BAIRRO",
		"MUN",
		"UF",
		"CEP",
		"DDD",
		"TEL",
		"VL_PATRIM_LIQ",
		"DT_PATRIM_LIQ",
		"EMAIL",
		"SITE_ADMIN",
	),
	("CNPJ",),
)

CAD_ADM_CART_DIRETOR = FileContract(
	"Cadastro de Administradores de Carteira (ADM_CART) — diretores",
	"cad_adm_cart_diretor",
	(
		"CNPJ",
		"DIRETOR",
		"DIRETOR_DEFAULT",
	),
	("CNPJ",),
)

CAD_ADM_CART_RESP = FileContract(
	"Cadastro de Administradores de Carteira (ADM_CART) — responsáveis",
	"cad_adm_cart_resp",
	(
		"CNPJ",
		"RESP",
		"TP_RESP",
	),
	("CNPJ",),
)

CAD_ADM_CART_SOCIOS = FileContract(
	"Cadastro de Administradores de Carteira (ADM_CART) — sócios",
	"cad_adm_cart_socios",
	(
		"CNPJ",
		"SOCIOS",
	),
	("CNPJ",),
)
