"""Data contract for the CVM open-data *Cadastro de Emissor CEPAC* CSV (ingestion).

``cad_emissor_cepac.csv`` (dataset ``EMISSOR_CEPAC/CAD``) is the registry **snapshot** of the
issuers of CEPAC (Certificados de Potencial Adicional de Construção) — municipalities running an
urban operation. Verified against the real file: the 20 columns below are exactly as published.

A bare CSV at a **fixed URL** — CVM overwrites it in place, so there is no ``date_ref`` and a
persisted ``path_raw`` snapshot is the only record of what the registry said that day (the
``CadastroFiReader`` precedent). ``DT_REG`` / ``DT_CANCEL`` / ``DT_INI_SIT`` are dates; every other
column is exact source text. Keyed by ``CNPJ`` (the issuer is a municipality).
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_EMISSOR_CEPAC = FileContract(
	"Cadastro de Emissor CEPAC",
	"cad_emissor_cepac",
	(
		"CNPJ",
		"DENOM_SOCIAL",
		"DT_REG",
		"DT_CANCEL",
		"MOTIVO_CANCEL",
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
		"DDD_FAX",
		"FAX",
		"EMAIL",
		"DIRETOR",
	),
	("CNPJ",),
)
