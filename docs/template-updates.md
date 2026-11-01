# Atualizações do template

Um scaffold é uma cópia única. Uma correção que entra em `templates/` depois disso só chega aos
projetos gerados depois dela. `python bin/check_template_drift.py` é o relator que fecha essa
lacuna (blueprintx#872).

## O que ele compara

Para um projeto carimbado com `tier` e `blueprintx_commit` em `.blueprintx-provenance.yaml`,
existem três versões de cada arquivo gerenciado pelo template:

| Nome | De onde vem |
|---|---|
| base | o arquivo do template no `blueprintx_commit` carimbado |
| theirs | o arquivo do template no checkout do BlueprintX agora |
| ours | o arquivo do projeto |

O conjunto de arquivos gerenciados nunca é listado à mão. A entrada de scaffold de cada tier
responde a `--list-copies` executando em modo simulado os seus próprios passos de cópia
(`bin/lib/scaffold_python_templates.sh` para os tiers de serviço, `bin/scaffold/python_lib_minimal.sh`
para o lib-minimal) e imprimindo uma linha `COPY` ou `RM` por cópia. A simulação substitui `cp`,
`rm`, `mkdir`, `touch`, `chmod`, `envsubst` e `print_status` por meio de `scaffold_dry_run` em
`bin/lib/scaffold_provenance.sh`, de modo que a saída não pode divergir do que o scaffold faz.

A simulação aceita `--roster true|false` para corresponder à escolha do projeto sobre o roster de
bots de revisão, e limpa `GITGUARDIAN_API_KEY` para que a saída nunca dependa do ambiente de quem
chama. Arquivos renderizados em vez de copiados (`README.md`, `pyproject.toml`) não aparecem. O CI
do próprio BlueprintX gera cada tier de verdade e falha quando `--list-copies` e a árvore gerada
divergem.

## O que ele reporta

- Ausente: o template entrega um caminho que o projeto não tem.
- Template mudou desde o scaffold: ours é igual a base e theirs difere.
- Ambos mudaram: ours e theirs diferem de base e entre si.
- Não comparado: o projeto tem o arquivo, mas a fonte no checkout do BlueprintX não é um arquivo
  (por exemplo, foi apagada localmente); a execução não prova nada sobre ele e nunca termina em
  veredito limpo.

Um arquivo que o projeto editou enquanto o template ficou parado não é deriva. Quebras de linha
CRLF (checkout com `core.autocrlf`) não contam como edição: o texto é normalizado para LF antes de
comparar; conteúdo binário não é alterado. Arquivos que o scaffold renderiza com `envsubst`
(`pyproject.toml`, `LICENSE`, `README.md`, `SECURITY.md`) não são cópias literais e ficam fora da
comparação, assim como os arquivos copiados de `bin/ci/`. Cópias condicionadas a uma resposta dada
no scaffold (o roster de bots de revisão) são listadas exatamente quando a simulação recebe o valor
correspondente, lido do carimbo. As demais cópias condicionadas (chave do GitGuardian, destinos de
publicação) ainda não são policiadas. Um arquivo ausente no commit carimbado que o projeto escreveu
por conta própria é reportado como "ambos mudaram", a menos que o conteúdo já seja igual ao template
atual, caso em que é "igual".

## Por que ele se auto-ignora

Cada pré-requisito que falta tem a sua própria saída, e nenhuma delas é um veredito limpo:

- Sem carimbo (`.blueprintx-provenance.yaml`) ou sem checkout do BlueprintX, a ferramenta imprime uma
  linha `SKIPPED: ...` genérica explicando o que falta e encerra antes de qualquer comparação.
- Com checkout e carimbo, mas com `blueprintx_commit` ausente, `unknown` ou fora do histórico de
  `HEAD` do checkout (um commit divergente ou mais novo que o checkout não serve de base de
  mesclagem), a seção de conteúdo imprime `SKIPPED content drift` e diz o motivo. A verificação de
  caminhos ausentes ainda roda.

A ferramenta sempre encerra com 0.

## Aplicando atualizações: `python bin/template_update.py`

`python bin/template_update.py` lê os mesmos dados base, ours e theirs e age sobre eles. É uma
simulação, a menos que `--apply` seja passado. O checkout vem de `--blueprintx-root` ou de
`BLUEPRINTX_TEMPLATE_ROOT`, como no relator, e a resolução dos caminhos gerenciados é reaproveitada
(`managed_sources` em `bin/check_template_drift.py`).

| Arquivo do projeto | Ação |
|---|---|
| ausente | adiciona, com o modo de arquivo do template |
| igual a base | avança (fast-forward) para theirs |
| igual a theirs, ou theirs igual a base | nada a fazer |
| editado localmente e o template também mudou | `git merge-file` base, ours, theirs |
| um diretório no lugar do arquivo | listado como não mesclável e deixado intacto |

Uma mesclagem limpa é escrita como está. Um conflito é escrito com marcadores `<<<<<<< ours`,
`=======` e `>>>>>>> template` e listado na saída. Um arquivo que o git não consegue mesclar
(conteúdo binário, ou o `git merge-file` encerrado por sinal) é listado como não mesclável e
deixado intacto. Uma edição local nunca é sobrescrita em silêncio, e um arquivo cuja base é
desconhecida (adicionado ao template depois do commit carimbado) é mesclado contra uma base vazia,
de modo que uma cópia local diferente aparece como conflito.

`--apply` primeiro confere que `--root` é a raiz de uma árvore de trabalho git (um projeto dentro de
outro repositório não tem o HEAD desse repositório movido) e então executa
`git switch -c chore/template-update-<short-sha>`, em que o sha curto é o HEAD do checkout. Nunca
escreve na branch em que você estava e para antes de alterar qualquer coisa quando a branch não pode
ser criada. Depois escreve os arquivos e os deixa sem commit para revisão. `blueprintx_commit` no
carimbo passa para o HEAD do checkout somente quando todos os arquivos foram aplicados sem
pendências; após um conflito o carimbo não muda e a ferramenta encerra com 1, de modo que resolver os
marcadores e rodar de novo continua a partir da mesma base.

Sem carimbo, checkout ou `blueprintx_commit` utilizável (inclusive um commit que não é ancestral do
HEAD do checkout), a ferramenta imprime `SKIPPED update` (ou o `SKIPPED` do relator) e encerra com 0
sem tocar no projeto.

### Tentando de novo após um conflito

Rode `python bin/template_update.py --apply` outra vez enquanto a branch de atualização continua em
checkout. A branch é reaproveitada, arquivos já escritos não são reescritos, e um arquivo
conflitado ou mesclado conta como resolvido assim que não tem linha de marcador `<<<<<<<` ou
`>>>>>>>`. Só então `blueprintx_commit` avança. Um arquivo não mesclável continua bloqueando até ser
tratado à mão.

Retomar só vale quando uma execução anterior registrou que escreveu o plano (um arquivo
`template-update-<short-sha>.written` dentro do diretório `.git`). Uma branch de mesmo nome sem esse
registro (execução interrompida ou criada à mão) recebe o plano completo, para que mesclagens não
escritas nunca sejam puladas e carimbadas como aplicadas.

`--apply` também recusa um checkout do BlueprintX com alterações não commitadas ou não rastreadas,
porque theirs é lido da árvore de trabalho enquanto o commit carimbado vem do histórico.

## Neste repositório

O filings-cvm carrega um carimbo (`.blueprintx-provenance.yaml`, tier `lib-minimal`). As tarefas poe
`template_drift` e `template_update` chegam com a migração para o poe; até lá, rode os scripts
diretamente, apontando para um checkout do BlueprintX com `--blueprintx-root` ou com a variável de
ambiente `BLUEPRINTX_TEMPLATE_ROOT`:

```bash
python bin/check_template_drift.py --root . --blueprintx-root ~/github/blueprintx
python bin/template_update.py --root . --blueprintx-root ~/github/blueprintx   # dry run
```

`blueprintx_commit` no carimbo não é o commit do qual o repositório foi literalmente gerado. Foi
escolhido por medição: o commit do BlueprintX em que os arquivos do template que ninguém aqui tocou
ainda são iguais às cópias do projeto, de modo que "template mudou" e "ambos mudaram" sejam
classificados corretamente. Apenas `tier` e `review_bot_roster` são respostas de scaffold que o
carimbo registra.

### Limites conhecidos

- As ferramentas reportam apenas arquivos que o template ainda entrega. Não listam arquivos que o
  projeto tem e que o template removeu ou substituiu (`Makefile`, `tasks.sh`, `bin/db.sh`,
  `docs/api.md`).
- Arquivos renderizados (`pyproject.toml`, `README.md`, `mkdocs.yml`, `SECURITY.md`, `LICENSE`) e as
  cópias de `bin/ci/` ficam fora da comparação.
- A árvore do pacote vendorizado aparece sob o nome de espaço reservado do tier, `src/project/...`;
  neste repositório, todo o `src/` é reportado como ausente. Ignore essas linhas.
- Respostas de scaffold além do roster de bots de revisão não são registradas no carimbo.
