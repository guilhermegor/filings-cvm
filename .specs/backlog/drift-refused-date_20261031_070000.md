# Treat a refused probe date like a 404 in the drift check

- [x] Reproduced: `PerfilMensalReader` refuses 202311 (before its series start) with `ValueError`, and `check_real_header` let it escape, so the sweep reported "header check errored" for a reader that was fine
- [x] `check_real_header` now skips a refused date and tries the next; it re-raises only when every date was refused and none was merely unpublished
- [x] Regression tests: one refused date among 404s is "no artifact found"; every date refused still reports

Completed — kept as a record.
