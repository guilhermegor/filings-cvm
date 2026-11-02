# **Registro de incidentes**

O que quebrou neste projeto e o que mudou para não quebrar de novo daquela forma. Esta página
mantém o conhecimento de depuração dentro do repositório, e não no histórico do git ou na memória
de uma pessoa.

> **Veja também:** [Uso](usage.md) · [Contribuindo](contributing.md) · [Histórico de versões](changelog.md).

## Não é um ADR

Um **ADR** registra uma decisão tomada *antes* de algo dar errado. Um incidente documenta uma
decisão tomada *porque* algo já deu errado: gatilho e público diferentes.

## Publicada de propósito: redija antes de escrever

Esta página vai para o site publicado. Remova hostnames, consultas e qualquer detalhe de produção
antes de commitar a entrada.

## Formato

Cinco campos, nesta ordem, cada um com poucas frases.

- **Sintoma**: o que foi observado, não o que estava errado.
- **Como foi encontrado**: a ferramenta, a consulta ou o acaso que revelou.
- **Causa raiz**: medida, não presumida.
- **A mudança**: o que torna esta classe de falha impossível ou barulhenta.
- **Como saberíamos que regrediu**: o gate ou teste que pegaria a volta.

---

## Leitor apontado para o membro errado passava na suíte inteira

**Sintoma.** No DFP, um leitor de `DRE_con` que lia o arquivo `DRE_ind` devolvia um DataFrame
válido, com os tipos certos, e o contrato passava.

**Como foi encontrado.** Por mutação deliberada: trocar o membro lido e rodar a suíte inteira, que
continuou verde.

**Causa raiz.** Os 16 membros de demonstração do DFP colapsam em apenas 3 listas de colunas e são
idênticos entre si. Um teste que só confere colunas e tipos não consegue distinguir `con` de `ind`.

**A mudança.** Um teste de identidade do membro: cada membro sintético se identifica numa coluna, e
o leitor só passa se devolver o membro que pediu.

**Como saberíamos que regrediu.** A mesma mutação (trocar o membro lido) deixa o teste de
identidade vermelho.

## Workflow com gatilho inexistente: nenhum run, nenhum aviso

**Sintoma.** Um PR ficou sem rótulos e sem o comentário do gate. Parecia um gate lento, mas era um
gate morto.

**Como foi encontrado.** Pela mensagem "This run likely failed because of a workflow file issue" na
aba Actions, não por nenhum check do PR.

**Causa raiz.** `pull_request_review_thread` é um evento de webhook, não um gatilho de workflow. O
GitHub rejeitou o arquivo inteiro, e o `yamllint` considerava o arquivo válido.

**A mudança.** O `actionlint` passou a validar tudo em `.github/workflows/` (`bin/lint_actions.sh`),
no hook e no passo de CI.

**Como saberíamos que regrediu.** O `actionlint` falha com `unknown Webhook event` ao ver o gatilho.
