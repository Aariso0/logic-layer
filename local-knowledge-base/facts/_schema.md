---
id: schema-fact
title: Fact entry schema
---

# Fact entry schema

Each fact file in this directory follows the same structure so the verification
pipeline can parse entries uniformly. Required + optional frontmatter fields:

| Field | Required | Purpose |
|---|---|---|
| `id` | yes | Unique kebab-case identifier (used for `[[wiki-links]]`) |
| `claim` | yes | The atomic factual claim, written as a plain sentence |
| `category` | yes | Domain tag (e.g. `programming-languages`, `history`, `science`) |
| `confidence` | yes | `high` \| `medium` \| `low` — curator's assessment |
| `status` | yes | `verified` \| `stale` \| `disputed` — refreshed by the scheduler |
| `last_verified` | yes | ISO-8601 date of last successful source check |
| `source` | recommended | Wiki-link to a record in `../sources/` |

Body rules:

- One atomic claim per file.
- Cross-link generously with `[[kebab-case-id]]` syntax.
- Body text should expand or contextualize the claim, not restate it.
- Mark facts `status: stale` rather than deleting them, so the audit trail stays intact.