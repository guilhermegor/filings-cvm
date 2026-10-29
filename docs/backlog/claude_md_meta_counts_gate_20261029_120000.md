# Gate the root CLAUDE.md META counts (#161)

- [x] Confirm not already done at `origin/main` (the gate only covered `docs/ingestion/meta.md`)
- [x] Measure the real numbers from the code (48 readers = 19 .txt + 29 .zip, 48 contracts); CLAUDE.md was already right
- [x] Add `test_claude_md_meta_counts_match_the_real_numbers`, every expected value derived from the package
- [x] Prove it bites: mutated `48 readers` and `48 = 19` in CLAUDE.md, test went red; restore verified by sha256
- [x] Update the CLAUDE.md provenance note to say this paragraph is now gated
- [x] Completed — kept as a record.
