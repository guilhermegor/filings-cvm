# Security Policy

## Supported versions

`filings-cvm` is published on [PyPI](https://pypi.org/project/filings-cvm/) and is still in
the `0.x` series, where **every release is a minor bump** and only the newest one receives
fixes. Always upgrade to the latest release before reporting — a fix will not be backported
to an older `0.x` line.

| Version | Supported |
|---------|-----------|
| latest `0.x` (newest release on PyPI) | ✅ |
| any older release | ❌ |

## Reporting a vulnerability

**Please do not open a public issue for a security vulnerability.** Public issues disclose the
problem before a fix exists.

Instead, use **GitHub's private vulnerability reporting** for this repository:

1. Go to the [**Security** tab](https://github.com/guilhermegor/filings-cvm/security).
2. Click **Report a vulnerability** (this opens a private GitHub Security Advisory visible only
   to you and the maintainers).
3. Describe the issue, the affected version, and a reproduction if you have one.

You will get an acknowledgement on a **best-effort basis within 7 days**. If a report is
confirmed, a fix ships in a new release and a GitHub Security Advisory is published crediting the
reporter (unless anonymity is requested).

## Scope

This is a **read-only ingestion / file-standard library**: it downloads and parses public CVM
open-data artifacts (`.zip`/`.csv`/`.xlsx`) and serialises submission XML. Security-relevant
issues therefore include:

- **In scope** — parser-level flaws reachable from an untrusted CVM artifact: zip-bomb /
  decompression-bomb resource exhaustion, unbounded memory on a crafted CSV, path traversal on
  archive extraction, ReDoS in a validator, or a dependency with a known CVE that this library
  pulls in.
- **Out of scope** — the security of a **consumer's own** deployment (datalake credentials,
  object-store configuration, the network they fetch over), the availability or correctness of
  CVM's own servers, and social-engineering or physical attacks. These are not properties this
  library controls.

## What this library does not do

- It ships **no runtime secrets** and reads **no `.env`** — a distributable library has no
  runtime environment to seed, so there is no credential surface here to compromise.
- It performs **no code execution** on ingested data — files are parsed into typed DataFrames,
  never `eval`'d or executed.
