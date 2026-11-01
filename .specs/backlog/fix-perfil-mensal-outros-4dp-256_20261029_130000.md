# Perfil Mensal VAL_PERCENT_OUTROS com quatro casas decimais (#256)

Branch: `fix/perfil-mensal-outros-4dp-256` · Issue: #256 · Sequel de #245 / PR #255

## Por que existe

A pagina `PadraoXMLPerfilV4.asp` descreve `VAL_PERCENT_OUTROS` como "Numerico com quatro casas
decimais". O schema o declarava `TwoDecimalField` e o writer renderizava com 2 casas, truncando
valores em silencio.

## Feito

- [x] Reproduzido em `origin/main` (schema `VarOutros.val_percent_outros`, writer com escala `2`).
- [x] Pagina da CVM lida (ISO-8859-1): quatro casas confirmadas.
- [x] `val_percent_outros` usa `FourDecimalField`; a tag renderiza com 4 casas.
- [x] Testes: truncamento (positivo, negativo, `0.99999`) e XML renderizado (`2` -> `2,0000`).
- [x] Mutacao: revertendo a fonte, os testes novos falham; restaurada e verificada por sha256.
- [x] `docs/submission/perfil_mensal.md` atualizado.
- [x] Gates de pre-commit.

Completed — kept as a record.
