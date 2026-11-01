# Graphite Configuration

Graphite has no repo-level config file (no `.graphite.yaml`). Everything below is either one
versioned file or a dashboard step the repository owner performs by hand.

## What the repository versions

- `.gitattributes` marks lockfiles and the coverage badge `linguist-generated=true`. The
  comment-budget baseline is deliberately not marked: it is a ratchet, and a reviewer must
  see its count go up. Per Graphite's docs, marked files are collapsed in the Graphite
  and GitHub diff views, skipped by the AI review and excluded from its PR size check. They
  are collapsed for every reviewer and human too.
- The review rules are the existing `.greptile/rules.md`. There is no `.graphite/` copy.

## Dashboard steps (not versionable)

1. Install the Graphite GitHub App on the account (personal accounts: *Join team*), then
   sync the repository.
2. AI reviews, enable the repository.
3. Rules & exclusions, add a file-based rule with the glob `.greptile/rules.md`
   (globs are case-sensitive; large files are truncated).
4. Settings tab (org-admin rights required), PR filtering by **PR labels**: restrict AI
   reviews to PRs carrying `review:graphite`.

## Never auto-review

Graphite reviews every new PR by default. The label filter in step 4 is the opt-in: the
`/dev-loop` ladder adds `review:graphite` when it is Graphite's turn and removes it once the
review lands. A label left on lets every push trigger another review.

## Measured behavior

Measured on blueprintx#807, 2026-10-16.

- Adding the label is enough. At 10:25:13 UTC the label was added to head `8912317c` with no
  push and no comment; about 76 s later Graphite reported the check run
  `Graphite / AI Reviews` (app `graphite-app`): success, "AI review ran and left 0 comments".
- A clean review leaves no PR review and no comment. The check run is its only trace, so a
  review-thread gate that counts reviews sees nothing.
- Without the label, nothing runs. Heads `ac0f9231` and `5d3e1fde`, pushed while the label
  was absent, each got the check run `Graphite / AI Reviews` with conclusion `skipped` ("does
  not match your org's AI review filters") and zero reviews.

Login measured on 2026-10-17 (probe PR with deliberate defects, label `review:graphite` added at
21:43:12 UTC): about 67 s later `Graphite / AI Reviews` reported "AI review ran and left 2
comments", and `graphite-app[bot]` (type `Bot`) submitted a `COMMENTED` review carrying 2 inline
review comments. So `.review-bots.yaml` lists it as `posts: threads`. A draft PR got nothing in
10 minutes, so the label only works on a PR that is ready for review.
