"""Data contracts for the CVM open-data *Ofertas de Distribuição* ZIP (ingestion).

``oferta_distribuicao.zip`` (dataset ``OFERTA/DISTRIB``) ships **two members**, one per regulatory
regime, declared here together (the ``cad_coord_oferta.py`` precedent — members of one archive
share a module):

- ``oferta_distribuicao.csv`` — the historical offerings register (76 columns, pre-RCVM 160).
- ``oferta_resolucao_160.csv`` — the RCVM 160 offering requests (71 columns).

⚠️ They are **not** a registry + satellite pair: they are two offering tables of **different
regimes** with disjoint columns, so copying one onto the other would ship the wrong contract. Their
columns are **generated from and pinned to** the verbatim published headers
(``tests/fixtures/oferta_distribuicao/*_header.csv``) — at 76/71 columns, hand-transcription is
exactly the error a pinned oracle exists to catch.

A **fixed URL** — CVM overwrites the archive in place, so there is no ``date_ref`` and a persisted
``path_raw`` snapshot is the only record of what the register said that day. The ISO ``Data_*``
columns are dates (typed in the reader); every other column is exact source text — including all
the ``Nr_*`` / ``Num_*`` / ``Qtd_*`` / ``Qtde_*`` counts and the ``Valor_*`` / ``Preco_*`` monetary
fields, which keep CVM's exact decimal text so no precision is lost (a consumer casts to
``Decimal`` where it computes). Several ``CNPJ_*`` columns hold valid CNPJs: ``CNPJ_Emissor`` /
``CNPJ_Lider`` / ``CNPJ_Ofertante`` for ``oferta_distribuicao``, ``CNPJ_Emissor`` / ``CNPJ_Lider``
for ``oferta_resolucao_160``.

⚠️ ``oferta_resolucao_160.Data_deliberacao_aprovou_oferta`` is a date **in ``DD/MM/YYYY``** (e.g.
``02/01/2023``), not the ISO form every other date column uses. The shared coercion is ISO-only
(``pd.to_datetime`` with no ``dayfirst``), so parsing it there would silently swap day and month;
it is therefore **kept as exact ``str``** and a consumer parses it with ``dayfirst=True``.
Honoured, not "fixed".
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
OFERTA_DISTRIBUICAO = FileContract(
	"Oferta de Distribuição (pré-RCVM 160)",
	"oferta_distribuicao",
	(
		"Numero_Processo",
		"Numero_Registro_Oferta",
		"Tipo_Oferta",
		"Tipo_Componente_Oferta_Mista",
		"Tipo_Ativo",
		"CNPJ_Emissor",
		"Nome_Emissor",
		"CNPJ_Lider",
		"Nome_Lider",
		"Nome_Vendedor",
		"CNPJ_Ofertante",
		"Nome_Ofertante",
		"Rito_Oferta",
		"Modalidade_Oferta",
		"Modalidade_Registro",
		"Modalidade_Dispensa_Registro",
		"Data_Abertura_Processo",
		"Data_Protocolo",
		"Data_Dispensa_Oferta",
		"Data_Registro_Oferta",
		"Data_Inicio_Oferta",
		"Data_Encerramento_Oferta",
		"Emissao",
		"Classe_Ativo",
		"Serie",
		"Especie_Ativo",
		"Forma_Ativo",
		"Data_Emissao",
		"Data_Vencimento",
		"Quantidade_Sem_Lote_Suplementar",
		"Quantidade_No_Lote_Suplementar",
		"Quantidade_Total",
		"Preco_Unitario",
		"Valor_Total",
		"Oferta_Inicial",
		"Oferta_Incentivo_Fiscal",
		"Oferta_Regime_Fiduciario",
		"Atualizacao_Monetaria",
		"Juros",
		"Projeto_Audiovisual",
		"Tipo_Societario_Emissor",
		"Tipo_Fundo_Investimento",
		"Ultimo_Comunicado",
		"Data_Comunicado",
		"Nr_Pessoa_Fisica",
		"Qtd_Pessoa_Fisica",
		"Nr_Clube_Investimento",
		"Qtd_Clube_Investimento",
		"Nr_Fundos_Investimento",
		"Qtd_Fundos_Investimento",
		"Nr_Entidade_Previdencia_Privada",
		"Qtd_Entidade_Previdencia_Privada",
		"Nr_Companhia_Seguradora",
		"Qtd_Companhia_Seguradora",
		"Nr_Investidor_Estrangeiro",
		"Qtd_Investidor_Estrangeiro",
		"Nr_Instit_Intermed_Partic_Consorcio_Distrib",
		"Qtd_Instit_Intermed_Partic_Consorcio_Distrib",
		"Nr_Instit_Financ_Emissora_Partic_Consorcio",
		"Qtd_Instit_Financ_Emissora_Partic_Consorcio",
		"Nr_Demais_Instit_Financ",
		"Qtd_Demais_Instit_Financ",
		"Nr_Demais_Pessoa_Juridica_Emissora_Partic_Consorcio",
		"Qtd_Demais_Pessoa_Juridica_Emissora_Partic_Consorcio",
		"Nr_Demais_Pessoa_Juridica",
		"Qtd_Demais_Pessoa_Juridica",
		"Nr_Soc_Adm_Emp_Prop_Demais_Pess_Jurid_Emiss_Partic_Consorcio",
		"Qdt_Soc_Adm_Emp_Prop_Demais_Pess_Jurid_Emiss_Partic_Consorcio",
		"Nr_Outros",
		"Qtd_Outros",
		"Qtd_Cli_Pessoa_Fisica",
		"Qtd_Cli_Pessoa_Juridica",
		"Qtd_Cli_Pessoa_Juridica_Ligada_Adm",
		"QtD_Cli_Demais_Pessoa_Juridica",
		"Qtd_Cli_Investidor_Estrangeiro",
		"Qtd_Cli_Soc_Adm_Emp_Prop_Demais_Pess_Jurid_Emiss_Partic_Consorcio",
	),
	("CNPJ_Emissor", "CNPJ_Lider", "CNPJ_Ofertante"),
)

OFERTA_RESOLUCAO_160 = FileContract(
	"Oferta de Distribuição (RCVM 160)",
	"oferta_resolucao_160",
	(
		"Numero_Requerimento",
		"Rito_Requerimento",
		"Numero_Processo",
		"Data_requerimento",
		"Data_Registro",
		"Data_Encerramento",
		"Status_Requerimento",
		"Valor_Mobiliario",
		"Tipo_requerimento",
		"Bookbuilding",
		"CNPJ_Emissor",
		"Nome_Emissor",
		"CNPJ_Lider",
		"Nome_Lider",
		"Grupo_Coordenador",
		"Tipo_Oferta",
		"Emissao",
		"Qtde_Total_Registrada",
		"Valor_Total_Registrado",
		"Oferta_inicial",
		"Oferta_vasos_comunicantes",
		"Publico_alvo",
		"Reabertura_serie",
		"Titulo_classificado_como_sustentavel",
		"Titulo_padronizado",
		"Destinacao_recursos",
		"Data_deliberacao_aprovou_oferta",
		"Mercado_negociacao",
		"Tipo_lastro",
		"Regime_fiduciario",
		"Ativos_alvo",
		"Descricao_garantias",
		"Descricao_lastro",
		"Identificacao_devedores_coobrigados",
		"Possibilidade_revolvencia",
		"FIDC_nao_padronizado",
		"Titulo_incentivado",
		"Regime_distribuicao",
		"Tipo_societario",
		"Administrador",
		"Gestor",
		"Agente_fiduciario",
		"Escriturador",
		"Custodiante",
		"Avaliador_Risco",
		"Processo_SEI",
		"Endereco_emissor_rede_mundial_computadores",
		"Num_Invest_Pessoa_Natural",
		"Qtde_VM_Pessoa_Natural",
		"Num_Invest_Clube_Investimento",
		"Qtde_VM_Clube_Investimento",
		"Num_Invest_Fundos_Investimento",
		"Qtde_VM_Fundos_Investimento",
		"Num_Invest_Entidade_Previdencia_Privada",
		"Qtde_VM_Entidade_Previdencia_Privada",
		"Num_Invest_Companhia_Seguradora",
		"Qtde_VM_Companhia_Seguradora",
		"Num_Invest_Investidor_Estrangeiro",
		"Qtde_VM_Investidor_Estrangeiro",
		"Num_Invest_Instit_Intermed_Partic_Consorcio_Distrib",
		"Qtde_VM_Instit_Intermed_Partic_Consorcio_Distrib",
		"Num_Invest_Instit_Financ_Emissora_Partic_Consorcio",
		"Qtde_VM_Instit_Financ_Emissora_Partic_Consorcio",
		"Num_Invest_Demais_Instit_Financ",
		"Qtde_VM_Demais_Instit_Financ",
		"Num_Invest_Demais_Pessoa_Juridica_Emissora_Partic_Consorcio",
		"Qtde_VM_Demais_Pessoa_Juridica_Emissora_Partic_Consorcio",
		"Num_Invest_Demais_Pessoa_Juridica",
		"Qtde_VM_Demais_Pessoa_Juridica",
		"Num_Invest_Soc_Adm_Emp_Prop_Demais_Pess_Jurid_Emiss_Partic_Consorcio",
		"Qdte_VM_Soc_Adm_Emp_Prop_Demais_Pess_Jurid_Emiss_Partic_Consorcio",
	),
	("CNPJ_Emissor", "CNPJ_Lider"),
)
