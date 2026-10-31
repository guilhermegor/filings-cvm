# Work ledger — #28 Informe Anual de Auditor submission writer

Branch `feat/informe-anual-auditor-writer-28`. Spec: `PadraoXMLAuditorAnual.asp` (fetched 2026-10-31).

- [x] Confirmed no writer for this standard on `origin/main` (only the CAD ingestion reader).
- [x] Schema `_internal/config/schemas/informe_anual_auditor.py` (models only).
- [x] Validators `_internal/utils/xml_fields.py` (copied from #291) and `xml_fields_digits.py` (CPF, CEP, e-mail).
- [x] Writer `submission/informe_anual_auditor.py` (encodes to bytes before touching the target file).
- [x] Names registered in `submission/__init__.py` (sorted `__all__`).
- [x] Unit tests: XML of every block, every rule, failed export leaves target intact.
- [ ] `docs/submission/informe_anual_auditor.md`, `mkdocs.yml` nav, `docs/api.md`, `CLAUDE.md` catalog.
- [ ] Merge `origin/main`, PR (`Closes #28`).

## Assumptions (stated on the docs page and in the PR)

- Page states 2 decimals for VL_AUDIT, PR_AUDIT, PR_FATURA: used 2, truncated.
- The page contradicts itself: the tag list says the tag of the pessoa block is TREINA_PESSOA but
  also says "AIPF"/"AIPJ" job codes by person type; cargo 4 for PF, 1-3 for PJ is enforced.
- DS_NOME of audited entity has no stated limit: assumed 100.
- Namespace `urn:audtanual` from the sample.
- No CVM validator was run.
