# Logic Layer

**A universal AI masking layer that catches hallucinations before they reach the user.**

Maintained by **Team ReBinders**


---

## 1. The Problem

AI agents hallucinate. They generate confident, fluent, well-structured answers that are sometimes simply false. The industry-standard fix today — Retrieval Augmented Generation / "feeding the AI factual data" — helps, but it doesn't solve the problem. The facts still pass *through* the model, and the model can still distort, misattribute, or fabricate on top of them. The hallucination rate goes down. It never goes to zero.

## 2. Our Solution

Logic Layer is not another prompting trick or fine-tune. It's a **masking layer** that sits *outside* the AI agent, between the agent and the user.

Every response the agent generates is intercepted before the user sees it, broken down, checked against facts, and only released once it passes verification — or clearly labeled if it can't be verified.

**The key design choice:** our factual data is never handed to the AI agent as context. It is only used *after* the fact, to check the agent's output. This keeps our reference data clean — it's never paraphrased, diluted, or "creatively interpreted" by the model — and it's what separates Logic Layer from the standard RAG approach.

## 3. How It Works

### 3.1 The Big Picture

```
Universal UI Client
        |
        | (1) user prompt sent via API
        v
   LOGIC LAYER (middleware)
        |
        |--(2) routes prompt to target AI agent
        |--(3) receives raw response
        |--(4) breaks response into individual claims
        |--(5) verifies each claim (3-layer check, see below)
        |--(6) flags hallucinations / errors
        |--(7) sends correction feedback back to the AI agent and re-runs the check
        |--(8) once clean, returns verified response + report
        v
Universal UI Client (final answer + verification report shown to user)
```

The middleware is designed to be **agent-agnostic** — it doesn't matter which AI model is generating the response. It works as a wrapper/extension on top of any agent that exposes an API.

### 3.2 Claim-Level Verification (not whole-response verification)

We never verify a response as one block. We **decompose it into atomic claims** first.

> Example: *"Python was created by Guido van Rossum and released in 1991"* → two separate claims:
> 1. Python was created by Guido van Rossum
> 2. Python was released in 1991

Each claim is checked **independently**, so a response that is 90% correct doesn't get a blanket "wrong" — and a single false detail doesn't hide inside a mostly-true paragraph.

### 3.3 The Three-Layer Fact Check

Each atomic claim passes through up to three layers, in order of cost (cheapest/fastest first):

| Layer | What it does |
|---|---|
| **1. Local Check** | Looks up the claim against our own curated local facts database. Instant, free, no external calls. |
| **2. Trusted Source Check** | If not found locally, searches our whitelisted trusted sources (authentic, vetted sites; falls back to `*.gov` domain search for the relevant keyword if nothing else matches). |
| **3. Contradiction Detector** | A small AI model reads the claim alongside whatever evidence was found and gives a verdict — does the evidence support, contradict, or say nothing about this claim? |

### 3.4 Verdicts — Four Outputs, Not Two

Most fact-checkers give a binary true/false. We don't, because that's dishonest about what's actually checkable.

-  **Verified** — claim matches evidence, source is cited.
-  **Wrong** — claim contradicts evidence; correction + source provided.
-  **Unverifiable** — no evidence found anywhere in our system; flagged for the user as "we couldn't confirm this, be careful."
-  **Hallucinated** — the layer has detected the agent fabricated something; the incorrect statement and the correct one are shown **side by side** so the user sees exactly where the agent went wrong and what the truth is.

**On the "Unverifiable" output (and why we don't claim zero hallucinations):**
We can only verify claims that have evidence somewhere — in our local facts database or in trusted sources. If an AI agent invents something that has no footprint anywhere on the internet, there is nothing to check it against. That claim gets marked **Unverifiable**, not silently passed as true. Claiming "zero hallucinations" would require being able to verify literally everything that can be said — no system can do that, and we'd rather be transparent about the boundary than overclaim.

### 3.5 The Local Knowledge Base ("Second Brain" Architecture)

Inspired by Andrej Karpathy's "second brain" note-taking method, our local facts database is structured as an interlinked wiki rather than a flat lookup table:

- Each fact is a node with its own page/entry.
- Every fact entry links directly to its source (no orphan facts — every claim we can verify locally has a citation attached, by design).
- Facts and sources are cross-linked the way a personal wiki links related notes, which makes it easy for the verification layer to traverse related facts instead of doing flat keyword matching.
- This structure is **refreshed on a schedule** (not a one-time build) — sources get re-checked and facts get re-validated periodically so the local check layer doesn't go stale.

### 3.6 Why the Local Check Comes First

It's the fastest and cheapest layer, so we want it to absorb as much of the verification load as possible before falling back to live trusted-source lookups, which are slower and have rate/cost constraints.

## 4. Differentiation Summary

1. Factual data is never processed *through* the AI agent — it only checks the agent's output, so the reference data stays uncorrupted.
2. Claims are atomized before checking — no whole-block verdicts.
3. Three-layer pipeline balances speed (local) with coverage (trusted sources) with judgment (contradiction model).
4. Four honest verdicts instead of two, including an explicit "we don't know" state.
5. Hallucination verdicts show the wrong statement and the correct one side by side, not just a flag.
6. Works as a layer on top of *any* AI agent — not tied to one model or vendor.

## 5. Tech Stack (proposed)

| Layer | Technology |
|---|---|
| Middleware / orchestration API | Python (FastAPI) |
| Claim extraction (response → atomic claims) | LLM-based decomposition (function calling) + spaCy for sentence/entity splitting |
| Local facts database | Markdown-based wiki structure + vector store (ChromaDB / FAISS) for semantic lookup |
| Trusted source verification | Whitelisted-domain search + scraping (`requests`, `BeautifulSoup`), with `.gov` fallback search |
| Contradiction detector | Lightweight NLI-style model (entailment / contradiction / neutral classification) |
| Metadata / logs / verdict history | PostgreSQL |
| Source/db update scheduler | Cron-based or Airflow-style scheduled jobs |
| Universal UI client | Browser extension (React) + lightweight web dashboard |
| Agent connectors | REST/HTTP adapters per target AI agent's API |
| Containerization / deployment | Docker |

*(This stack is a starting proposal — to be revisited once the team finalizes the plan in `plan.md`.)*

## 6. Project Structure (proposed)

```
logic-layer/
├── README.md
├── plan.md
├── LICENSE
├── CONTRIBUTING.md
├── CODEOWNERS
├── .gitignore
├── .gitattributes
├── .env.example                 # template for required env vars/API keys, real .env never committed
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # lint + test on every push/PR
│   │   └── release.yml          # versioning/release automation (added once we're past the pilot)
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── middleware/
│   ├── api/                     # FastAPI app, routes between UI client and target agents
│   ├── claim_extraction/        # breaks raw AI responses into atomic claims
│   ├── verification/
│   │   ├── local_check/         # queries the local facts database
│   │   ├── trusted_source_check/ # whitelisted source + .gov fallback search
│   │   └── contradiction_detector/ # small model giving verdicts
│   ├── feedback_loop/           # sends correction prompts back to the AI agent, re-runs checks
│   └── config/                  # whitelisted domains, agent connectors, settings
├── local-knowledge-base/
│   ├── facts/                   # individual fact entries (wiki-style nodes)
│   ├── sources/                 # source records linked to facts
│   └── embeddings/              # vector index for semantic lookup
├── ui-client/
│   ├── browser-extension/
│   └── web-dashboard/
├── scripts/
│   ├── source_curation.py       # manual + assisted sorting of authentic sources
│   └── db_updater.py            # scheduled refresh of local facts database
├── tests/
└── docs/
```

### 6.1 Repo Hygiene Files — What They're For

| File / Folder | Purpose |
|---|---|
| `.gitignore` | Keeps env files, `__pycache__`, `node_modules`, model weights, local embeddings/index files, and logs out of version control. |
| `.gitattributes` | Normalizes line endings and marks large binary files (model weights, vector indexes) for Git LFS if we end up needing it. |
| `.env.example` | Documents which environment variables/API keys are required (agent API keys, DB connection strings) without ever committing real secrets. |
| `LICENSE` | Open-source license for the repo — to be chosen by the team before the first public push. |
| `CONTRIBUTING.md` | How to set up the repo locally, branch naming convention, PR process — useful once more than one person is pushing code. |
| `CODEOWNERS` | Maps each folder (`middleware/`, `local-knowledge-base/`, `ui-client/`) to whoever owns that part per Section 3 of `plan.md`, so PRs auto-request the right reviewer. |
| `.github/workflows/` | CI: runs lint + tests on every push/PR; release automation added later. |
| `.github/ISSUE_TEMPLATE/`, `PULL_REQUEST_TEMPLATE.md` | Keeps bug reports, feature requests, and PRs consistent as the team grows. |

**Suggested starter `.gitignore` contents:**

```
# Environments
.env
venv/
__pycache__/
*.pyc

# Node / UI client
node_modules/
dist/
build/

# Local knowledge base artifacts (regenerable, shouldn't bloat the repo)
local-knowledge-base/embeddings/*.index
local-knowledge-base/embeddings/*.faiss

# Logs & local DB dumps
*.log
*.db

# OS/editor clutter
.DS_Store
.vscode/
.idea/
```

## 7. Roadmap

See [`plan.md`](./plan.md) for phases, task breakdown, timeline, and open risks.

## 8. Team

**Team ReBinders**
