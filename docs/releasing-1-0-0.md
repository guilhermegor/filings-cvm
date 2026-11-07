# Lançamento do 1.0.0

O 1.0.0 é o momento em que esta biblioteca promete a sua API pública. Até lá valem as regras
do 0.x: uma mudança incompatível é um MINOR, uma funcionalidade ou correção é um PATCH. A
partir do 1.0.0 vale o semver completo. Duas coisas precisam ser verdade nesse momento e são
fáceis de errar à mão: o backlog está concluído e a documentação descreve o código que de fato
é publicado.

## O caminho

1. Abra a issue **Cut 1.0.0** a partir do modelo de issue. Ela nasce `state:blocked`,
   bloqueada por todas as outras issues abertas.
2. Conclua o backlog. Uma issue que não entrará no 1.0.0 recebe o rótulo `post-1.0`,
   aplicado pelo mantenedor (crie-o uma vez com `gh label create post-1.0`), de modo que fique
   adiada no registro em vez de descartada.
3. Percorra o checklist da issue: auditoria da documentação, exemplos executáveis, a tabela de
   versões suportadas 1.x em `SECURITY.md`, e então o ensaio e a publicação.
4. Depois do lançamento, passe a política de versão documentada para o semver completo.

## O portão de release

O workflow de release executa `bin/check_release_gate.py` antes de publicar. Ele só se aplica
quando o MAJOR pedido é pelo menos 1 e a última versão final publicada (sem pré-releases nem releases retiradas) é 0.x. Nesse caso lista as
issues abertas e falha enquanto alguma não tiver o rótulo `post-1.0`, nomeando cada uma.

- Pull requests não contam, nem a própria issue **Cut 1.0.0**.
- As issues são lidas pela API REST do GitHub com o token do workflow, somente leitura.
- Se a API não puder ser lida, o portão falha fechado: bloqueia o release em vez de adivinhar.
- Qualquer outro incremento, como 0.4.0 para 0.5.0 ou 1.0.0 para 1.0.1, não é afetado.
- Uma primeira publicação conta como vinda de 0.0.0, então um projeto cujo primeiro release é
  o 1.0.0 também passa pelo portão.

Para passar, conclua cada issue listada ou rotule-a `post-1.0` e execute o workflow de novo.
