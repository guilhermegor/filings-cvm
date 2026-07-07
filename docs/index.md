# **filings-cvm**

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

### Padrão implementado

- ✅ **Perfil Mensal — V4** ([`PadraoXMLPerfilV4.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV4.asp))
  — envio (`submission/perfil_mensal.py`).

Os demais padrões do catálogo (Informe Diário, CDA, Lâmina, Informe Mensal FIDC, etc.) estão
pendentes. Consulte o `CLAUDE.md` do repositório para o catálogo completo com o status de cada um.

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

Continue em **[Uso](usage.md)** para o primeiro documento, ou pule direto para os
**[Exemplos](examples.md)**.

---

Gerado a partir do template **lib-minimal** via [BlueprintX](https://github.com/guilhermegor/BlueprintX).
