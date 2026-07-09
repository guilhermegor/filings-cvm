"""Data contract for the CVM open-data *Lâmina FIF* CSV (ingestion).

The monthly dump `lamina_fi_AAAAMM.zip` ships four CSV members; this contract describes the
lâmina proper, `lamina_fi_AAAAMM.csv` — the fact sheet, one row per fund class. Its sibling
`lamina_fi_carteira_AAAAMM.csv` has its own contract (`lamina_carteira_fif.py`), and the two
`rentab_*` series have theirs.

Every one of the 78 columns is declared required, read off the real `lamina_fi_202504.zip`
(1,324 rows). Listing them all — rather than only the keys — is the point of the contract
here: this is a single-layout member, so a column CVM drops or renames must fail loudly at
read time instead of surfacing as a `KeyError` deep in a consumer's transform. Extra columns
are tolerated; missing ones are not.

`CNPJ_FUNDO_CLASSE` arrives **masked** (`32.159.627/0001-86`); the contract's CNPJ check
unmasks before validating.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
LAMINA_FIF = FileContract(
	"Lâmina FIF",
	"lamina_fif",
	(
		"TP_FUNDO_CLASSE",
		"CNPJ_FUNDO_CLASSE",
		"ID_SUBCLASSE",
		"DENOM_SOCIAL",
		"DT_COMPTC",
		"NM_FANTASIA",
		"ENDER_ELETRONICO",
		"PUBLICO_ALVO",
		"RESTR_INVEST",
		"OBJETIVO",
		"POLIT_INVEST",
		"PR_PL_ATIVO_EXTERIOR",
		"PR_PL_ATIVO_CRED_PRIV",
		"PR_PL_ALAVANC",
		"PR_ATIVO_EMISSOR",
		"DERIV_PROTECAO_CARTEIRA",
		"RISCO_PERDA",
		"RISCO_PERDA_NEGATIVO",
		"PR_PL_APLIC_MAX_FUNDO_UNICO",
		"INVEST_INICIAL_MIN",
		"INVEST_ADIC",
		"RESGATE_MIN",
		"HORA_APLIC_RESGATE",
		"VL_MIN_PERMAN",
		"QT_DIA_CAREN",
		"CONDIC_CAREN",
		"CONVERSAO_COTA_COMPRA",
		"QT_DIA_CONVERSAO_COTA_COMPRA",
		"CONVERSAO_COTA_CANC",
		"QT_DIA_CONVERSAO_COTA_RESGATE",
		"TP_DIA_PAGTO_RESGATE",
		"QT_DIA_PAGTO_RESGATE",
		"TP_TAXA_ADM",
		"TAXA_ADM",
		"TAXA_ADM_MIN",
		"TAXA_ADM_MAX",
		"TAXA_ADM_OBS",
		"TAXA_ENTR",
		"CONDIC_ENTR",
		"QT_DIA_SAIDA",
		"TAXA_SAIDA",
		"CONDIC_SAIDA",
		"TAXA_PERFM",
		"PR_PL_DESPESA",
		"DT_INI_DESPESA",
		"DT_FIM_DESPESA",
		"ENDER_ELETRONICO_DESPESA",
		"VL_PATRIM_LIQ",
		"CLASSE_RISCO_ADMIN",
		"PR_RENTAB_FUNDO_5ANO",
		"INDICE_REFER",
		"PR_VARIACAO_INDICE_REFER_5ANO",
		"QT_ANO_PERDA",
		"DT_INI_ATIV_5ANO",
		"ANO_SEM_RENTAB",
		"CALC_RENTAB_FUNDO_GATILHO",
		"PR_VARIACAO_PERFM",
		"CALC_RENTAB_FUNDO",
		"RENTAB_GATILHO",
		"DS_RENTAB_GATILHO",
		"ANO_EXEMPLO",
		"ANO_ANTER_EXEMPLO",
		"VL_RESGATE_EXEMPLO",
		"VL_IMPOSTO_EXEMPLO",
		"VL_TAXA_ENTR_EXEMPLO",
		"VL_TAXA_SAIDA_EXEMPLO",
		"VL_AJUSTE_PERFM_EXEMPLO",
		"VL_DESPESA_EXEMPLO",
		"VL_DESPESA_3ANO",
		"VL_DESPESA_5ANO",
		"VL_RETORNO_3ANO",
		"VL_RETORNO_5ANO",
		"REMUN_DISTRIB",
		"DISTRIB_GESTOR_UNICO",
		"CONFLITO_VENDA",
		"TEL_SAC",
		"ENDER_ELETRONICO_RECLAMACAO",
		"INF_SAC",
	),
	("CNPJ_FUNDO_CLASSE",),
)
