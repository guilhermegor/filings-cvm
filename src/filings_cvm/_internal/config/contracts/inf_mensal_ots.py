"""Data contracts for the CVM open-data *Informe Mensal OTS* CSVs (ingestion).

``inf_mensal_ots_AAAA.zip`` (dataset ``SECURIT/DOC/INF_MENSAL_OTS``) ships **8 members** — the
sections of the monthly report of the *Operações de Securitização* that are neither CRA nor CRI.
Every member shares the same four-column key prefix — ``CNPJ_Securitizadora``,
``Codigo_Identificacao_Certificado``, ``Data_Referencia``, ``Versao`` — then carries its own
section-specific columns. Verified against the real archive (``2025``): each column list and order
below is exactly as published.

⚠️ **Yearly-partitioned despite being a monthly report** (``inf_mensal_ots_AAAA.zip``, members
``inf_mensal_ots_<section>_AAAA.csv``), like the FII dumps.

**Three findings from the real bytes, all honoured below:**

1. **``CNPJ_Securitizadora`` is the ONLY CNPJ column** — on all 8 members. The ``CNPJ`` column of
   ``cedente_devedor`` holds a **CPF on 257 of 1650 rows** (the cedente/devedor may be a natural
   person), so declaring it a CNPJ column would make a valid file fail the contract — the same trap
   as ``cad_fi``'s ``CPF_CNPJ_GESTOR``. It is read as exact text and never validated (and, being a
   CPF, it is personal data: verbatim in bronze, LGPD handled downstream).
2. **``Indice_Subordinacao_Data_Base`` (in ``classe``) is NOT a date** despite its name — the real
   values are numeric (``0.00000000000000000000``). A reader must not coerce it; it stays ``str``.
3. **CVM typo preserved verbatim:** ``Outras_Contigencias_Relevantes`` in ``geral`` (missing the
   *n* of *Contingências*) — while ``Contingencias_Principais_Fatos``, in the **same** file, is
   spelled correctly. Reproduce the names as published, never as they "should" be.

**Deviation from "one contract per file" — deliberate**, exactly as for ``cad_fi_hist.py`` and
``inf_mensal_fidc.py``. These 8 are the members of a **single input artifact** (one yearly ZIP, one
dataset page) and a **uniform family**, so 8 one-constant modules would be pure sprawl. They live
together here, one constant each, re-exported individually from ``contracts/__init__``.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
INF_MENSAL_OTS_GERAL = FileContract(
	"Informe Mensal OTS — geral",
	"inf_mensal_ots_geral",
	(
		"CNPJ_Securitizadora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Data_Entrega",
		"Companhia_Securitizadora",
		"Descricao_Titulo_Securitizacao",
		"Relativo_SPE",
		"Agente_Fiduciario",
		"Custodiante_Registradora",
		"Instituicao_Regime_Fiduciario",
		"Revolvencia",
		"Numero_Emissao",
		"Nome_Emissao",
		"Quantidade_Series",
		"Data_Emissao",
		"Tipo_Lastro",
		"Detalhamento_Lastro",
		"Segmento_Economico_Lastro",
		"Principais_Caracteristicas_Lastro",
		"Sobrecolateralizacao",
		"Outras_Caracteristicas",
		"Tipo_Retencao_Risco",
		"Retentor_Risco",
		"Total_Quantidade_Valores_Mobiliarios",
		"Total_Valor_Valores_Mobiliarios",
		"Total_Rendimentos_Distribuidos",
		"Total_Amortizacoes",
		"Agencia_Classificadora",
		"Data_Classificacao_Risco",
		"Recomposicao_Indice",
		"Patrimonio_Liquido_Emissao",
		"Desempenho_Emissao",
		"Contingencias_Principais_Fatos",
		"Contingencias_Valores_Envolvidos",
		"Outras_Contigencias_Relevantes",
	),
	("CNPJ_Securitizadora",),
)

INF_MENSAL_OTS_ATIVO_PASSIVO = FileContract(
	"Informe Mensal OTS — ativo/passivo",
	"inf_mensal_ots_ativo_passivo",
	(
		"CNPJ_Securitizadora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Ativo",
		"Direitos_Creditorios",
		"Creditos_A_Vencer_Sem_Parcelas_Atraso",
		"Creditos_A_Vencer_Com_Parcelas_Atraso",
		"Creditos_Vencidos",
		"Reducao_Valor_Recuperacao",
		"Caixa_Equivalentes",
		"Caixa_Titulos_Publicos_Federais",
		"Caixa_Cotas_Fundos",
		"Caixa_Operacoes_Compromissadas",
		"Caixa_Outros",
		"Ativo_Derivativos",
		"Ativo_Contratos_Termo",
		"Ativo_Futuros",
		"Ativo_Opcoes",
		"Ativo_Swap",
		"Outros_Ativos",
		"Passivo",
		"Passivo_Derivativos",
		"Passivo_Contratos_Termo",
		"Passivo_Futuros",
		"Passivo_Opcoes",
		"Passivo_Swap",
		"Valor_Atualizado_Emissao",
		"Reducao_Valor_Emissao",
		"Outros_Passivos",
	),
	("CNPJ_Securitizadora",),
)

INF_MENSAL_OTS_CLASSE = FileContract(
	"Informe Mensal OTS — classe",
	"inf_mensal_ots_classe",
	(
		"CNPJ_Securitizadora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Classe",
		"Numero_Serie",
		"Tipo_Oferta",
		"Codigo_Negociacao_Mercado_Secundario",
		"Codigo_ISIN",
		"Data_Vencimento",
		"Situacao",
		"Total_Integralizado",
		"Taxa_Juros",
		"Pagamento_Periodicidade",
		"Pagamento_Mes_Base",
		"Quantidade_Certificados",
		"Valor_Certificados",
		"Rendimentos",
		"Amortizacoes",
		"Rentabilidade",
		"Classificacao_Risco_Atual",
		"Indice_Subordinacao_Minimo",
		"Indice_Subordinacao_Data_Base",
	),
	("CNPJ_Securitizadora",),
)

INF_MENSAL_OTS_DIREITOS_CREDITORIOS = FileContract(
	"Informe Mensal OTS — direitos creditórios",
	"inf_mensal_ots_direitos_creditorios",
	(
		"CNPJ_Securitizadora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Parcelas_Atraso",
		"Concentracao",
		"A_Vencer",
		"A_Vencer_Ate30Dias",
		"A_Vencer_31a60Dias",
		"A_Vencer_61a90Dias",
		"A_Vencer_91a120Dias",
		"A_Vencer_121a150Dias",
		"A_Vencer_151a180Dias",
		"A_Vencer_181a360Dias",
		"A_Vencer_Acima361Dias",
		"Nao_Pagos",
		"Nao_Pagos_Ate30Dias",
		"Nao_Pagos_31a60Dias",
		"Nao_Pagos_61a90Dias",
		"Nao_Pagos_91a120Dias",
		"Nao_Pagos_121a150Dias",
		"Nao_Pagos_151a180Dias",
		"Nao_Pagos_181a360Dias",
		"Nao_Pagos_Acima361Dias",
		"Pre_Pagamentos",
		"Pre_Pagamento_Lastro",
		"Pre_Pagamento_Impacto",
		"Dividas_Emissor_Securitizadora",
		"Percentual_Coobrigacao_Cedentes",
		"Percentual_Outras_Garantias",
		"Percentual_Garantias_Exceto_Coobrigacao",
		"Periodicidade_Avaliacao_Garantias",
		"Duration_Carteira",
		"Relacao_Total_Emissao",
		"Outras_Consideracoes",
		"Maior_Devedor",
		"Cinco_Maiores_Devedores",
		"Dez_Maiores_Devedores",
		"Vinte_Maiores_Devedores",
		"Maior_Cedente",
		"Cinco_Maiores_Cedentes",
		"Dez_Maiores_Cedentes",
		"Vinte_Maiores_Cedentes",
	),
	("CNPJ_Securitizadora",),
)

INF_MENSAL_OTS_DESEMBOLSO = FileContract(
	"Informe Mensal OTS — desembolso",
	"inf_mensal_ots_desembolso",
	(
		"CNPJ_Securitizadora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Pagamento_Despesas",
		"Pagamento_Despesas_Ate30Dias",
		"Pagamento_Despesas_31a60Dias",
		"Pagamento_Despesas_61a90Dias",
		"Pagamento_Despesas_91a120Dias",
		"Pagamento_Despesas_121a150Dias",
		"Pagamento_Despesas_151a180Dias",
		"Pagamento_Despesas_181a360Dias",
		"Pagamento_Despesas_Acima361Dias",
		"Pagamento_Investidores",
		"Pagamento_Investidores_Ate30Dias",
		"Pagamento_Investidores_31a60Dias",
		"Pagamento_Investidores_61a90Dias",
		"Pagamento_Investidores_91a120Dias",
		"Pagamento_Investidores_121a150Dias",
		"Pagamento_Investidores_151a180Dias",
		"Pagamento_Investidores_181a360Dias",
		"Pagamento_Investidores_Acima361Dias",
	),
	("CNPJ_Securitizadora",),
)

INF_MENSAL_OTS_FLUXO_CAIXA = FileContract(
	"Informe Mensal OTS — fluxo de caixa",
	"inf_mensal_ots_fluxo_caixa",
	(
		"CNPJ_Securitizadora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Recebimentos_Creditos",
		"Pagamentos_Despesas",
		"Pagamentos_Classe_Senior",
		"Pagamentos_Classe_Senior_Amortizacao_Principal",
		"Pagamentos_Classe_Senior_Juros",
		"Pagamentos_Classe_Subordinada_Mezanino",
		"Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal",
		"Pagamentos_Classe_Subordinada_Mezanino_Juros",
		"Pagamentos_Classe_Subordinada_Junior",
		"Pagamentos_Classe_Subordinada_Junior_Amortizacao_Principal",
		"Pagamentos_Classe_Subordinada_Junior_Juros",
		"Recebimentos_Alienacao_Caixa",
		"Aquisicao_Caixa",
		"Aquisicao_Novos_Creditos",
		"Outros_Recebimentos",
		"Outros_Pagamentos",
		"Variacao_Liquida_Caixa",
	),
	("CNPJ_Securitizadora",),
)

INF_MENSAL_OTS_DERIVATIVOS = FileContract(
	"Informe Mensal OTS — derivativos",
	"inf_mensal_ots_derivativos",
	(
		"CNPJ_Securitizadora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Mercado_Termo_Juros",
		"Mercado_Termo_Commodities",
		"Mercado_Termo_Cambio",
		"Mercado_Termo_Outros",
		"Futuros_Juros",
		"Futuros_Commodities",
		"Futuros_Cambio",
		"Futuros_Outros",
		"Opcoes_Juros",
		"Opcoes_Commodities",
		"Opcoes_Cambio",
		"Opcoes_Outros",
		"Swap_Juros",
		"Swap_Commodities",
		"Swap_Cambio",
		"Swap_Outros",
	),
	("CNPJ_Securitizadora",),
)

# ``CNPJ`` here is NOT declared a CNPJ column: it holds a CPF on 257 of 1650 real rows (the
# cedente/devedor may be a natural person). See the module docstring, finding 1.
INF_MENSAL_OTS_CEDENTE_DEVEDOR = FileContract(
	"Informe Mensal OTS — cedente/devedor",
	"inf_mensal_ots_cedente_devedor",
	(
		"CNPJ_Securitizadora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Tipo",
		"CNPJ",
		"Percentual",
	),
	("CNPJ_Securitizadora",),
)
