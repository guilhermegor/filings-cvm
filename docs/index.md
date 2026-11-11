# **filings-cvm** <img src="assets/logo.png" align="right" width="200" style="border-radius: 15px;" alt="filings-cvm">

Biblioteca Python **tipada** para ler os arquivos abertos da
[CVM](https://www.gov.br/cvm) (Comissão de Valores Mobiliários): baixa o dump publicado no
portal de dados abertos e devolve um `DataFrame` tipado e validado por contrato.

> **Migração:** a seção de **envio** (`filings_cvm.submission`, modelo validado → XML) foi
> removida e vive no pacote separado `layouts-cvm`. Esta biblioteca não depende dele.

---

## Fonte da verdade — portal de dados abertos

Nomes de coluna e tipos vêm dos arquivos reais publicados no portal, não desta documentação:

> <https://dados.cvm.gov.br/dados/>

Cada leitor fica sob `filings_cvm.ingestion.<raiz_do_portal>`; veja **[Leitura](ingestion/index.md)**
para a visão geral e o catálogo de leitores.

---

## Início rápido

```bash
make init          # cria o virtualenv e instala os hooks de pre-commit
make unit_tests    # executa a suíte de testes
make docs_server   # serve esta documentação em http://0.0.0.0:8000
```

Instalação como dependência:

```bash
pip install opendata-cvm
```

Continue em **[Uso](usage.md)** para o primeiro `DataFrame`, ou veja a **[Leitura](ingestion/index.md)**.

---

Gerado a partir do template **lib-minimal** via [BlueprintX](https://github.com/guilhermegor/BlueprintX).
