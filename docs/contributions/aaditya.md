Contribution Report – Ollama, Qwen3.5, spaCy Claim Extraction, and Docker Packaging

Contributor

Module: Verifier Layer (Steps 3 and 13)
Files Contributed:

- `logiclayer/verifier/claim_extractor.py`
- `logiclayer/verifier/ollama_client.py`
- `logiclayer/verifier/system_prompt.py`
- `logiclayer/verifier/_standalone_test.py`
- `logiclayer/verifier/__init__.py`
- `Dockerfile`

---

1. Overview

This contribution covers Step 3 of the Logic Layer pipeline and the Step 13 Dockerfile. Step 3 is responsible for two things: splitting a raw agent response into atomic, verifiable claims, and asking a local Qwen3.5 4B model (served via Ollama) to judge any claim that the earlier local-DB and scraper layers could not resolve on their own. Step 13 packages the entire project — including the Qwen model pull and the spaCy language model download — into a reproducible container image.

The module is intentionally narrow. It does not perform local-DB lookups, scraping, or final verdict reporting. Its only outputs are a list of clean claims and a stream of `report_verdict` tool calls, which the orchestrator (Step 5) and the formatter (Step 6) consume downstream.

---

2. Objectives

The verifier module was designed to achieve the following objectives:

- Convert a raw agent response into a clean, ordered list of atomic claims.
- Enforce a stable `list[{"claim_id": int, "text": str}]` contract on the boundary with the orchestrator.
- Wrap Ollama's `/api/chat` HTTP endpoint behind a small, testable client.
- Define the OpenAI-style tool schemas (`check_local_db`, `search_trusted_sources`, `report_verdict`) once, in code.
- Provide a system prompt that tells Qwen its exact role: judge the evidence the orchestrator has already collected.
- Allow configuration through environment variables (`OLLAMA_HOST`, `OLLAMA_MODEL`) with sensible local defaults.
- Package the full stack — Python code, Qwen model, and spaCy model — into a single Docker image.

---

3. Architecture

The Step 3 portion of the pipeline follows the architecture below.

    raw agent response
            │
            ▼
     claim_extractor.extract_claims(text)
            │  list[{claim_id, text}]
            ▼
     orchestrator (step 5) pre-checks each claim
            │
            ├── local-DB / scraper can resolve it  →  record verdict, skip Qwen
            │
            └── neither can resolve it  →  build system prompt
                                           │  list[{claim_id, text, evidence}]
                                           ▼
                                  ollama_client.chat(messages, tools=[...])
                                           │
                                           ▼
                                  Qwen3.5 4B via Ollama
                                           │
                                           ▼
                                  report_verdict (one per claim)

The Dockerfile (Step 13) sits one layer above this: it installs the package, pulls Qwen3.5 4B via Ollama (or points at an existing instance via `OLLAMA_HOST`), downloads the spaCy `en_core_web_sm` model, and runs the CLI or scheduler.

---

4. Files Owned

| File | What it does |
|---|---|
| `logiclayer/verifier/claim_extractor.py` | spaCy pipeline that splits a raw agent response into atomic claims and returns `list[{"claim_id": int, "text": str}]` — the contract shape the orchestrator consumes. |
| `logiclayer/verifier/ollama_client.py` | Thin HTTP wrapper around Ollama's `/api/chat` endpoint. POSTs the messages array and tools schema, returns the parsed response, and exposes helpers (`extract_tool_calls`, `extract_content`) to read the reply. Also defines the three OpenAI-style tool schemas: `check_local_db`, `search_trusted_sources`, `report_verdict`. Host and model are read from `OLLAMA_HOST` / `OLLAMA_MODEL` env vars, falling back to `http://localhost:11434` and `qwen3.5:4b`. |
| `logiclayer/verifier/system_prompt.py` | The system prompt template fed to Qwen. Tells the model it is receiving only the claims the local-DB and scraper layers could not auto-verify, and that its job is to judge the evidence (or its absence) and call `report_verdict` per claim. |
| `logiclayer/verifier/_standalone_test.py` | Throwaway manual smoke test for `ollama_client.py` — exercises 5 hand-written claims end-to-end and prints whether Qwen actually emits tool calls instead of answering from its own knowledge. |
| `logiclayer/verifier/__init__.py` | Package marker so `from logiclayer.verifier...` resolves. |
| `Dockerfile` (Step 13) | Installs the package, pulls Qwen3.5 4B via Ollama (or points at an existing instance via `OLLAMA_HOST`), downloads the spaCy `en_core_web_sm` model, and runs the CLI/scheduler. |

---

5. Boundary Contracts

5.1 Contract with the Orchestrator (Step 5)

The claim list passed to the orchestrator is always `list[{"claim_id": int, "text": str}]`. It is ordered as the claims appear in the source text, deduplicated (case-insensitive, whitespace-normalized), and with pure questions, interjections, and very short fragments already filtered out. The orchestrator never sees the raw agent response — only this list.

---

5.2 Contract with the Formatter (Step 6)

Qwen's `report_verdict` tool calls are the only thing the formatter needs. The orchestrator (Step 5) collects them into a structured report object; this module does not produce the user-facing reply itself. The `report_verdict` tool schema — defined in `ollama_client.py` — defines which fields are available to the formatter.

---

6. What This Module Depends On

- **Manish (Step 1)** — `check_local_db(claim)` must exist and return `(fact_id, statement, source_name)` or `None` so the orchestrator can decide whether a claim is already resolved before handing it to Qwen.
- **Ranveer (Step 2)** — `search_trusted_sources(query)` must exist and return the same shape so the orchestrator can fall back to scraping before involving Qwen.
- **Anay (Step 5)** — the orchestrator is responsible for the per-claim gating logic. That gating lives in code, not in the system prompt, so Qwen cannot skip the local check even if it wanted to.

---

7. What Depends on This Module

- **Anay (Step 5)** consumes `extract_claims` and `ollama_client.chat` directly. The claim shape and the tool schema names are the contract.
- **Soumya (Step 6)** reads the verdict report that the orchestrator builds from Qwen's `report_verdict` calls. The `report_verdict` tool schema (in `ollama_client.py`) defines what fields are available.

---

8. Manual Checks Before Integration

1. `ollama pull qwen3.5:4b` and `ollama run qwen3.5:4b "hello"` from the terminal — confirm Ollama is reachable end-to-end before any code is touched.
2. `python -m logiclayer.verifier._standalone_test` — runs the 5 hand-written claims through `ollama_client.chat` and prints whether Qwen emits tool calls. The expectation is that every claim produces at least one `check_local_db` call; if not, the tool schema or model tag needs adjusting before Step 5 is wired on top.
3. `python -m logiclayer.verifier.claim_extractor` — quick smoke test of the spaCy extractor. The plan calls for 10–15 hand-written responses tested standalone before integration; that wider sweep lives in `tests/test_orchestrator.py` once Step 5 lands.

---

9. Design Principles Followed

The implementation follows several software engineering principles.

---

Separation of Concerns

This module handles claim extraction and LLM judgement only — local-DB lookups, scraping, and reporting are explicitly out of scope.

---

Stable Contracts

The claim list shape and the tool schema names are treated as public interfaces and documented as such.

---

Configuration over Hard-coding

Ollama host and model are environment variables with local defaults, so the same code works in dev, CI, and the container.

---

Testability

A standalone smoke test exercises the LLM boundary without involving the rest of the pipeline, making regressions easy to spot.

---

Reproducibility

The Dockerfile pins the model and the spaCy language model so a fresh container can run end-to-end with no extra setup.

---

10. Outcome

The contribution delivers the claim-extraction and LLM-judgement core of the verifier layer, plus a Dockerfile that lets the whole stack run reproducibly in a container. Together they give the rest of the team a stable boundary to build against: a clean list of claims on the input side, and a stream of `report_verdict` tool calls on the output side.

Overall, this contribution turns the Step 3 and Step 13 work into a focused, testable, and clearly-contracted piece of the system that slots cleanly into the wider Logic Layer pipeline.
