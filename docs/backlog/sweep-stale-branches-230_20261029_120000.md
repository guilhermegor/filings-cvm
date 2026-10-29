# Weekly per-branch sweep (#230)

Branch: `ci/230-sweep-stale-branches` · Issue: #230 · Backstop to `reconcile-merged-prs.yaml`

## Feito

- [x] `bin/sweep_stale_branches.py`: criterio `PR state == MERGED` por `headRefName` (nunca
  ancestralidade — o repo squash-merge); pura `branch_verdict`/`branches_to_delete`/`is_dry_run`,
  efeitos so em `main()`.
- [x] Guardas: nunca default/`gh-pages`; nunca branch com PR `OPEN`; sem PR ou so `CLOSED` fica.
- [x] Dry run por padrao (`SWEEP_DRY_RUN`); o workflow aplica no `schedule`, dispatch padrao e dry.
- [x] Relata quantas branches examinou (nunca sai 0 em silencio).
- [x] `.github/workflows/sweep-stale-branches.yaml`: semanal + dispatch, concurrency group
  `reconcile-merged-prs` compartilhado.
- [x] Testes unitarios, incluindo controle negativo e guardas.
- [x] Completed — kept as a record.
