"""Data contracts for the CVM open-data *Informe Mensal CRI* CSVs (ingestion).

``inf_mensal_cri_AAAA.zip`` (dataset ``SECURIT/DOC/INF_MENSAL_CRI``) ships **11 members** — the
sections of the monthly report of the **CRI** (*Certificado de Recebíveis Imobiliários*)
operations. Every member shares the same four-column key prefix — ``CNPJ_Emissora``,
``Codigo_Identificacao_Certificado``, ``Data_Referencia``, ``Versao`` — then carries its own
section-specific columns. Verified against the real archive (``2025``): each column list and order
below was **generated from the published header**, never transcribed, and is locked by
``tests/fixtures/inf_mensal_cri/*_header.csv`` (the verbatim header bytes as published).

⚠️ **Yearly-partitioned despite being a monthly report** (``inf_mensal_cri_AAAA.zip``, members
``inf_mensal_cri_<section>_AAAA.csv``), like the OTS and CRA dumps.

⚠️ **NOT the CRA/OTS contracts with a new name — CRI is real-estate, not agro/generic.** It shares
seven section *names* (geral, ativo_passivo, classe, derivativos, desembolso, fluxo_caixa,
cedente_devedor) but **has no ``direitos_creditorios``** — its receivables member is ``creditos``
(51 columns) — and **adds four members absent from CRA/OTS**: ``carteira``,
``carteira_modificacao``, ``creditos`` and ``responsavel``. Copying the sibling would ship wrong
contracts with all tests
green, which is why the tuples here come from the bytes and are pinned to the tracked header
fixtures.

**Findings from the real 2025 bytes, all honoured below:**

1. **``CNPJ_Emissora`` is the ONLY declared CNPJ column** — on all 11 members (3000/3000 sampled
   rows are well-formed 14-digit CNPJs). The ``CNPJ`` column of ``cedente_devedor`` is **not a CNPJ
   column**: it is a dirty free-text identifier that may hold a CPF when the cedente/devedor is a
   natural person (in 2025 mostly CNPJs, but the field is not guaranteed). Declaring it would
   fail a valid file — the ``cedente_devedor`` trap shared with CRA/OTS. Read as exact text, never
   validated; being possibly a CPF, it is personal data — verbatim in bronze, LGPD handled
   downstream.
2. **``Indice_Subordinacao_Data_Base`` (in ``classe``) is NOT a date** despite its name — the real
   values are numeric (``0.00``). It stays ``str``.
3. **``geral`` carries three columns that are 100% blank** in 2025 — ``CNPJ_Agente_Fiduciario``,
   ``CNPJ_Custodiante`` and ``CNPJ_Agencia_Classificadora`` — part of the contract but deliberately
   **left out of ``tuple_cnpj_cols``** (nothing to validate today; declaring them would fail a
   valid file). Its ``Outras_Contigencias_Relevantes`` keeps CVM's misspelling **verbatim**
   (unlike CRA,
   which drops the contingency block — a quirk is a fact about an *artifact*, not a *family*).
4. **``carteira_modificacao`` and ``responsavel`` are header-only in 2025** (zero data rows — a
   modification event and the responsible officer are filed only in specific circumstances). A
   member with no rows has no CNPJ to validate, so ``CNPJ_Emissora`` is deliberately left out of
   *their* ``tuple_cnpj_cols`` (it stays a required column). Keeping it there would raise
   ``ContractError`` on a legitimately empty member — the whole-member version of finding 3.

**Deviation from "one contract per file" — deliberate**, exactly as for ``inf_mensal_cra.py`` /
``inf_mensal_ots.py`` / ``inf_mensal_fidc.py``. These 11 are the members of a **single input
artifact** (one yearly ZIP, one dataset page) and a uniform family, so 11 one-constant modules
would be pure sprawl. They live together here, one constant each, re-exported individually from
``contracts/__init__``.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.

INF_MENSAL_CRI_GERAL = FileContract(
	"Informe Mensal CRI — geral",
	"inf_mensal_cri_geral",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Data_Entrega",
		"Numero_Emissao",
		"Nome_Emissao",
		"Quantidade_Series",
		"Data_Emissao",
		"Companhia_Emissora",
		"Instituicao_Regime_Fiduciario",
		"Agente_Fiduciario",
		"CNPJ_Agente_Fiduciario",
		"Custodiante",
		"CNPJ_Custodiante",
		"Segmento_Creditos_Vinculados",
		"Valor_Aquisicao_Credito",
		"Taxas_Medias_Indexadores_Creditos_Vinculados",
		"Anos_Duration_Carteira",
		"Meses_Duration_Carteira",
		"Forma_Calculo_Duration",
		"Tipos_Garantias_Coobrigacao_Securitizadora",
		"Tipos_Garantias_Coobrigacao_Terceiros",
		"Indice_LTV",
		"Data_LTV",
		"Tipo_Lastro",
		"Detalhamento_Lastro",
		"Sobrecolateralizacao",
		"Outras_Caracteristicas_Emissao",
		"Tipo_Retencao_Risco",
		"Retentor_Risco",
		"Agencia_Classificadora",
		"CNPJ_Agencia_Classificadora",
		"Data_Ultima_Classificacao",
		"Recomposicao_Indice",
		"Impacto_Eventos_Pre_Pagamento",
		"Analise_Impacto_Eventos_Pre_Pagamento",
		"Analise_Impacto_Outros_Eventos",
		"Analise_Impacto_Demais_Fatos",
		"Patrimonio_Liquido_Emissao",
		"Desempenho_Emissao",
		"Contingencias_Principais_Fatos",
		"Contingencias_Valores_Envolvidos",
		"Outras_Contigencias_Relevantes",
	),
	("CNPJ_Emissora",),
)

INF_MENSAL_CRI_ATIVO_PASSIVO = FileContract(
	"Informe Mensal CRI — ativo/passivo",
	"inf_mensal_cri_ativo_passivo",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Ativo",
		"Ativo_Circulante",
		"Ativo_Circulante_Disponibilidades",
		"Ativo_Circulante_Aplicacoes",
		"Ativo_Circulante_Creditos",
		"Ativo_Circulante_Outros",
		"Ativo_Nao_Circulante",
		"Ativo_Nao_Circulante_Aplicacoes",
		"Ativo_Nao_Circulante_Creditos",
		"Ativo_Nao_Circulante_Outros",
		"Creditos",
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
		"Passivo_Circulante",
		"Passivo_Circulante_Valores_Mobiliarios",
		"Passivo_Circulante_Outros",
		"Passivo_Nao_Circulante",
		"Passivo_Nao_Circulante_Valores_Mobiliarios",
		"Passivo_Nao_Circulante_Outros",
		"Passivo_Derivativos",
		"Passivo_Contratos_Termo",
		"Passivo_Futuros",
		"Passivo_Opcoes",
		"Passivo_Swap",
		"Valor_Atualizado_Emissao",
		"Reducao_Valor_Emissao",
		"Outros_Passivos",
		"Companhia_Securitizadora_Emissora",
		"Total_Recebimentos",
		"Pagamentos_Despesas_Comissoes",
		"Senior_Pagamentos",
		"Senior_Amortizacao_Principal",
		"Senior_Juros",
		"Subordinada_Pagamentos",
		"Subordinada_Amortizacao_Principal",
		"Subordinada_Juros",
		"Outros_Pagamentos_Recebimentos",
		"Suficiencia_Insuficiencia_Caixa",
		"Premio_Subordinacao",
		"Valor_Securitizadora",
		"Valor_Fundo_Despesa",
		"Valor_Fundo_Reforco",
		"Outros_Valores",
		"Descricao_Outros_Valores",
		"Valor_Pagamentos_Contratuais",
		"Valor_Pagamentos_Contratuais_Senior",
		"Valor_Pagamentos_Contratuais_Subordinada",
	),
	("CNPJ_Emissora",),
)

INF_MENSAL_CRI_CLASSE = FileContract(
	"Informe Mensal CRI — classe",
	"inf_mensal_cri_classe",
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
		"Quantidade",
		"Valor",
		"Data_Vencimento",
		"Taxas_Indexadores",
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
		"Nivel_Subordinacao",
		"Periodicidade_Amortizacao",
		"Indice_Subordinacao_Minimo",
		"Indice_Subordinacao_Data_Base",
	),
	("CNPJ_Emissora",),
)

INF_MENSAL_CRI_CREDITOS = FileContract(
	"Informe Mensal CRI — créditos",
	"inf_mensal_cri_creditos",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Parcelas_Atraso",
		"Concentracao",
		"Creditos_Natureza_Economica",
		"Creditos_Incorporacao_Imobiliaria",
		"Creditos_Alugueis",
		"Creditos_Aquisicao_Imoveis",
		"Creditos_Loteamento",
		"Creditos_Multipropriedade",
		"Creditos_Home_Equity",
		"Creditos_Outros",
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
		"Percentual_Risco_Cedentes",
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

INF_MENSAL_CRI_CARTEIRA = FileContract(
	"Informe Mensal CRI — carteira",
	"inf_mensal_cri_carteira",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Creditos_Vinculados",
		"Creditos_Vinculados_Prazo_Vencimento_Ate30Dias",
		"Creditos_Vinculados_Prazo_Vencimento_31a60Dias",
		"Creditos_Vinculados_Prazo_Vencimento_61a90Dias",
		"Creditos_Vinculados_Prazo_Vencimento_91a120Dias",
		"Creditos_Vinculados_Prazo_Vencimento_121a150Dias",
		"Creditos_Vinculados_Prazo_Vencimento_151a180Dias",
		"Creditos_Vinculados_Prazo_Vencimento_Acima180Dias",
		"Creditos_Vinculados_Inadimplentes",
		"Creditos_Vinculados_Inadimplentes_Ate30Dias",
		"Creditos_Vinculados_Inadimplentes_31a60Dias",
		"Creditos_Vinculados_Inadimplentes_61a90Dias",
		"Creditos_Vinculados_Inadimplentes_91a120Dias",
		"Creditos_Vinculados_Inadimplentes_121a150Dias",
		"Creditos_Vinculados_Inadimplentes_151a180Dias",
		"Creditos_Vinculados_Inadimplentes_Acima180Dias",
		"Creditos_Vinculados_Pagos",
		"Creditos_Vinculados_Pagos_Ate30Dias",
		"Creditos_Vinculados_Pagos_31a60Dias",
		"Creditos_Vinculados_Pagos_61a90Dias",
		"Creditos_Vinculados_Pagos_91a120Dias",
		"Creditos_Vinculados_Pagos_121a150Dias",
		"Creditos_Vinculados_Pagos_151a180Dias",
		"Creditos_Vinculados_Pagos_Acima180Dias",
		"Creditos_Processo_Liquidacao",
	),
	("CNPJ_Emissora",),
)

INF_MENSAL_CRI_CARTEIRA_MODIFICACAO = FileContract(
	"Informe Mensal CRI — modificação de carteira",
	"inf_mensal_cri_carteira_modificacao",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Evento",
		"Valor",
		"Justificativa",
	),
	# This member is header-only in the real 2025 file, since a modification is a rare event.
	# With no rows there is no issuer id to validate, so this member declares no CNPJ column;
	# the issuer column stays required but unchecked, following the geral-blank precedent above.
	(),
)

INF_MENSAL_CRI_DESEMBOLSO = FileContract(
	"Informe Mensal CRI — desembolso",
	"inf_mensal_cri_desembolso",
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

INF_MENSAL_CRI_FLUXO_CAIXA = FileContract(
	"Informe Mensal CRI — fluxo de caixa",
	"inf_mensal_cri_fluxo_caixa",
	(
		"CNPJ_Emissora",
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
	("CNPJ_Emissora",),
)

INF_MENSAL_CRI_DERIVATIVOS = FileContract(
	"Informe Mensal CRI — derivativos",
	"inf_mensal_cri_derivativos",
	(
		"CNPJ_Emissora",
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
	("CNPJ_Emissora",),
)

INF_MENSAL_CRI_CEDENTE_DEVEDOR = FileContract(
	"Informe Mensal CRI — cedente/devedor",
	"inf_mensal_cri_cedente_devedor",
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

INF_MENSAL_CRI_RESPONSAVEL = FileContract(
	"Informe Mensal CRI — responsável",
	"inf_mensal_cri_responsavel",
	(
		"CNPJ_Emissora",
		"Codigo_Identificacao_Certificado",
		"Data_Referencia",
		"Versao",
		"Nome",
		"Cargo",
	),
	# This member is header-only in 2025 like the modification member above. It declares no
	# CNPJ column for the same reason — with no rows there is no issuer id to validate.
	(),
)
