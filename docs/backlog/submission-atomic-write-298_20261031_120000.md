# Write every submission writer's output atomically (#298)

- [x] `_internal/utils/atomic_write.py`: temp file in the target directory, fsync, `os.replace`, cleanup on failure
- [x] Nine writers on main routed through it (cadastro_ativos, cda, extrato, inf_fundo_157, informe_quadrimestral, lamina, informe_diario, perfil_mensal, inf_mensal_fidc); bytes and windows-1252 encoding unchanged
- [x] `tests/unit/test_atomic_write.py`: success, failure keeps old file, no temp left, same-directory temp, guard sweeping every public writer module
- [x] `docs/api.md` notes atomic output
- [ ] Writers still in open PRs adopt `atomic_write_bytes` when they merge main (the guard test fails them until they do)
