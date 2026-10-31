---
name: Task
about: One unit of work, with its acceptance criteria and declared file surface.
title: ""
labels: []
---

<!--
Required when the issue carries the `state:blocked` label:
  - a `**Blocked by:**` line naming each blocker: an issue ref (`repo#N`) where one exists, or
    `decision: …` when the blocker is a choice nobody has made yet. "Blocked" with no named
    blocker is not a status, it is a question the board cannot answer.
    Mirror same-repo blockers as native relationships too, and fill the board's "Blocked by"
    field.

Machine-readable form of the rule above, read by the guard (keep it on one line):
issue-template-guard: require "**Blocked by:**" if-label state:blocked
-->

## Objetivo

<O que muda, e por quê.>

**Blocked by:** <repo#N, repo#N, or decision: …>   ← delete this line unless labelled state:blocked

## Critério de aceite

- <Condição verificável.>

## File surface
```surface
<one path per line>
```
