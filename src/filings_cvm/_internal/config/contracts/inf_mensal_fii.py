"""Data contracts for the CVM open-data *Informe Mensal FII* CSVs (ingestion).

``inf_mensal_fii_AAAA.zip`` ships **3 members** — the tables of the FII monthly report
(``FII/DOC/INF_MENSAL``): ``geral`` (cadastro e administrador), ``ativo_passivo`` (composição do
ativo e do passivo) and ``complemento`` (cotistas, patrimônio e rentabilidade). Every member is
keyed by ``CNPJ_Fundo_Classe`` + ``Data_Referencia`` + ``Versao``. Verified against the real
archive (``2025``): each column list and order below is exactly as published.

**The dump is partitioned by YEAR, not by month** — ``inf_mensal_fii_2025.zip`` holds the twelve
monthly rows of 2025 (``Data_Referencia`` is the month's first day). The reader's ``date_ref``
therefore selects the *year*; see ``_base_inf_mensal_fii_reader``.

**Column names are reproduced verbatim, CVM's own quirks included** — do not "fix" them or the
contract stops matching the file:

- ``Numero_Cotistas_Entidade_Fechada_Previdência_Complementar`` carries an **accented** ``ê``,
  unlike its unaccented siblings.
- ``Outros_Valores_Mobliarios`` and ``Provisoes_Contigencias`` are **CVM's misspellings** (of
  *Mobiliários* / *Contingências*).

**Deviation from "one contract per file" — deliberate**, as for ``cad_fi_hist.py`` and
``inf_mensal_fidc.py``: these 3 are the members of a **single input artifact** (one yearly ZIP,
one dataset page) and a uniform family, so they live together here, one constant each,
re-exported individually from ``contracts/__init__``.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
INF_MENSAL_FII_GERAL = FileContract(
	"Informe Mensal FII — geral",
	"inf_mensal_fii_geral",
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
	),
	("CNPJ_Fundo_Classe",),
)

INF_MENSAL_FII_ATIVO_PASSIVO = FileContract(
	"Informe Mensal FII — ativo e passivo",
	"inf_mensal_fii_ativo_passivo",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Total_Necessidades_Liquidez",
		"Disponibilidades",
		"Titulos_Publicos",
		"Titulos_Privados",
		"Fundos_Renda_Fixa",
		"Total_Investido",
		"Direitos_Bens_Imoveis",
		"Terrenos",
		"Imoveis_Renda_Acabados",
		"Imoveis_Renda_Construcao",
		"Imoveis_Venda_Acabados",
		"Imoveis_Venda_Construcao",
		"Outros_Direitos_Reais",
		"Acoes",
		"Debentures",
		"Bonus_Subscricao",
		"Certificados_Deposito_Valores_Mobiliarios",
		"Cedulas_Debentures",
		"Fundo_Acoes",
		"FIP",
		"FII",
		"FDIC",
		"Outras_Cotas_FI",
		"Notas_Promissorias",
		"Acoes_Sociedades_Atividades_FII",
		"Cotas_Sociedades_Atividades_FII",
		"CEPAC",
		"CRI",
		"CRI_CRA",
		"Letras_Hipotecarias",
		"LCI",
		"LCI_LCA",
		"LIG",
		"Outros_Valores_Mobliarios",
		"Valores_Receber",
		"Contas_Receber_Aluguel",
		"Contas_Receber_Venda_Imoveis",
		"Outros_Valores_Receber",
		"Rendimentos_Distribuir",
		"Taxa_Administracao_Pagar",
		"Taxa_Performance_Pagar",
		"Obrigacoes_Aquisicao_Imoveis",
		"Adiantamento_Venda_Imoveis",
		"Adiantamento_Alugueis",
		"Obrigacoes_Securitizacao_Recebiveis",
		"Instrumentos_Financeiros_Derivativos",
		"Provisoes_Contigencias",
		"Outros_Valores_Pagar",
		"Total_Passivo",
	),
	("CNPJ_Fundo_Classe",),
)

INF_MENSAL_FII_COMPLEMENTO = FileContract(
	"Informe Mensal FII — complemento",
	"inf_mensal_fii_complemento",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Data_Informacao_Numero_Cotistas",
		"Total_Numero_Cotistas",
		"Numero_Cotistas_Pessoa_Fisica",
		"Numero_Cotistas_Pessoa_Juridica_Nao_Financeira",
		"Numero_Cotistas_Banco_Comercial",
		"Numero_Cotistas_Corretora_Distribuidora",
		"Numero_Cotistas_Outras_Pessoas_Juridicas_Financeira",
		"Numero_Cotistas_Investidores_Nao_Residentes",
		"Numero_Cotistas_Entidade_Aberta_Previdencia_Complementar",
		"Numero_Cotistas_Entidade_Fechada_Previdência_Complementar",
		"Numero_Cotistas_Regime_Proprio_Previdencia_Servidores_Publicos",
		"Numero_Cotistas_Sociedade_Seguradora_Resseguradora",
		"Numero_Cotistas_Sociedade_Capitalizacao_Arrendamento_Mercantil",
		"Numero_Cotistas_FII",
		"Numero_Cotistas_Outros_Fundos",
		"Numero_Cotistas_Distribuidores_Fundo",
		"Numero_Cotistas_Outros_Tipos",
		"Valor_Ativo",
		"Patrimonio_Liquido",
		"Cotas_Emitidas",
		"Valor_Patrimonial_Cotas",
		"Percentual_Despesas_Taxa_Administracao",
		"Percentual_Despesas_Agente_Custodiante",
		"Percentual_Rentabilidade_Efetiva_Mes",
		"Percentual_Rentabilidade_Patrimonial_Mes",
		"Percentual_Dividend_Yield_Mes",
		"Percentual_Amortizacao_Cotas_Mes",
	),
	("CNPJ_Fundo_Classe",),
)
