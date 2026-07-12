"""Data contracts for the CVM open-data *Informe Mensal FIAGRO* CSVs (ingestion).

``inf_mensal_fiagro_AAAAMM.zip`` (dataset ``FIAGRO/DOC/INF_MENSAL``) ships **2 members** — the
FIAGRO monthly report and its per-subclasse breakdown:

- ``inf_mensal_fiagro_AAAAMM.csv`` — the informe proper, **133 columns**, one row per fund class
  per reference month (keyed ``CNPJ_Classe`` × ``Data_Referencia``).
- ``inf_mensal_fiagro_subclasse_AAAAMM.csv`` — **6 columns**, naturally long (one row per
  subclasse of a class).

Both use the **post-RCVM 175** nomenclature (Classe / Subclasse). Verified against the real
archive (``202506``): each column list and order below is exactly as published. Two CVM
spellings are preserved **verbatim** — ``Provisoes_Contigencias`` (missing the *n* of
*Contingências*) and the asymmetric ``A_Vencer_Acima1080_Dias`` (extra ``_`` before ``Dias``)
against ``Vencidos_Acima1080Dias`` (none). A reader must reproduce them, not "fix" them.

**Deviation from "one contract per file" — deliberate**, exactly as for ``cad_fi_hist.py`` and
``inf_mensal_fidc.py``. These 2 are members of a **single input artifact** (one monthly ZIP, one
dataset page), so two one-constant modules would be pure sprawl. They live together here, one
constant each, re-exported individually from ``contracts/__init__``. ``CNPJ_Classe`` is the CNPJ
column of both members; a subclass reader pairs each constant with its own date columns.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
INF_MENSAL_FIAGRO = FileContract(
	"Informe Mensal FIAGRO",
	"inf_mensal_fiagro",
	(
		"CNPJ_Classe",
		"Nome_Classe",
		"Data_Referencia",
		"Data_Entrega",
		"Versao",
		"Classe_Unica",
		"CNPJ_Administrador",
		"Nome_Administrador",
		"Data_Registro",
		"Publico_Alvo",
		"Codigo_ISIN",
		"Cotistas_Vinculo_Familiar",
		"Regra_Anexo",
		"Classificacao_Autorregulada",
		"Prazo_Duracao",
		"Encerramento_Exercicio_Social",
		"Mercado_Negociacao",
		"Entidade_Administradora",
		"Email_Administrador",
		"Servico_Atendimento_Cotista",
		"Site",
		"Nome_Gestor",
		"CNPJ_Gestor",
		"Numero_Cotistas",
		"Numero_Cotistas_Pessoa_Natural",
		"Numero_Cotistas_Pessoa_Juridica_Nao_Financeira",
		"Numero_Cotistas_Pessoa_Juridica_Financeira",
		"Numero_Cotistas_Investidor_Nao_Residente",
		"Numero_Cotistas_Entidade_Previdencia_Complementar_Exceto_RPPS",
		"Numero_Cotistas_Entidade_RPPS",
		"Numero_Cotistas_Sociedade_Seguradora_Resseguradora",
		"Numero_Cotistas_Fundos_Investimento",
		"Numero_Cotistas_Distribuidos_Conta_Ordem",
		"Numero_Cotistas_Outros_Tipos",
		"Valor_Ativo",
		"Patrimonio_Liquido",
		"Cotas_Emitidas",
		"Valor_Patrimonial_Cotas",
		"Percentual_Despesas_Taxa_Administracao",
		"Percentual_Despesas_Taxa_Gestao",
		"Percentual_Despesas_Taxa_Distribuicao",
		"Rentabilidade_Efetiva_Mes",
		"Rentabilidade_Patrimonial_Mes",
		"Dividend_Yield_Mes",
		"Percentual_Amortizacao_Cotas_Mes",
		"Total_Necessidades_Liquidez",
		"Fundos_Renda_Fixa",
		"Titulos_Renda_Fixa",
		"Total_Investido",
		"Imoveis_Rurais",
		"Participacoes_Societarias",
		"Ativos_Financeiros_Lato_Sensu",
		"Ativos_Financeiros",
		"Ativos_Financeiros_Emissao_IF",
		"LCA",
		"LCI",
		"Outros_Ativos_Emissao_IF",
		"Outros_Ativos_Financeiros",
		"Valores_Mobiliarios",
		"Titulos_Participacoes_Societarias",
		"Acoes_Certificados_Deposito",
		"Outros_Titulos_Participacao",
		"Titulos_Divida_Corporativa",
		"Debentures",
		"Debentures_Conversiveis",
		"Debentures_Nao_Conversiveis",
		"Notas_Comerciais",
		"Notas_Comerciais_Curto_Prazo",
		"Notas_Comerciais_Longo_Prazo",
		"Outros_Titulos_Divida_Corporativa",
		"Valor_Titulos_Credito",
		"CPR",
		"CPR_Financeira",
		"CPR_Fisica",
		"CDCA",
		"CDA_WA",
		"Outros_Titulos_Credito_Agronegocio",
		"Titulos_Credito_Liquidacao_Financeira",
		"Devedor_Pessoa_Juridica_Liquidacao_Financeira",
		"Devedor_Pessoa_Natural_Liquidacao_Financeira",
		"Titulos_Credito_Liquidacao_Fisica",
		"Devedor_Pessoa_Juridica_Liquidacao_Fisica",
		"Devedor_Pessoa_Natural_Liquidacao_Fisica",
		"Demais_Direitos_Creditorios",
		"Direitos_Creditorios_Agronegocio",
		"Direitos_Creditorios_Imoveis_Rurais",
		"Titulos_Securitizacao",
		"CRA",
		"CRI",
		"Outros_Titulos_Securitizacao",
		"Cotas_Fundos_Investimento",
		"FIF",
		"FIDC",
		"FII",
		"FIP",
		"FIIM",
		"FIAGRO",
		"Creditos_Carbono_Agronegocio",
		"Creditos_Descarbonizacao",
		"Valores_Receber",
		"Total_Ativos_Prazo_Vencimento",
		"A_Vencer",
		"A_Vencer_Ate30Dias",
		"A_Vencer_31a60Dias",
		"A_Vencer_61a90Dias",
		"A_Vencer_91a120Dias",
		"A_Vencer_121a180Dias",
		"A_Vencer_181a360Dias",
		"A_Vencer_361a720Dias",
		"A_Vencer_721a1080Dias",
		"A_Vencer_Acima1080_Dias",
		"Vencidos",
		"Vencidos_Ate30Dias",
		"Vencidos_31a60Dias",
		"Vencidos_61a90Dias",
		"Vencidos_91a120Dias",
		"Vencidos_121a180Dias",
		"Vencidos_181a360Dias",
		"Vencidos_361a720Dias",
		"Vencidos_721a1080Dias",
		"Vencidos_Acima1080Dias",
		"Rendimentos_Distribuir",
		"Taxa_Administracao_Pagar",
		"Taxa_Gestao_Pagar",
		"Taxa_Performance_Pagar",
		"Taxa_Distribuicao_Pagar",
		"Obrigacoes_Aquisicao_Ativos",
		"Adiantamento_Venda_Ativos",
		"Adiantamento_Valores_Receber",
		"Instrumentos_Financeiros_Derivativos",
		"Provisoes_Contigencias",
		"Outros_Valores_Pagar",
		"Total_Passivo",
	),
	("CNPJ_Classe",),
)

INF_MENSAL_FIAGRO_SUBCLASSE = FileContract(
	"Informe Mensal FIAGRO — subclasse",
	"inf_mensal_fiagro_subclasse",
	(
		"CNPJ_Classe",
		"Nome_Classe",
		"Data_Referencia",
		"Nome_Subclasse",
		"Numero_Cotas",
		"Valor_Patrimonial_Cota",
	),
	("CNPJ_Classe",),
)
