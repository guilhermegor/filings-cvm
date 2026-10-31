# Balancete COFI 4010 writer (#23)

Branch: `feat/cofi-balancete-writer-23` · Issue: #23

## Por que existe

`PadraoXMLBalancete.asp` nao define XML; o envio e um arquivo largura fixa COFI 4010
(`PadraoCOFI.aspx`). O dono re-escopou a issue para um writer COFI 4010.

## Feito

- [x] Camada de registros COFI compartilhada (`_internal/utils/cofi_records.py`).
- [x] Schema `balancete.py` e writer `submission/balancete.py`.
- [x] Testes por posicao de cada registro, validacoes e escrita atomica.
- [x] Docs, nav, api.md, catalogo do CLAUDE.md.

## Fora do escopo

- COS 4010 (BACEN) e as criticas de consistencia da CVM.
