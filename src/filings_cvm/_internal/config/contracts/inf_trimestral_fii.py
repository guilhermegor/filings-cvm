"""Data contracts for the CVM open-data *Informe Trimestral FII* CSVs (ingestion).

``inf_trimestral_fii_AAAA.zip`` ships **16 members** — the tables of the FII quarterly report
(``FII/DOC/INF_TRIMESTRAL``): cadastro (``geral``, ``complemento``), the portfolio of assets
(``ativo`` and its garantia), and the real-estate detail (``imovel``, ``terreno``, their
acquisitions/alienations, tenants, performance) plus ``rentabilidade_efetiva`` and
``resultado_contabil_financeiro``. Verified against the real archive (``2025``): each column list
and order below is exactly as published.

**Partitioned by YEAR, not by quarter** — ``inf_trimestral_fii_2025.zip`` holds every quarter of
2025 (``Data_Referencia`` is the quarter-end). The reader's ``date_ref`` selects the *year*; see
``_base_inf_trimestral_fii_reader``.

``CNPJ_Fundo_Classe`` is the fund key on every member and the only CNPJ-validated column. Some
members also carry a **counterparty** CNPJ — ``CNPJ_Emissor`` (``ativo``), ``CNPJ_Administrador``
(``geral``) — which is read as text and **not** validated as the fund's CNPJ.

**Column names are reproduced verbatim, CVM's own quirks included** — do not "fix" them or the
contract stops matching the file: ``Outras_Receitas_Depesas_Contabil`` /
``Outras_Receitas_Depesas_Financeiro`` (in ``resultado_contabil_financeiro``) are **CVM's
misspelling** of *Despesas*.

**No unique key.** Most members are **long** — one row per asset / imóvel / contrato / inquilino /
transaction — so a fund appears many times; the readers assert no grain.

**Deviation from "one contract per file" — deliberate**, as for ``cad_fi_hist.py``,
``inf_mensal_fidc.py`` and ``inf_mensal_fii.py``: the 16 are members of a single input artifact
(one yearly ZIP, one dataset page), so they live together here, one constant each, re-exported
individually from ``contracts/__init__``.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
INF_TRIMESTRAL_FII_GERAL = FileContract(
	"Informe Trimestral FII — geral",
	"inf_trimestral_fii_geral",
	(
		"Tipo_Fundo_Classe",
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Data_Entrega",
		"Nome_Fundo_Classe",
		"Data_Funcionamento",
		"Publico_Alvo",
		"Codigo_ISIN",
		"Quantidade_Cotas_Emitidas",
		"Fundo_Exclusivo",
		"Fundo_Nao_Listado_Exclusivo",
		"Cotistas_Vinculo_Familiar",
		"Mandato",
		"Segmento_Atuacao",
		"Tipo_Gestao",
		"Prazo_Duracao",
		"Data_Prazo_Duracao",
		"Encerramento_Exercicio_Social",
		"Mercado_Negociacao_Bolsa",
		"Mercado_Negociacao_MBO",
		"Mercado_Negociacao_MB",
		"Entidade_Administradora_BVMF",
		"Entidade_Administradora_CETIP",
		"Nome_Administrador",
		"CNPJ_Administrador",
		"Logradouro",
		"Numero",
		"Complemento",
		"Bairro",
		"Cidade",
		"Estado",
		"CEP",
		"Telefone1",
		"Telefone2",
		"Telefone3",
		"Site",
		"Email",
		"Data_Encerramento_Trimestre",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_COMPLEMENTO = FileContract(
	"Informe Trimestral FII — complemento",
	"inf_trimestral_fii_complemento",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Percentual_Vencimento_Valor_Total_Faixa_Ate_3Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_Ate_3Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_3a6Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_3a6Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_6a9Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_6a9Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_9a12Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_9a12Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_12a15Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_12a15Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_15a18Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_15a18Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_18a21Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_18a21Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_21a24Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_21a24Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_24a27Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_24a27Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_27a30Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_27a30Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_30a33Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_30a33Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_33a36Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_33a36Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_Acima_36Meses",
		"Percentual_Vencimento_Receita_FII_Faixa_Acima_36Meses",
		"Percentual_Vencimento_Valor_Total_Faixa_Indeterminado",
		"Percentual_Vencimento_Receita_FII_Faixa_Indeterminado",
		"Percentual_Indexador_Valor_Total_IGPM",
		"Percentual_Indexador_Receita_FII_IGPM",
		"Percentual_Indexador_Valor_Total_INPC",
		"Percentual_Indexador_Receita_FII_INPC",
		"Percentual_Indexador_Valor_Total_IPCA",
		"Percentual_Indexador_Receita_FII_IPCA",
		"Percentual_Indexador_Valor_Total_INCC",
		"Percentual_Indexador_Receita_FII_INCC",
		"Caracteristicas_Contratuais",
		"Politica_Contratacao_Seguro_Imovel_Renda_Acabado",
		"Politica_Contratacao_Seguro_Imovel_Renda_Construcao",
		"Politica_Contratacao_Seguro_Imovel_Venda_Acabado",
		"Politica_Contratacao_Seguro_Imovel_Venda_Construcao",
		"Ativo_Liquidez_Valor_Disponibilidades",
		"Ativo_Liquidez_Valor_Titulos_Publicos",
		"Ativo_Liquidez_Valor_Titulos_Privados",
		"Ativo_Liquidez_Valor_Fundos_Renda_Fixa",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_ATIVO = FileContract(
	"Informe Trimestral FII — ativo",
	"inf_trimestral_fii_ativo",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Tipo",
		"Emissor",
		"CNPJ_Emissor",
		"Emissao",
		"Serie",
		"Codigo_Acao",
		"Nome_Ativo",
		"Data_Vencimento",
		"Quantidade",
		"Valor",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_ATIVO_GARANTIA_RENTABILIDADE = FileContract(
	"Informe Trimestral FII — ativo com garantia de rentabilidade",
	"inf_trimestral_fii_ativo_garantia_rentabilidade",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Ativo",
		"Percentual_Garantido_Relativo",
		"Garantidor",
		"Principais_Caracteristicas_Garantia",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_DIREITO = FileContract(
	"Informe Trimestral FII — direito",
	"inf_trimestral_fii_direito",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Ativo",
		"Principais_Caracteristicas",
		"Valor",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_IMOVEL = FileContract(
	"Informe Trimestral FII — imóvel",
	"inf_trimestral_fii_imovel",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Classe",
		"Nome_Imovel",
		"Endereco",
		"Area",
		"Numero_Unidades",
		"Outras_Caracteristicas_Relevantes",
		"Percentual_Vacancia",
		"Percentual_Inadimplencia",
		"Percentual_Receitas_FII",
		"Percentual_Locado",
		"Percentual_Vendido",
		"Percentual_Conclusao_Obras_Realizado",
		"Percentual_Conclusao_Obras_Previsto",
		"Custo_Construcao_Realizado",
		"Custo_Construcao_Previsto",
		"Percentual_Imovel_Total_Investido",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_IMOVEL_DESEMPENHO = FileContract(
	"Informe Trimestral FII — desempenho do imóvel",
	"inf_trimestral_fii_imovel_desempenho",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Classe",
		"Nome_Endereco_Imovel",
		"Justificativa_Evolucao_Inferior_Previsto",
		"Justificativa_Custo_Superior_Previsto",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_IMOVEL_RENDA_ACABADO_CONTRATO = FileContract(
	"Informe Trimestral FII — contrato de imóvel de renda acabado",
	"inf_trimestral_fii_imovel_renda_acabado_contrato",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Endereco_Imovel",
		"Caracteristicas_Contratuais",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_IMOVEL_RENDA_ACABADO_INQUILINO = FileContract(
	"Informe Trimestral FII — inquilino de imóvel de renda acabado",
	"inf_trimestral_fii_imovel_renda_acabado_inquilino",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Imovel",
		"Setor_Atuacao",
		"Percentual_Receita_Imovel",
		"Percentual_Receitas_FII",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_TERRENO = FileContract(
	"Informe Trimestral FII — terreno",
	"inf_trimestral_fii_terreno",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Endereco",
		"Outras_Caracteristicas_Relevantes",
		"Area",
		"Percentual_Terreno_Total_Investido",
		"Percentual_Terreno_PL",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_AQUISICAO_IMOVEL = FileContract(
	"Informe Trimestral FII — aquisição de imóvel",
	"inf_trimestral_fii_aquisicao_imovel",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Imovel",
		"Endereco",
		"Area",
		"Numero_Unidades",
		"Outras_Caracteristicas_Relevantes",
		"Percentual_Imovel_Total_Investido",
		"Categoria",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_AQUISICAO_TERRENO = FileContract(
	"Informe Trimestral FII — aquisição de terreno",
	"inf_trimestral_fii_aquisicao_terreno",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Endereco",
		"Area",
		"Outras_Caracteristicas_Relevantes",
		"Percentual_Terreno_Total_Investido",
		"Percentual_Terreno_PL",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_ALIENACAO_IMOVEL = FileContract(
	"Informe Trimestral FII — alienação de imóvel",
	"inf_trimestral_fii_alienacao_imovel",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Imovel",
		"Endereco",
		"Data_Alienacao",
		"Area",
		"Numero_Unidades",
		"Outras_Caracteristicas_Relevantes",
		"Percentual_Imovel_Total_Investido",
		"Percentual_Imovel_PL",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_ALIENACAO_TERRENO = FileContract(
	"Informe Trimestral FII — alienação de terreno",
	"inf_trimestral_fii_alienacao_terreno",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Endereco",
		"Data_Alienacao",
		"Area",
		"Outras_Caracteristicas_Relevantes",
		"Percentual_Terreno_Total_Investido",
		"Percentual_Terreno_PL",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_RENTABILIDADE_EFETIVA = FileContract(
	"Informe Trimestral FII — rentabilidade efetiva",
	"inf_trimestral_fii_rentabilidade_efetiva",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Mes_Referencia",
		"Percentual_Rentabilidade_Efetiva_Mes",
		"Percentual_Rentabilidade_Auferida_Ausencia_Garantia",
	),
	("CNPJ_Fundo_Classe",),
)

INF_TRIMESTRAL_FII_RESULTADO_CONTABIL_FINANCEIRO = FileContract(
	"Informe Trimestral FII — resultado contábil e financeiro",
	"inf_trimestral_fii_resultado_contabil_financeiro",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Receita_Venda_Estoque_Contabil",
		"Receita_Venda_Estoque_Financeiro",
		"Custo_Estoque_Contabil",
		"Custo_Estoque_Financeiro",
		"Ajuste_Realizacao_Estoque_Contabil",
		"Ajuste_Realizacao_Estoque_Financeiro",
		"Outras_Receitas_Despesas_Estoque_Contabil",
		"Outras_Receitas_Despesas_Estoque_Financeiro",
		"Resultado_Liquido_Estoque_Contabil",
		"Resultado_Liquido_Estoque_Financeiro",
		"Receita_Aluguel_Investimento_Contabil",
		"Receita_Aluguel_Investimento_Financeiro",
		"Despesa_Manutencao_Investimento_Contabil",
		"Despesa_Manutencao_Investimento_Financeiro",
		"Receita_Venda_Investimento_Contabil",
		"Receita_Venda_Investimento_Financeiro",
		"Custo_Investimento_Contabil",
		"Custo_Investimento_Financeiro",
		"Ajuste_Justo_Investimento_Contabil",
		"Ajuste_Justo_Investimento_Financeiro",
		"Outras_Receitas_Despesas_Investimento_Contabil",
		"Outras_Receitas_Despesas_Investimento_Financeiro",
		"Resultado_Liquido_Renda_Contabil",
		"Resultado_Liquido_Renda_Investimento_Financeiro",
		"Receita_Juros_TVM_Contabil",
		"Receita_Juros_TVM_Financeiro",
		"Ajuste_Justo_TVM_Contabil",
		"Ajuste_Justo_TVM_Financeiro",
		"Resultado_Venda_TVM_Contabil",
		"Resultado_Venda_TVM_Financeiro",
		"Outras_Receitas_Despesas_TVM_Contabil",
		"Outras_Receitas_Despesas_TVM_Financeiro",
		"Resultado_Liquido_TVM_Contabil",
		"Resultado_Liquido_TVM_Financeiro",
		"Resultado_Liquido_Total_Contabil",
		"Resultado_Liquido_Total_Financeiro",
		"Receita_Juros_Aplicacao_Contabil",
		"Receita_Juros_Aplicacao_Financeiro",
		"Ajuste_Justo_Aplicacao_Contabil",
		"Ajuste_Justo_Aplicacao_Financeiro",
		"Resultado_Venda_Aplicacao_Contabil",
		"Resultado_Venda_Aplicacao_Financeiro",
		"Outras_Receitas_Despesas_Aplicacao_Contabil",
		"Outras_Receitas_Despesas_Aplicacao_Financeiro",
		"Resultado_Liquido_Recurso_Liquidez_Contabil",
		"Resultado_Liquido_Recurso_Liquidez_Financeiro",
		"Resultado_Liquido_Derivativos_Contabil",
		"Resultado_Liquido_Derivativos_Financeiro",
		"Taxa_Administracao_Contabil",
		"Taxa_Administracao_Financeiro",
		"Taxa_Desempenho_Contabil",
		"Taxa_Desempenho_Financeiro",
		"Despesa_Consultoria_Especializada_Contabil",
		"Despesa_Consultoria_Especializada_Financeiro",
		"Despesa_Empresa_Especializada_Contabil",
		"Despesa_Empresa_Especializada_Financeiro",
		"Despesa_Formador_Mercado_Contabil",
		"Despesa_Formador_Mercado_Financeiro",
		"Despesa_Custodia_Contabil",
		"Despesa_Custodia_Financeiro",
		"Despesa_Auditoria_Independente_Contabil",
		"Despesa_Auditoria_Independente_Financeiro",
		"Despesa_Representantes_Cotistas_Contabil",
		"Despesa_Representantes_Cotistas_Financeiro",
		"Taxa_Imposto_Contribuicao_Contabil",
		"Taxa_Imposto_Contribuicao_Financeiro",
		"Despesa_Comissoes_Emolumentos_Contabil",
		"Despesa_Comissoes_Emolumentos_Financeiro",
		"Despesa_Honorarios_Defesas_Contabil",
		"Despesa_Honorarios_Defesas_Financeiro",
		"Despesa_Contratos_Seguros_Contabil",
		"Despesa_Contratos_Seguros_Financeiro",
		"Despesa_Avaliacoes_Contabil",
		"Despesa_Avaliacoes_Financeiro",
		"Taxa_Ingresso_Saida_Cotista_Contabil",
		"Taxa_Ingresso_Saida_Cotista_Financeiro",
		"Despesa_Registro_Cartorio_Contabil",
		"Despesa_Registro_Cartorio_Financeiro",
		"Outras_Receitas_Depesas_Contabil",
		"Outras_Receitas_Depesas_Financeiro",
		"Total_Receitas_Despesas_Contabil",
		"Total_Receitas_Despesas_Financeiro",
		"Resultado_Trimestral_Liquido_Contabil",
		"Resultado_Trimestral_Liquido_Financeiro",
		"Resultado_Financeiro_Liquido_Acumulado",
		"Resultado_Financeiro_Liquido_Acumulado_95",
		"Parcela_Rendimento_Retido",
		"Lucro_Contabil",
		"Rendimentos_Declarados",
		"Rendimentos_Pagos_Antecipadamente",
		"Rendimento_Liquido_Pagar",
		"Percentual_Resultado_Financeiro_Liquido_Declarado",
	),
	("CNPJ_Fundo_Classe",),
)
