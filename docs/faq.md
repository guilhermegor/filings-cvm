# **Perguntas frequentes**

Respostas para dúvidas comuns de uso e desenvolvimento. Adicione entradas específicas do projeto
conforme surgirem nas issues.

> **Veja também:** [Uso](usage.md) · [Envio](submission/perfil_mensal.md) · [Contribuindo](contributing.md).

---

## Como instalo a biblioteca?

```bash
pip install filings-cvm
```

Requer Python **>= 3.10**.

## Quais padrões da CVM já estão implementados?

Apenas o **Perfil Mensal V4** (envio), por enquanto. O catálogo completo — Informe Diário, CDA,
Lâmina, Informe Mensal FIDC, entre outros — está listado no `CLAUDE.md` do repositório, com o
status de cada padrão. A fonte da verdade é a
[página de padrões da CVM](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp).

## Qual a diferença entre `submission` e `ingestion`?

`submission` **monta e serializa** um arquivo para *enviar* à CVM (envio). `ingestion` **lê e
interpreta** um arquivo *baixado* da CVM de volta para modelos tipados (leitura). A seção
`ingestion` é criada quando o primeiro padrão de leitura for implementado.

## Por que devo passar valores decimais como string?

`float` binário (IEEE 754) não representa a maioria das frações decimais com exatidão, e os erros
se acumulam silenciosamente. Passe `"10.5"` (string) ou `Decimal("10.5")` — nunca `10.5`. A
biblioteca ainda **trunca** o excesso de casas em direção a zero, para não inflar o valor
reportado.

## Por que meu CNPJ foi recusado?

O CNPJ é validado pelos **dígitos verificadores**, não apenas pelo formato. Um número com dígitos
inválidos levanta `ValidationError` na construção do modelo. O valor é armazenado sem máscara
(apenas os 14 caracteres).

## Em qual codificação o arquivo é gravado?

Quando você passa `output_path`, o arquivo é gravado em **`windows-1252`**, conforme exigência da
CVM. Sem `output_path`, o método retorna a string XML (UTF-8 em memória).

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
