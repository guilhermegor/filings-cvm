"""Data contracts for the CVM *Cadastro de Consultores de Valores Mobiliários* (CONSULTOR_VLMOB).

`cad_consultor_vlmob.zip` is a **current-state snapshot** of the registry of securities consultants
(consultores de valores mobiliários) CVM supervises — a ZIP of **five** members, not a periodic
dump, and not partitioned by reference date. It shares ADM_CART's five-member shape (the natural-
and legal-person consultants plus their directors, responsible officers and partners):

- `cad_consultor_vlmob_pf.csv` — the natural-person (pessoa física) consultants: the consultant's
  name, the registration/cancellation dates and reason, the situation, and a website. **No CNPJ and
  no CPF** — the registry identifies a person consultant by `NOME` alone.
- `cad_consultor_vlmob_pj.csv` — the legal-person (pessoa jurídica) consultants: the masked `CNPJ`,
  corporate and commercial names, the same dates/reason/situation, shareholding control, full
  address, phone, e-mail and website.
- `cad_consultor_vlmob_diretor.csv` — the managing directors: the consultant's `CNPJ`, the
  director's name, and whether they are the default director.
- `cad_consultor_vlmob_resp.csv` — the responsible officers: the consultant's `CNPJ`, the officer's
  name and their role.
- `cad_consultor_vlmob_socios.csv` — the partners: the consultant's `CNPJ` and the partner's name.

Every contract declares all of its columns required — a single-layout file, so a column CVM drops
or renames must fail loudly at read time rather than surfacing as a `KeyError` deep in a consumer's
transform. Extra columns are tolerated; missing ones are not. The five column lists are pinned to
the verbatim published headers under `tests/fixtures/cad_consultor_vlmob/`, the only
non-tautological oracle (see the `pin-contracts-to-a-source-published-oracle` lesson).

⚠️ **Three of the five members carry no date column at all** (`diretor`, `resp`, `socios`) — like
ADM_CART. Their readers declare `_DATE_COLS = ()` and every column is read as exact source text;
the CVM META agrees (those three declare no `date` field).

⚠️ **Not a copy of ADM_CART.** `pf` is keyed by `NOME` (not `ADMIN`) and its seventh column is
`SITE_ADMIN` (not `CATEG_REG`); `pj` has 20 columns (ADM_CART has 24), dropping
`CATEG_REG`/`SUBCATEG_REG`/`VL_PATRIM_LIQ`/`DT_PATRIM_LIQ` — so `pj` carries only **three** date
columns (`DT_REG`/`DT_CANCEL`/`DT_INI_SIT`), not four. Copying the sibling would ship the wrong
columns with every test green — hence header-pinned generation.

⚠️ **`diretor`, `resp` and `socios` carry personal data** — `DIRETOR`, `RESP` and `SOCIOS` are
people's names — but **no CPF column**. So `tuple_cnpj_cols` on those three is `("CNPJ",)` (the
*consultant's* masked CNPJ), never a personal identifier, and the fixtures are header-only (LGPD).
`cad_consultor_vlmob_pf` has no CNPJ column at all, so its `tuple_cnpj_cols` is empty — an explicit
"constrains no CNPJ", not an omission. Every CNPJ column is 100% valid in the source (no malformed
value like ADM_CART's).

⚠️ **`CEP` and `TEL` are declared `numeric` in the CVM META but are read as text.** They are
identifiers, not quantities: the published `CEP` already arrives with its leading zero dropped, and
typing it as a number would consolidate that loss. `pj` uses `DDD` (like ADM_CART), not `DDD_TEL`.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_CONSULTOR_VLMOB_PF = FileContract(
	"Cadastro de Consultores de Valores Mobiliários (CONSULTOR_VLMOB) — pessoa física",
	"cad_consultor_vlmob_pf",
	(
		"NOME",
		"DT_REG",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"SITE_ADMIN",
	),
	(),
)

CAD_CONSULTOR_VLMOB_PJ = FileContract(
	"Cadastro de Consultores de Valores Mobiliários (CONSULTOR_VLMOB) — pessoa jurídica",
	"cad_consultor_vlmob_pj",
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
		"DDD",
		"TEL",
		"EMAIL",
		"SITE_ADMIN",
	),
	("CNPJ",),
)

CAD_CONSULTOR_VLMOB_DIRETOR = FileContract(
	"Cadastro de Consultores de Valores Mobiliários (CONSULTOR_VLMOB) — diretores",
	"cad_consultor_vlmob_diretor",
	(
		"CNPJ",
		"DIRETOR",
		"DIRETOR_DEFAULT",
	),
	("CNPJ",),
)

CAD_CONSULTOR_VLMOB_RESP = FileContract(
	"Cadastro de Consultores de Valores Mobiliários (CONSULTOR_VLMOB) — responsáveis",
	"cad_consultor_vlmob_resp",
	(
		"CNPJ",
		"RESP",
		"TP_RESP",
	),
	("CNPJ",),
)

CAD_CONSULTOR_VLMOB_SOCIOS = FileContract(
	"Cadastro de Consultores de Valores Mobiliários (CONSULTOR_VLMOB) — sócios",
	"cad_consultor_vlmob_socios",
	(
		"CNPJ",
		"SOCIOS",
	),
	("CNPJ",),
)
