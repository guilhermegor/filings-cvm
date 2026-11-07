# CLAUDE.md — .specs/

This file guides Claude Code (and any other agent) when reading or writing inside
`.specs/` — the repo-root home for feature design specs, implementation plans, work
trackers and PR bodies. `docs/` is solely for published documentation; working material
lives here.

## Layout

```
.specs/
├── CLAUDE.md          # this file
├── features/
│   └── <feature-name>/
│       ├── design.md  # what and why — the feature spec (template below)
│       ├── plan.md    # how (optional — not every design reaches a plan)
│       ├── tasks.md   # the feature's work tracker (optional)
│       └── pr.md      # the PR body (optional); pr-<N>-<slug>.md when a feature has several
├── backlog/
│   └── <kebab-topic>_YYYYMMDD_HHMMSS.md   # tracker for an effort spanning no single feature
└── _lessons/          # generated, git-ignored, free-form
```

## Rules

`bin/check_specs_structure.sh --root .` enforces every rule below; it runs in the
`specs-structure` pre-commit hook and in CI. Nothing here is advisory except where marked.

- Nothing lives directly under `.specs/` besides `CLAUDE.md`, `features/`, `backlog/` and
  `_lessons/`. A stray top-level note fails by name.
- `<feature-name>` is kebab-case with at least one letter — not a date, not an issue number.
- `features/` splits on **lifecycle, not change type**. A feature directory named after a
  type (`bugfix/`, `chore/`, `feat/`, `fix/`, `docs/`, `refactor/`, ...) fails: the type is
  already in the branch name and the Conventional-Commit prefix. A name that merely contains
  one (`bugfix-triage`) is a feature and passes.
- A `features/<name>/` directory holds at least one of `design.md`, `plan.md` or `tasks.md`.
- `pr.md` is the PR body; several PRs use `pr-<N>-<kebab-slug>.md`, where `<N>` is an
  ordinal inside the feature, not the PR number (the body exists before the number does).
  Both are recognized but never sufficient on their own. Any other `pr...md` name fails.
- `tasks.md` task lines use `- [ ]` (to-do), `- [~] <type>/<name>` (in progress on that
  branch) or `- [x]` (done). `[~]` carries a branch, never an agent id. A marker is a claim,
  not evidence; the gate cannot check that the branch exists (advisory).
- `backlog/` is flat; every file is named `<kebab-topic>_YYYYMMDD_HHMMSS.md`.
- A tracker is never deleted when done: tick the last box and add a short
  "Completed — kept as a record" note.

## Feature spec template (`features/<feature-slug>/design.md`)

Fill it in before writing code. Delete a section that genuinely does not apply — an empty
heading reads as an unanswered question, not a skip. Ids are sequential within the file.

```markdown
# <Feature name>

Status: draft
Owner: <name>
Created: YYYY-MM-DD

## Objective
<One or two sentences: the outcome, not the implementation.>

## User Stories
- US-001: As a <role>, I want <capability>, so that <benefit>.

## Acceptance Criteria
Given/When/Then, one per testable behavior, naming the story it satisfies.
- AC-001 (US-001): Given <context>, when <action>, then <outcome>.

## Assumptions
- ASM-001: <taken as given but not verified>.

## Open Questions
- Q-001: <blocks or shapes the design and has no answer yet>.

## Out of Scope
- <behavior this feature deliberately does not have>.

## Notes
Links to related issues and prior art.
```
