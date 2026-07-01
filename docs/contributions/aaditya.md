# Aaditya — Step 3 (Ollama + Qwen3.5 4B + spaCy claim extraction) + Step 13 (Dockerfile)

## Files owned

| File | What it does |
|---|---|
| `logiclayer/verifier/claim_extractor.py` | spaCy pipeline that splits a raw agent response into atomic claims and returns `list[{"claim_id": int, "text": str}]` — the contract shape the orchestrator consumes. |
| `logiclayer/verifier/ollama_client.py` | Thin HTTP wrapper around Ollama's `/api/chat` endpoint. POSTs the messages array + tools schema, returns the parsed response, and exposes helpers (`extract_tool_calls`, `extract_content`) to read the reply. Also defines the three OpenAI-style tool schemas: `check_local_db`, `search_trusted_sources`, `report_verdict`. Host and model are read from `OLLAMA_HOST` / `OLLAMA_MODEL` env vars, falling back to `http://localhost:11434` and `qwen3.5:4b`. |
| `logiclayer/verifier/system_prompt.py` | The system prompt template fed to Qwen. Tells the model it is receiving only the claims the local-DB and scraper layers could not auto-verify, and that its job is to judge the evidence (or its absence) and call `report_verdict` per claim. |
| `logiclayer/verifier/_standalone_test.py` | Throwaway manual smoke test for `ollama_client.py` — exercises 5 hand-written claims end-to-end and prints whether Qwen actually emits tool calls instead of answering from its own knowledge. |
| `logiclayer/verifier/__init__.py` | Package marker so `from logiclayer.verifier...` resolves. |
| `Dockerfile` (step 13) | Installs the package, pulls Qwen3.5 4B via Ollama (or points at an existing instance via `OLLAMA_HOST`), downloads the spaCy `en_core_web_sm` model, and runs the CLI/scheduler. |

## How the pieces plug into the pipeline

```
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
```

The key contract on the boundary with Anay (step 5): the claim list is
**always** `list[{"claim_id": int, "text": str}]`, ordered as the claims
appear in the source text, deduplicated (case-insensitive, whitespace-
normalized), and with pure questions / interjections / very short
fragments already filtered out. The orchestrator never sees the raw
agent response — only this list.

The key contract on the boundary with Soumya (step 6): Qwen's
`report_verdict` tool calls are the only thing the formatter needs.
The orchestrator (step 5) collects them into a structured report
object; this module does not produce the user-facing reply itself.

## What I depend on

- **Manish (step 1)** — `check_local_db(claim)` must exist and return
  `(fact_id, statement, source_name)` or `None` so the orchestrator can
  decide whether a claim is already resolved before handing it to Qwen.
- **Ranveer (step 2)** — `search_trusted_sources(query)` must exist and
  return the same shape so the orchestrator can fall back to scraping
  before involving Qwen.
- **Anay (step 5)** — the orchestrator is responsible for the per-claim
  gating logic. I deliberately put that gating in code, not in the
  system prompt, so Qwen cannot skip the local check even if it wanted
  to.

## What depends on me

- **Anay (step 5)** consumes `extract_claims` and `ollama_client.chat`
  directly. The claim shape and the tool schema names are the contract.
- **Soumya (step 6)** reads the verdict report that the orchestrator
  builds from Qwen's `report_verdict` calls. The `report_verdict` tool
  schema (in `ollama_client.py`) defines what fields are available.

## Manual checks before integration

1. `ollama pull qwen3.5:4b` and `ollama run qwen3.5:4b "hello"` from
   the terminal — confirm Ollama is reachable end-to-end before any
   code is touched.
2. `python -m logiclayer.verifier._standalone_test` — runs the 5
   hand-written claims through `ollama_client.chat` and prints whether
   Qwen emits tool calls. The expectation is that every claim produces
   at least one `check_local_db` call; if not, the tool schema or model
   tag needs adjusting before step 5 is wired on top.
3. `python -m logiclayer.verifier.claim_extractor` — quick smoke test
   of the spaCy extractor. Plan calls for 10–15 hand-written
   responses tested standalone before integration; that wider sweep
   lives in `tests/test_orchestrator.py` once step 5 lands.
