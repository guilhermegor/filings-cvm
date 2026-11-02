# Segurança das dependências

Um PR falha quando o `poetry.lock` contém um pacote com vulnerabilidade conhecida. O gate é o
`pip-audit` (PyPA), rodando sobre o lock exportado, e está nos dois lugares exigidos pela regra de
*gate parity*: o hook `audit-dependencies` do `.pre-commit-config.yaml` e o passo
**Run Dependency Vulnerability Audit (pip-audit)** do `.github/workflows/tests.yaml`. Os dois
chamam o mesmo script, `bin/audit_dependencies.sh`.

```bash
bash bin/audit_dependencies.sh
```

## Avaliação: pip-audit × Snyk (#90)

O que já existia: CodeQL (SAST), alertas do Dependabot (avisam, não bloqueiam) e atualizações de
versão do Dependabot. A lacuna era só **um gate em CI que falhe diante de dependência vulnerável**.

| Critério | pip-audit | Snyk |
|---|---|---|
| Custo | Gratuito | Camada gratuita limitada; pago acima |
| Conta / segredo | Nenhum | Conta + segredo `SNYK_TOKEN` |
| Escopo | Dependências Python | Dependências, SAST, contêineres, IaC, licenças |
| Base de vulnerabilidades | PyPA Advisory DB + OSV | Base própria da Snyk |
| Dados enviados | Só consulta a base; nada é enviado | Envia o manifesto (e o código, no Snyk Code) |
| Gate | Código de saída (`--strict`) | Checagem de PR |
| Sobreposição com o que existe | Nenhuma (preenche a lacuna) | SAST repete o CodeQL; alertas repetem o Dependabot |

**Decisão: pip-audit.** Cobre exatamente a lacuna, sem conta, sem segredo e sem custo. O ganho extra
da Snyk (base mais rica, PRs de correção) não compensa o token, a camada paga e o envio do
manifesto. Reavaliar apenas se o projeto passar a precisar de SAST multilinguagem ou de varredura de
contêineres/IaC.

## Como funciona

- `poetry export --with dev,docs` gera o lock fixado; `pip-audit --no-deps --disable-pip --strict`
  consulta as bases sem resolver nem criar venv. Audita o que o lock fixa, não o que está instalado.
- Cobre todos os grupos (principal, `dev`, `docs`).
- **CI:** passo único, no job Linux / Python 3.12. O `pip-audit` avalia os marcadores de ambiente do
  export contra o interpretador em execução, então cada perna auditaria uma fatia diferente do mesmo
  lock.
- **Local:** o hook só roda quando `pyproject.toml`, `poetry.lock` ou o script mudam, porque
  precisa de rede.

## Limitações conhecidas

- **Fatia Python 3.10 não é auditada.** O lock usa versões distintas para 3.10 (`pillow 12.3.0`,
  `filelock 4.1.0`, as últimas que o resolvedor aceita) e para 3.11+. Ambas as versões da fatia 3.10
  têm avisos abertos, sem versão corrigida compatível; são ferramentas de dev/docs, não vão no wheel.
- **Uma nova vulnerabilidade pode falhar PRs não relacionados**, já que o passo roda em todo PR. Se
  a base de avisos ficar indisponível, o passo também falha (`--strict`). A saída é corrigir a
  versão no lock ou aceitar o aviso explicitamente.

## Aceitar um aviso

Adicione o ID à lista `IGNORE_VULNS` em `bin/audit_dependencies.sh`, no formato
`"<ID>  # motivo (#issue)"`. Todo ID precisa de motivo escrito e issue de acompanhamento; a lista
começa vazia.
