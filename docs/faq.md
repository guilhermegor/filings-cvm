# **Perguntas frequentes**

Respostas para dúvidas comuns de uso e desenvolvimento. Adicione entradas específicas do projeto
conforme surgirem nas issues.

> **Veja também:** [Uso](usage.md) · [Leitura](ingestion/index.md) · [Contribuindo](contributing.md).

---

## Como instalo a biblioteca?

```bash
pip install filings-cvm
```

Requer Python **>= 3.11**.

## Quais conjuntos da CVM já estão implementados?

Os leitores de `ingestion` cobrem os dumps de *open-data* do portal
<https://dados.cvm.gov.br/dados/>; veja a [Leitura](ingestion/index.md).

## Onde foi parar a seção `submission`?

Foi removida desta biblioteca e vive no pacote separado `layouts-cvm`, que monta e serializa os
arquivos XML de *envio* à CVM. `filings-cvm` agora só **lê** (`ingestion`) e não depende dele.

## Como adiciono ou atualizo uma dependência?

Use Poetry para manter o lock file autoritativo:

```bash
poetry add <pacote>                # dependência de runtime
poetry add --group dev <pacote>    # ferramenta só de desenvolvimento
```

Todo pacote que o código importa deve ser uma dependência **direta** — nunca dependa de que ele
chegue transitivamente por outro pacote.

## Como a versão é determinada?

A versão vem da **tag git** (via `poetry-dynamic-versioning`); o `pyproject.toml` guarda um
placeholder `0.0.0`. Lance a partir do workflow de release — veja [Contribuindo](contributing.md).
