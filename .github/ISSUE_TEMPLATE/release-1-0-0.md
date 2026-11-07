---
name: Cut 1.0.0
about: The blocked path to the first stable release
title: "Cut 1.0.0"
labels: ["state:blocked"]
---

<!--
issue-template-guard: require "**Blocked by:**" if-label state:blocked
-->

**Blocked by:** decision: every other open issue is implemented or labelled `post-1.0`; re-read the open list before starting

## What / Why

1.0.0 is the moment this library promises its public API. The version policy changes from
0.x rules (breaking is a MINOR, feat and fix are a PATCH) to full semver. The release
workflow refuses a 0.x to 1.0.0 jump while an open issue lacks the `post-1.0` label; see
`docs/releasing-1-0-0.md`.

## Checklist

- [ ] **Queue empty:** every remaining issue is implemented, or labelled `post-1.0` by the owner, never silently dropped
- [ ] **Docs audit against the code:** README, CONTRIBUTING, SECURITY, CHANGELOG, everything under `docs/` (minus historical ledgers), every `CLAUDE.md` and `AGENTS.md`, issue and PR templates, the docs-site nav and the public-API docstrings. Every count, path, import example and status mark is re-measured from the code, never incremented by hand
- [ ] **Runnable examples:** each README and usage example runs, or is covered by a doctest or a test
- [ ] **SECURITY.md** gains a supported-versions table for 1.x
- [ ] **Release:** rehearsal, then publish, then install-verify (Test PyPI then PyPI), with the tag present and the release not a draft
- [ ] **Post-release:** switch the documented version policy from 0.x rules to full semver
