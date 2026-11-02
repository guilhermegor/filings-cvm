# **Atualizações do template**

Este projeto nasceu do template `python-common` do BlueprintX. Um scaffold é uma cópia única: uma
correção que entra no template depois só chega a quem foi gerado depois dela. Este repositório
**não** carrega o carimbo de proveniência (`.blueprintx-provenance.yaml`) nem a tarefa `poe` que
compara com o template, então a atualização é manual e deliberada.

> **Veja também:** [Contribuindo](contributing.md) · [Registro de incidentes](incidents.md).

## O que já foi importado

Cada importação é uma issue própria, com um gate no pre-commit **e** um passo no CI (paridade de
gates, descrita em `.github/CLAUDE.md`).

| Issue | O que veio do template |
|---|---|
| #294 | guards de qualidade de código e de testes, com o catraca `bin/quality_ratchet.py` |
| #295 | guards de documentação (`check_docs_code_refs.py`, `check_docs_gap.py`), de higiene (`check_identifier_masking.py`, `check_clean_index.sh`, `check_secrets.sh`) e o workflow `secret_scan.yaml` |
| #296 | workflows de revisão (`review_threads`, `review_retry`, `coderabbit_trigger`) |

O `pr-reconcile.yaml` do template **não** foi importado: duplica o `reconcile-merged-prs.yaml`
deste repositório, e dois reconciliadores competiriam pelas mesmas issues e branches.

## Como trazer uma correção nova do template

1. Compare o arquivo do template com o do repositório e leia o que mudou.
2. Ajuste aos nomes deste projeto (`filings_cvm`, o `src/` e os caminhos reais).
3. Rode o guard na árvore atual. Ele precisa passar sem afrouxar a regra. Só os guards envolvidos por
   `bin/quality_ratchet.py` (function-length, complexity, dead-code, all-exports, one-assert) usam
   `bin/quality_baseline.txt`: o que já existia no `main` entra nessa linha de base, nunca o código
   novo. Os guards de documentação e de higiene não leem essa linha de base; corrija as violações
   existentes antes de registrar o gate.
4. Registre o gate em `.pre-commit-config.yaml` e em `.github/workflows/tests.yaml` no mesmo commit.
5. Escreva só ASCII na saída dos scripts: o CI roda no Windows, cujo console falha ao imprimir
   símbolos como `✓`.
