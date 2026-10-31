# Work ledger — #22 COFI 4016 Balanço writer

Branch `feat/cofi-balanco-writer-22`. Spec: `PadraoXMLBalanco.asp` (no XML) -> `PadraoCOFI.aspx`.

- [x] Confirmed no Balanço writer on `origin/main`; found the page defines no XML (COS/COFI 4016 upload only).
- [x] Owner re-scoped #22 to the COFI 4016 fixed-width writer.
- [x] Shared record layer `_internal/utils/cofi_records.py`; plan `cofi_plan.py`; checks `balanco_checks.py`.
- [x] Schema `schemas/balanco.py` (models only), writer `submission/balanco.py`, names registered.
- [x] Tests, docs page, nav, api.md, CLAUDE.md catalog.
- [ ] PR (`Closes #22`).

## Assumptions (stated in the PR)

- Amount scale 2 implied places, truncated; the page states none.
- Check digit mod 10, weights 3,1,7: fitted to and verified on all 479 plan accounts, not stated by CVM.
- CRLF line ends, ASCII default, EBCDIC cp037 optional; zero written `+`.
- E5/EX/G1 on the total column; D2 not implemented; COS 4016 not implemented.
- No CVM validator was run.
