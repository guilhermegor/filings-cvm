"""Data contracts for the CVM open-data *Informe Mensal CRA* CSVs (ingestion).

``inf_mensal_cra_AAAA.zip`` (dataset ``SECURIT/DOC/INF_MENSAL_CRA``) ships **8 members** — the
sections of the monthly report of the **CRA** (*Certificado de Recebíveis do Agronegócio*)
operations. Every member shares the same four-column key prefix — ``CNPJ_Emissora``,
``Codigo_Identificacao_Certificado``, ``Data_Referencia``, ``Versao`` — then carries its own
section-specific columns. Verified against the real archive (``2025``): each column list and order
below was **generated from the published header**, never transcribed, and is locked by
``tests/fixtures/inf_mensal_cra/*_header.csv`` (the verbatim header bytes as published).

⚠️ **Yearly-partitioned despite being a monthly report** (``inf_mensal_cra_AAAA.zip``, members
``inf_mensal_cra_<section>_AAAA.csv``), like the OTS and FII dumps.

⚠️ **These are NOT the OTS contracts with a new name — all 8 members differ.** CRA is *agro*; OTS is
the generic residual. Copying the OTS tuples would ship 8 wrong contracts **with all tests green**
(the tests assert whatever contract was written), which is why the tuples here come from the bytes
and are pinned to a tracked header fixture. The real differences:

* all 8 members: OTS's ``CNPJ_Securitizadora`` is ``CNPJ_Emissora`` here;
* ``direitos_creditorios``: 56 columns vs OTS's 43 — 13 extra agro receivable buckets
  (produção / comercialização / beneficiamento / industrialização, each also ``_Insumos`` and
  ``_Maquinas``);
* ``geral``: 31 vs 36 — adds ``Cadeia_Producao``, ``Tipo_Segmento``, ``Data_Ultima_Classificacao``
  and drops OTS's contingency block (so OTS's ``Outras_Contigencias_Relevantes`` typo has **no
  counterpart here** — do not carry it over);
* ``derivativos``: ``*_Commodities`` is ``*_Commodities_Agricolas``;
* ``classe``: ``Codigo_CETIP`` and ``Valor_Total_Integralizado`` (not OTS's
  ``Codigo_Negociacao_Mercado_Secundario`` / ``Total_Integralizado``);
* ``fluxo_caixa``: ``Recebimentos_Direitos_Creditorios`` /
  ``Aquisicao_Novos_Direitos_Creditorios``.

**Three findings from the real bytes, all honoured below:**

1. **``CNPJ_Emissora`` is the ONLY declared CNPJ column** — on all 8 members (6000/6000 rows
   are well-formed 14-digit CNPJs). The ``CNPJ`` column of ``cedente_devedor`` is **not a CNPJ
   column at all**: it is a dirty free-text identifier field. Across the full 2025 file it holds
   14-digit CNPJs (7090 rows), **11-digit CPFs (327 rows — the cedente/devedor may be a natural
   person)**, a ``'0'`` placeholder (2352), a bare ``','`` (103), a malformed 15-digit value (72)
   and even **two identifiers crammed into one cell** (12 rows, e.g. a CPF followed by a second
   number). Declaring it a CNPJ column would make a valid file fail the contract — the same trap as
   ``cad_fi``'s ``CPF_CNPJ_GESTOR`` and OTS's own ``cedente_devedor``. It is read as exact text and
   never validated; being a CPF, it is **personal data** — verbatim in bronze, LGPD handled
   downstream.
2. **``Indice_Subordinacao_Data_Base`` (in ``classe``) is NOT a date** despite its name — the real
   values are numeric (``0.00``). A reader must not coerce it; it stays ``str``.
3. **``geral`` carries three columns that are 100% blank** in 2025 — ``CNPJ_Agente_Fiduciario``,
   ``CNPJ_Custodiante`` and ``CNPJ_Agencia_Classificadora``. Published, they are part of
   the contract, but they are deliberately **left out of ``tuple_cnpj_cols``**: there is nothing to
   validate today, and declaring them would fail a valid file the day CVM starts filling them with
   the same dirty free text as ``cedente_devedor.CNPJ``.

**Deviation from "one contract per file" — deliberate**, exactly as for ``cad_fi_hist.py``,
``inf_mensal_fidc.py`` and ``inf_mensal_ots.py``. These 8 are the members of a **single input
artifact** (one yearly ZIP, one dataset page) and a **uniform family**, so 8 one-constant modules
would be pure sprawl. They live together here, one constant each, re-exported individually from
``contracts/__init__``.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
INF_MENSAL_CRA_GERAL = FileContract(
	"Informe Mensal CRA — geral",
	"inf_mensal_cra_geral",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Data_Entrega",
		"Companhia_Emissora",
		"Agente_Fiduciario",
		"CNPJ_Agente_Fiduciario",
		"Custodiante",
		"CNPJ_Custodiante",
		"Instituicao_Regime_Fiduciario",
		"Revolvencia",
		"Numero_Emissao",
		"Nome_Emissao",
		"Quantidade_Series",
		"Data_Emissao",
		"Tipo_Lastro",
		"Detalhamento_Lastro",
		"Sobrecolateralizacao",
		"Outras_Caracteristicas_Emissao",
		"Cadeia_Producao",
		"Tipo_Segmento",
		"Especificacao_Tipo_Segmento",
		"Tipo_Retencao_Risco",
		"Retentor_Risco",
		"Agencia_Classificadora",
		"CNPJ_Agencia_Classificadora",
		"Data_Ultima_Classificacao",
		"Recomposicao_Indice",
		"Patrimonio_Liquido_Emissao",
		"Desempenho_Emissao",
	),
	("CNPJ_Emissora",),
)

INF_MENSAL_CRA_ATIVO_PASSIVO = FileContract(
	"Informe Mensal CRA — ativo/passivo",
	"inf_mensal_cra_ativo_passivo",
	(
		"CNPJ_Emissora",
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
		"Companhia_Securitizadora_Emissora",
	),
	("CNPJ_Emissora",),
)

INF_MENSAL_CRA_CLASSE = FileContract(
	"Informe Mensal CRA — classe",
	"inf_mensal_cra_classe",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Classe",
		"Numero_Serie",
		"Tipo_Oferta",
		"Codigo_CETIP",
		"Codigo_ISIN",
		"Data_Vencimento",
		"Situacao",
		"Valor_Total_Integralizado",
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
	("CNPJ_Emissora",),
)

INF_MENSAL_CRA_DIREITOS_CREDITORIOS = FileContract(
	"Informe Mensal CRA — direitos creditórios",
	"inf_mensal_cra_direitos_creditorios",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Parcelas_Atraso",
		"Direitos_Creditorios_Receber",
		"Direitos_Creditorios_Receber_Producao",
		"Direitos_Creditorios_Receber_Comercializacao",
		"Direitos_Creditorios_Receber_Beneficiamento",
		"Direitos_Creditorios_Receber_Industrializacao",
		"Direitos_Creditorios_Receber_Producao_Insumos",
		"Direitos_Creditorios_Receber_Comercializacao_Insumos",
		"Direitos_Creditorios_Receber_Beneficiamento_Insumos",
		"Direitos_Creditorios_Receber_Industrializacao_Insumos",
		"Direitos_Creditorios_Receber_Producao_Maquinas",
		"Direitos_Creditorios_Receber_Comercializacao_Maquinas",
		"Direitos_Creditorios_Receber_Beneficiamento_Maquinas",
		"Direitos_Creditorios_Receber_Industrializacao_Maquinas",
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
	("CNPJ_Emissora",),
)

INF_MENSAL_CRA_DESEMBOLSO = FileContract(
	"Informe Mensal CRA — desembolso",
	"inf_mensal_cra_desembolso",
	(
		"CNPJ_Emissora",
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
	("CNPJ_Emissora",),
)

INF_MENSAL_CRA_FLUXO_CAIXA = FileContract(
	"Informe Mensal CRA — fluxo de caixa",
	"inf_mensal_cra_fluxo_caixa",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Recebimentos_Direitos_Creditorios",
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
		"Aquisicao_Novos_Direitos_Creditorios",
		"Outros_Recebimentos",
		"Outros_Pagamentos",
		"Variacao_Liquida_Caixa",
	),
	("CNPJ_Emissora",),
)

INF_MENSAL_CRA_DERIVATIVOS = FileContract(
	"Informe Mensal CRA — derivativos",
	"inf_mensal_cra_derivativos",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Mercado_Termo_Juros",
		"Mercado_Termo_Commodities_Agricolas",
		"Mercado_Termo_Cambio",
		"Mercado_Termo_Outros",
		"Futuros_Juros",
		"Futuros_Commodities_Agricolas",
		"Futuros_Cambio",
		"Futuros_Outros",
		"Opcoes_Juros",
		"Opcoes_Commodities_Agricolas",
		"Opcoes_Cambio",
		"Opcoes_Outros",
		"Swap_Juros",
		"Swap_Commodities_Agricolas",
		"Swap_Cambio",
		"Swap_Outros",
	),
	("CNPJ_Emissora",),
)

INF_MENSAL_CRA_CEDENTE_DEVEDOR = FileContract(
	"Informe Mensal CRA — cedente/devedor",
	"inf_mensal_cra_cedente_devedor",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Tipo",
		"CNPJ",
		"Percentual",
	),
	("CNPJ_Emissora",),
)
