# Work ledger — #361 `atomic_write_bytes` narrows the mode before writing, not after

Branch `fix/361-atomic-write-mode-before-write`. Fecha **#361**. **Release** (toca `src/`; fix → PATCH).

- [x] Teste vermelho primeiro: `test_atomic_write_bytes_never_exposes_payload_under_wider_mode`
  (destino `0o600`, umask `022`, modo do temp lido no `fsync`) falhava com `0o644`.
- [x] `atomic_write.py`: o modo do destino existente é lido antes do `os.open` e aplicado ao temp
  (`os.chmod`) antes de qualquer byte escrito; destino novo segue `0o666 & ~umask`, sem tocar o umask.
- [x] Docstring declara a garantia de permissão.
- [x] ruff, mypy e `tests/unit/test_atomic_write.py` verdes.
- [x] Completed — kept as a record.
