# Probe every closed series in the contract-drift job (#321)

- [x] Measured on origin/main: `PerfilMensalPre175Reader` and `ExtratoFiPre2020Reader` refuse every rolling probe date with `ValueError`
- [x] Both added to `_CLOSED_SERIES_PROBES` (202311 and 2019), pinned by `test_closed_series_readers_are_probed_at_their_last_published_month`
- [x] Sweep test over every public reader: the first date the drift job passes must construct it
- [ ] Mutation-proved: removing either entry fails both tests
- [ ] Report-only drift run: both headers are now actually checked
- [ ] Open, not in scope: `PerfilMensalReader` (series from 202312) refuses the oldest rolling date (`today - 1095 d` = 202311 until early Dec 2026). It only bites if the six newer periods all 404, then the job logs "errored" instead of "skipped"
