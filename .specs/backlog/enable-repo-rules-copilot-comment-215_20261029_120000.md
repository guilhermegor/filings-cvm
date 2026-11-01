# Work ledger — #215 comentário falso sobre o Copilot em enable_repo_rules.sh

Branch `fix/enable-repo-rules-copilot-comment-215`. Fecha **#215**. Sem release (`ci`, zero diff em `src/`).

## O que estava em jogo

`bin/enable_repo_rules.sh` dizia que `required_review_thread_resolution` torna vinculantes os
comentários do Copilot. Falso: a regra vale para todo thread inline (hoje, os do CodeRabbit) e o
`copilot_code_review` é inerte nesta conta (restrição do plano). O PR #214 corrigiu só a documentação.

## Feito

- [x] Comentário reescrito descrevendo a regra pelo que ela faz, sem atribuí-la a uma ferramenta,
  e apontando que o `copilot_code_review` é inerte.
- [x] O script não foi executado (ele altera as regras do repositório no GitHub).
- [x] Hooks de pre-commit verdes.

Completed — kept as a record.
