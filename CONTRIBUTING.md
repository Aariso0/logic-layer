# Contributing to Logic Layer

Thanks for your interest in contributing to **Logic Layer** — a universal AI masking layer that catches hallucinations before they reach the user.

This guide explains how to set up the project locally, how we organize branches and commits, the PR process, and the standards we hold contributions to.

---

## 1. Code of Conduct

By participating in this project you agree to keep discussions respectful, constructive, and on-topic. We're a small team building something hard — assume good intent, give feedback on the work not the person, and help each other ship.

---

## 2. Getting Started

### 2.1 Prerequisites

- **Python** ≥ 3.11 (for the FastAPI middleware, claim extraction, verification layers)
- **Node.js** ≥ 18 LTS (for the UI client — browser extension + web dashboard)
- **PostgreSQL** ≥ 14 (for verdict history, metadata, logs)
- **Docker** + Docker Compose (for the local dev environment)
- **Git** ≥ 2.30
- **Make** (optional but recommended — we ship a `Makefile` with common commands)

### 2.2 Clone the repo

```bash
git clone https://github.com/<org>/logic-layer.git
cd logic-layer
```

### 2.3 Local environment setup

```bash
# Copy the env template and fill in real values
cp .env.example .env

# Python virtualenv for the middleware
python -m venv venv
source venv/bin/activate     # (Windows: venv\Scripts\activate)
pip install -r middleware/requirements.txt

# UI client
cd ui-client
npm install
cd ..
```

### 2.4 Running the stack locally

```bash
docker compose up --build       # postgres + middleware + ui-client
```

For running pieces individually during development:

```bash
# Middleware (FastAPI with hot reload)
cd middleware
uvicorn api.main:app --reload --port 8000

# UI client
cd ui-client
npm run dev
```

---

## 3. Branch Naming Convention

Use the following prefixes so the intent of every branch is obvious at a glance:

| Prefix | Use for |
|---|---|
| `feat/` | A new feature (e.g. `feat/trusted-source-check`) |
| `fix/` | A bug fix (e.g. `fix/claim-extraction-empty-string`) |
| `chore/` | Tooling, deps, refactors with no behavior change |
| `docs/` | Documentation-only changes |
| `test/` | Adding or fixing tests only |
| `hotfix/` | Urgent production fix (branch from `main`, not `develop`) |

Branch names are kebab-case after the prefix. Keep them short and specific.

---

## 4. Commit Messages

We follow **Conventional Commits** so the changelog and release notes can be generated automatically later.

Format:

```
<type>(<scope>): <short summary>

<body — wrap at ~72 chars, explain the *why*, not the *what*>

<footer — reference issues, breaking changes>
```

Examples:

```
feat(verification): add contradiction-detector verdict mapping
fix(claim-extraction): don't drop trailing punctuation on last claim
docs(readme): clarify four-verdict output contract
```

Allowed types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`.

---

## 5. Pull Request Process

1. **Branch off `develop`** for normal work, off `main` only for hotfixes.
2. **Keep PRs focused** — one logical change per PR. If a fix and a refactor are entangled, split them.
3. **Write or update tests** for any behavior change. PRs without tests will be asked to add them.
4. **Run the full local check before pushing:**
   ```bash
   make lint
   make test
   ```
5. **Fill out the PR template** completely — context, what changed, how to test, screenshots for UI.
6. **Request the right reviewer(s)** — `CODEOWNERS` will auto-request, but check the diff actually went to the folder owner.
7. **Squash-merge** once approved and CI is green. Don't merge your own PR until at least one approval is recorded.

### 5.1 Review expectations

- First review within **2 working days**.
- Reviews focus on: correctness, edge cases, readability, test coverage, and whether the change matches the design in `README.md` / `PLAN.md`.
- We do **not** block on style nits — the linter handles that.

---

## 6. Coding Standards

### 6.1 Python (middleware, verification, scripts)

- **PEP 8** + `ruff` for formatting and import order.
- **Type hints** on all public functions. `mypy --strict` is the bar.
- **Docstrings** (Google style) on every module and public function.
- No print statements in production code — use the `logging` module.
- Tests with `pytest`. Aim for ≥ 80% line coverage on touched modules.

### 6.2 JavaScript / TypeScript (UI client)

- **TypeScript strict mode**, no `any` unless justified in a comment.
- **ESLint + Prettier** with the repo config.
- **React functional components + hooks.** No class components in new code.
- Component files in `PascalCase.tsx`; utilities in `camelCase.ts`.

### 6.3 Markdown (local knowledge base, docs)

- One fact per file, frontmatter at the top.
- Every fact file must have a `source:` field linking to a record in `local-knowledge-base/sources/`.
- Link related facts with relative wiki-style links: `[[python-created-by-guido]]`.

---

## 7. Local Knowledge Base Contribution Rules

The local knowledge base is **curated, not auto-generated**. Follow these rules when adding facts:

1. Every fact must be **verifiable** from a whitelisted source in `local-knowledge-base/sources/`.
2. Facts are atomic — one claim per file. Don't bundle multiple claims together.
3. Cross-link generously with `[[wiki-style]]` links.
4. Never paste facts as context into the AI agent — that's the whole point of this project. The agent never sees the KB.
5. When a fact becomes outdated, mark it `status: stale` rather than deleting it, so the audit trail stays intact.

---

## 8. Issue Reporting

- **Bug reports** → use the `.github/ISSUE_TEMPLATE/bug_report.md` template.
- **Feature requests** → use the `.github/ISSUE_TEMPLATE/feature_request.md` template.
- **Security issues** → do **not** open a public issue. Email the team lead directly (see `CODEOWNERS`).

---

## 9. Releasing

Releases follow [Semantic Versioning](https://semver.org/). Tag format: `vMAJOR.MINOR.PATCH`. The `.github/workflows/release.yml` pipeline handles version bumps, changelog generation, and Docker image publishing. Manual releases are discouraged.

---

## 10. Questions?

If something in this guide is unclear, open a PR against this file — documentation is part of the project.

Thanks for contributing. 🎯