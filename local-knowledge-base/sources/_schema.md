---
title: Source record schema
---

# Source record schema

Each source file in this directory represents a single whitelisted URL or
document. The Layer 2 (trusted source check) pipeline loads this directory at
startup and only searches sources listed here (or `.gov` fallback if enabled).

| Field | Required | Purpose |
|---|---|---|
| `id` | yes | Unique kebab-case identifier (used for `[[wiki-links]]` from facts) |
| `domain` | yes | Bare domain (`python.org`, not the full URL) |
| `url` | yes | Canonical URL to fetch |
| `category` | yes | Domain tag, matches the categories used in fact entries |
| `added_on` | yes | ISO-8601 date the source was added to the whitelist |
| `last_verified` | yes | ISO-8601 date the source was last reachable + still authentic |
| `status` | yes | `authentic` \| `deprecated` \| `disputed` |

## Governance

Adding a source requires a maintainer's review (see PLAN.md §6). PRs that add
sources must include:

1. Justification for why the source is trustworthy.
2. At least one fact entry in `../facts/` linking to the new source.
3. A note on how often the source should be re-verified.