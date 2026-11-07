# **Referência da API**

<script>
  // Links profundos antigos (`/<versão>/api/#PerfilMensal`) apontavam para a página única `api.md`;
  // os símbolos agora vivem em `reference/`, com as mesmas âncoras.
  if (location.hash) location.replace("reference/" + location.hash);
</script>

A interface pública, agrupada pela divisão de topo do próprio código: `filings_cvm.submission`
(envio → CVM) e `filings_cvm.ingestion` (leitura ← CVM).

> **Veja também:** [Uso](../usage.md) · [Exemplos](../examples.md)

## Páginas

| Grupo | Conteúdo |
|-------|----------|
| [Referência](reference.md) | Cada símbolo público: serializadores (`submission`) e leitores (`ingestion`, por raiz do portal) |

## Crescendo esta seção

Esta seção é um **diretório, e não uma página única**, de propósito. A referência da API cresce a
cada unidade publicada; uma `api.md` única vira a maior página do repositório, e dividi-la depois
**apodrece todo link profundo já publicado** — para sempre, quando a documentação versionada
(`mike`) está no ar, pois `/<versão>/api/#âncora` existe eternamente.

Ao adicionar páginas:

- **Agrupe pela divisão de topo do próprio código** — nunca invente uma taxonomia paralela. Quem
  conhece o pacote adivinha a URL, e a documentação não se afasta da estrutura que espelha.
- **A profundidade segue a contagem, não o gosto.** O eixo real escolhe as seções; só o volume
  decide se uma seção precisa de um segundo nível.
- A prosa compartilhada por um grupo vive uma vez, na página do grupo.
- **Registre toda página nova no `nav:` do `mkdocs.yml` no mesmo commit.** O MkDocs publica a
  página mesmo sem registro — ela só some da navegação, e é isso que o gate
  `bin/check_docs_sections.py` existe para pegar.
- A entrada de cada novo leitor ou serializador entra em [`reference.md`](reference.md) (ou em uma
  página irmã neste diretório) — **nunca** em um `docs/api.md`, que não existe mais.
