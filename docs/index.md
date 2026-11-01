# **filings-cvm** <img src="assets/cvm-logo.png" align="right" width="200" style="border-radius: 15px;" alt="filings-cvm">

Biblioteca Python **tipada** para os padrões de arquivo XML regulatórios da
[CVM](https://www.gov.br/cvm) (Comissão de Valores Mobiliários).

Construa, valide e serialize documentos no formato exigido pela CVM — ou, à medida que a
biblioteca cresce, leia e interprete arquivos baixados da CVM de volta para modelos tipados.

---

## As duas macrosseções

Toda solução da biblioteca vive em uma destas duas direções:

| Seção | Sentido | O que faz |
|-------|---------|-----------|
| `filings_cvm.submission` | **envio** → CVM | Recebe modelos de schema validados e produz o arquivo XML compatível com a CVM, pronto para envio. |
| `filings_cvm.ingestion` | **leitura** ← CVM | Analisa e interpreta um arquivo recebido/baixado da CVM de volta para modelos tipados. Criada quando o primeiro padrão de leitura for implementado. |

O **schema compartilhado** (modelos [Pydantic](https://docs.pydantic.dev/) que espelham cada
padrão XML) é neutro em relação à direção e é reexportado pelas seções públicas — você importa
tudo de que precisa a partir de `filings_cvm.submission`.

---

## Fonte da verdade — catálogo CVM

Os nomes de campo, escalas decimais e cardinalidades vêm da página oficial de padrões da CVM,
não desta documentação:

> <https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp>

### Padrões implementados

- ✅ **Perfil Mensal — V4** ([`PadraoXMLPerfilV4.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV4.asp))
  — envio (`submission/perfil_mensal.py`).
- ✅ **Perfil Mensal — original** ([`PadraoXMLPerfil.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil.asp))
  — envio (`submission/perfil_mensal_original.py`).
- ✅ **Informe Diário — V4** ([`PadraoXMLInfoDiarioNetV4.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV4.asp))
  — envio (`submission/informe_diario.py`).
- ✅ **Informe Diário — V2** ([`PadraoXMLInfoDiarioNet739.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet739.asp))
  — envio (`submission/informe_diario_v2.py`).
- ✅ **Informe Quadrimestral — V2** ([`PadraoXMLInfoTrimV2.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoTrimV2.asp))
  — envio (`submission/informe_quadrimestral.py`).
- ✅ **Informe Trimestral — V1** ([`PadraoXMLInfoTrim.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoTrim.asp), válido até 2017-06)
  — envio (`submission/informe_trimestral_v1.py`).
- ✅ **Atualização do Cadastro de Ativos** ([`PadraoXMLAtivos.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAtivos.asp))
  — envio (`submission/cadastro_ativos.py`).
- ✅ **Informe Mensal de Investidor não Residente** ([`PadraoXMLInfoMensalINR.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoMensalINR.asp))
  — envio (`submission/inr_mensal.py`).

- ✅ **Informe de Fundo 157** ([`PadraoXMLInf157.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInf157.asp))
  — envio (`submission/inf_fundo_157.py`).
- ✅ **CDA — V4** ([`PadraoXMLCDANetV4.aspx`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV4.aspx))
  — envio (`submission/cda.py`).
- ✅ **Informe Mensal FIDC — a partir de 2019-11-01** ([`PadraoXMLMensalFIDC576.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLMensalFIDC576.asp))
  — envio (`submission/inf_mensal_fidc.py`).
- ✅ **Lâmina — V3** ([`PadraoXMLLaminaV3.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV3.asp))
  — envio (`submission/lamina.py`).
- ✅ **Extrato das Informações sobre o Fundo — V3** ([`PadraoXMLInfExtratoV3.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtratoV3.asp))
  — envio (`submission/extrato.py`).

Os demais padrões do catálogo (versões anteriores dos padrões acima, Balanço, Balancete, etc.)
estão pendentes.
Consulte o `CLAUDE.md` do repositório para o catálogo completo com o status de cada um.

---

## Início rápido

```bash
make init          # cria o virtualenv e instala os hooks de pre-commit
make unit_tests    # executa a suíte de testes
make docs_server   # serve esta documentação em http://0.0.0.0:8000
```

Instalação como dependência:

```bash
pip install filings-cvm
```

Continue em **[Uso](usage.md)** para o primeiro documento, ou veja cada padrão em **Envio**:
**[Perfil Mensal](submission/perfil_mensal.md)**, **[Informe Diário](submission/informe_diario.md)** (e **[V2](submission/informe_diario_v2.md)**),
**[Lâmina V3](submission/lamina.md)**, **[Cadastro de Ativos](submission/cadastro_ativos.md)** e **[Informe Mensal INR](submission/inr_mensal.md)**.

---

Gerado a partir do template **lib-minimal** via [BlueprintX](https://github.com/guilhermegor/BlueprintX).
