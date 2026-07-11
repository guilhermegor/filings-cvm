"""Data contracts for the CVM open-data *Informe Anual FII* CSVs (ingestion).

``inf_anual_fii_AAAA.zip`` ships **12 members** — the tables of the FII annual report
(``FII/DOC/INF_ANUAL``): cadastro (``geral``, ``complemento``), the assets acquired/transacted and
their book value, the shareholder distribution, the responsible director and service providers
(with their professional experience), the fund's lawsuits (``processo``, ``processo_semelhante``)
and the shareholders' representative. Verified against the real archive (``2025``): each column
list and order below is exactly as published.

**Partitioned by year** — ``inf_anual_fii_2025.zip``. Here the yearly partition is natural (it *is*
the annual report), unlike the FII monthly and quarterly dumps, where a yearly archive is the trap.
The reader's ``date_ref`` selects the year; see ``_base_inf_anual_fii_reader``.

``CNPJ_Fundo_Classe`` is the fund key on every member and the only CNPJ-validated column. Several
members also carry **counterparty** CNPJs — ``CNPJ_Prestador``, ``CNPJ_Administrador``, and (in
``complemento``) the gestor / custodiante / auditor / formador de mercado / distribuidor /
consultor / empresa de locação CNPJs — which are read as text and **not** validated as the fund's
CNPJ.

Two more things this dump carries that the others do not:

- ``complemento`` has a **``Link_Download_Anexo``** — an external URL to the filed annex. The
  reader returns it as **text and does not follow it**, exactly as ``DfinFiiReader`` treats its
  ``Link_Download``.
- ``diretor_responsavel`` and ``representante_cotista`` carry a **``CPF``** (a natural person's
  id). It is read as exact text and **never** validated as a CNPJ; treat it as personal data
  downstream.

**No unique key.** Most members are **long** — one row per ativo / transação / processo /
prestador / diretor — so a fund appears many times; the readers assert no grain.

**Deviation from "one contract per file" — deliberate**, as for ``cad_fi_hist.py``,
``inf_mensal_fidc.py``, ``inf_mensal_fii.py`` and ``inf_trimestral_fii.py``: the 12 are members of
a single input artifact (one yearly ZIP, one dataset page), so they live together here, one
constant each, re-exported individually from ``contracts/__init__``.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
INF_ANUAL_FII_GERAL = FileContract(
	"Informe Anual FII — geral",
	"inf_anual_fii_geral",
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

INF_ANUAL_FII_COMPLEMENTO = FileContract(
	"Informe Anual FII — complemento",
	"inf_anual_fii_complemento",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Gestor",
		"CNPJ_Gestor",
		"Endereco_Gestor",
		"Telefone_Gestor",
		"Nome_Custodiante",
		"CNPJ_Custodiante",
		"Endereco_Custodiante",
		"Telefone_Custodiante",
		"Nome_Auditor_Independente",
		"CNPJ_Auditor_Independente",
		"Endereco_Auditor_Independente",
		"Telefone_Auditor_Independente",
		"Nome_Formador_Mercado",
		"CNPJ_Formador_Mercado",
		"Endereco_Formador_Mercado",
		"Telefone_Formador_Mercado",
		"Nome_Distribuidor_Cotas",
		"CNPJ_Distribuidor_Cotas",
		"Endereco_Distribuidor_Cotas",
		"Telefone_Distribuidor_Cotas",
		"Nome_Consultor_Especializado",
		"CNPJ_Consultor_Especializado",
		"Endereco_Consultor_Especializado",
		"Telefone_Consultor_Especializado",
		"Nome_Empresa_Locacao",
		"CNPJ_Empresa_Locacao",
		"Endereco_Empresa_Locacao",
		"Telefone_Empresa_Locacao",
		"Programa_Investimentos_Exercicio_Seguinte",
		"Resultado_Exercicio_Findo",
		"Conjuntura_Economica_Periodo_Findo",
		"Perspectiva_Periodo_Seguinte",
		"Criterios_Avaliacao",
		"Analise_Impacto_Perda_Processos_Sigilosos",
		"Endereco_Fisico_Documentos_Assembleia_Geral",
		"Endereco_Eletronico_Documentos_Assembleia_Geral",
		"Meio_Comunicacao_Cotistas",
		"Regras_Participacao_Cotistas_Assembleia_Geral",
		"Pratica_Assembleia_Meio_Eletronico",
		"Politica_Remuneracao",
		"Valor_Pago_Ano_Referencia",
		"Percentual_Patrimonio_Contabil",
		"Percentual_Patrimonio_Valor_Mercado",
		"Politica_Divulgacao_Fato_Relevante",
		"Politica_Negociacao_Cotas",
		"Politica_Exercicio_Direito_Voto",
		"Responsaveis_Politica_Divulgacao",
		"Regras_Prazos_Chamada_Capital",
		"Link_Download_Anexo",
	),
	("CNPJ_Fundo_Classe",),
)

INF_ANUAL_FII_ATIVO_ADQUIRIDO = FileContract(
	"Informe Anual FII — ativo adquirido",
	"inf_anual_fii_ativo_adquirido",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Ativo",
		"Objetivos",
		"Montante_Investido",
		"Origem_Recursos",
	),
	("CNPJ_Fundo_Classe",),
)

INF_ANUAL_FII_ATIVO_TRANSACAO = FileContract(
	"Informe Anual FII — transação de ativo",
	"inf_anual_fii_ativo_transacao",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Ativo_Negociado",
		"Natureza_Transacao",
		"Data_Transacao",
		"Valor_Envolvido",
		"Data_Assembleia",
		"Contraparte",
	),
	("CNPJ_Fundo_Classe",),
)

INF_ANUAL_FII_ATIVO_VALOR_CONTABIL = FileContract(
	"Informe Anual FII — valor contábil do ativo",
	"inf_anual_fii_ativo_valor_contabil",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Ativo",
		"Valor",
		"Valor_Justo",
		"Percentual_Valorizacao_Desvalorizacao",
	),
	("CNPJ_Fundo_Classe",),
)

INF_ANUAL_FII_DISTRIBUICAO_COTISTAS = FileContract(
	"Informe Anual FII — distribuição de cotistas",
	"inf_anual_fii_distribuicao_cotistas",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Numero_Cotistas_Faixa_Ate_5",
		"Numero_Cotas_Detidas_Faixa_Ate_5",
		"Percentual_Cotas_Detidas_Faixa_Ate_5",
		"Percentual_Detido_PF_Faixa_Ate_5",
		"Percentual_Detido_PJ_Faixa_Ate_5",
		"Numero_Cotistas_Faixa_5a10",
		"Numero_Cotas_Detidas_Faixa_5a10",
		"Percentual_Cotas_Detidas_Faixa_5a10",
		"Percentual_Detido_PF_Faixa_5a10",
		"Percentual_Detido_PJ_Faixa_5a10",
		"Numero_Cotistas_Faixa_10a15",
		"Numero_Cotas_Detidas_Faixa_10a15",
		"Percentual_Cotas_Detidas_Faixa_10a15",
		"Percentual_Detido_PF_Faixa_10a15",
		"Percentual_Detido_PJ_Faixa_10a15",
		"Numero_Cotistas_Faixa_15a20",
		"Numero_Cotas_Detidas_Faixa_15a20",
		"Percentual_Cotas_Detidas_Faixa_15a20",
		"Percentual_Detido_PF_Faixa_15a20",
		"Percentual_Detido_PJ_Faixa_15a20",
		"Numero_Cotistas_Faixa_20a30",
		"Numero_Cotas_Detidas_Faixa_20a30",
		"Percentual_Cotas_Detidas_Faixa_20a30",
		"Percentual_Detido_PF_Faixa_20a30",
		"Percentual_Detido_PJ_Faixa_20a30",
		"Numero_Cotistas_Faixa_30a40",
		"Numero_Cotas_Detidas_Faixa_30a40",
		"Percentual_Cotas_Detidas_Faixa_30a40",
		"Percentual_Detido_PF_Faixa_30a40",
		"Percentual_Detido_PJ_Faixa_30a40",
		"Numero_Cotistas_Faixa_40a50",
		"Numero_Cotas_Detidas_Faixa_40a50",
		"Percentual_Cotas_Detidas_Faixa_40a50",
		"Percentual_Detido_PF_Faixa_40a50",
		"Percentual_Detido_PJ_Faixa_40a50",
		"Numero_Cotistas_Faixa_Acima_50",
		"Numero_Cotas_Detidas_Faixa_Acima_50",
		"Percentual_Cotas_Detidas_Faixa_Acima_50",
		"Percentual_Detido_PF_Faixa_Acima_50",
		"Percentual_Detido_PJ_Faixa_Acima_50",
	),
	("CNPJ_Fundo_Classe",),
)

INF_ANUAL_FII_DIRETOR_RESPONSAVEL = FileContract(
	"Informe Anual FII — diretor responsável",
	"inf_anual_fii_diretor_responsavel",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Diretor_Responsavel",
		"Idade",
		"CPF",
		"Profissao",
		"Email",
		"Formacao_Academica",
		"Quantidade_Cotas_FII_Detidas",
		"Quantidade_Cotas_FII_Compradas",
		"Quantidade_Cotas_FII_Vendidas",
		"Data_Inicio",
		"Condenacao_Criminal",
		"Condenacao_Processo_CVM",
	),
	("CNPJ_Fundo_Classe",),
)

INF_ANUAL_FII_EXPERIENCIA_PROFISSIONAL = FileContract(
	"Informe Anual FII — experiência profissional",
	"inf_anual_fii_experiencia_profissional",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Diretor_Representante",
		"Funcao",
		"Nome_Empresa",
		"Periodo",
		"Cargo_Funcao",
		"Atividade_Principal",
	),
	("CNPJ_Fundo_Classe",),
)

INF_ANUAL_FII_PRESTADOR_SERVICO = FileContract(
	"Informe Anual FII — prestador de serviço",
	"inf_anual_fii_prestador_servico",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Prestador",
		"CNPJ_Prestador",
		"Endereco",
		"Telefone",
	),
	("CNPJ_Fundo_Classe",),
)

INF_ANUAL_FII_PROCESSO = FileContract(
	"Informe Anual FII — processo",
	"inf_anual_fii_processo",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Numero_Processo",
		"Juizo",
		"Instancia",
		"Data_Instauracao",
		"Valor_Causa",
		"Partes_Processo",
		"Chance_Perda",
		"Principais_Fatos",
		"Analise_Impacto_Perda",
	),
	("CNPJ_Fundo_Classe",),
)

INF_ANUAL_FII_PROCESSO_SEMELHANTE = FileContract(
	"Informe Anual FII — processo semelhante",
	"inf_anual_fii_processo_semelhante",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Numero_Processo",
		"Valores",
		"Causa_Contingencia",
	),
	("CNPJ_Fundo_Classe",),
)

INF_ANUAL_FII_REPRESENTANTE_COTISTA = FileContract(
	"Informe Anual FII — representante de cotistas",
	"inf_anual_fii_representante_cotista",
	(
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Versao",
		"Nome_Representante",
		"Idade",
		"Profissao",
		"CPF",
		"Email",
		"Formacao_Academica",
		"Forma_Remuneracao",
		"Valor_Pago_Ano_Referencia",
		"Percentual_Patrimonio_Contabil",
		"Percentual_Patrimonio_Valor_Mercado",
		"Quantidade_Cotas_FII_Detidas",
		"Quantidade_Cotas_FII_Compradas",
		"Quantidade_Cotas_FII_Vendidas",
		"Data_Eleicao",
		"Termino_Mandato",
		"Condenacao_Criminal",
		"Condenacao_Processo_CVM",
	),
	("CNPJ_Fundo_Classe",),
)
