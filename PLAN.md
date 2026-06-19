# Logic Layer — Project Plan

Team: **ReBinders**

This document lays out *how* we are going to build Logic Layer — phases, ownership, timeline, decisions we've already locked in from our discussions, and the risks we still need to think through. `README.md` covers *what* we're building; this covers *how* we get there.

---

## 1. Vision

Build a model-agnostic masking layer that intercepts AI agent responses, verifies them claim-by-claim against curated facts and trusted sources, and only releases a response to the user once it's been checked — clearly labeling anything that can't be confirmed instead of pretending it's fine.

## 2. Decisions (from team discussion)

These came out of our group discussion and should be treated as settled unless something forces a revisit:

1. **Facts never pass through the AI agent.** The agent never sees our facts file as context — it's only used to check the agent's output after the fact. This is our core differentiator and shouldn't be compromised for convenience.
2. **Claims are atomized before verification.** No whole-response verdicts. Every response gets broken into individual factual claims first.
3. **Three-layer check order:** Local Check → Trusted Source Check → Contradiction Detector. Cheapest/fastest layer first, escalate only when needed.
4. **Four verdicts, not two:** Verified, Wrong, Unverifiable, Hallucinated. "Unverifiable" is a first-class output, not a failure state we hide.
5. **Hallucinated verdicts show both sides.** Incorrect statement and correct statement are displayed together, not just flagged.
6. **Local database is structured like a personal wiki** ("second brain" style) — facts as linked nodes, each with a source attached next to it, not a flat table.
7. **Local database is a living thing**, not a one-time build — it needs a recurring update/refresh cycle.
8. **We do not claim "zero hallucinations."** We only claim to catch what has evidence somewhere. This is a positioning decision as much as a technical one — it's part of how we'll talk about the product.

## 3. Team Roles

> To be confirmed with the full team — drafted here as a starting proposal based on who raised which ideas in our discussion.

| Role | Responsibility |
|---|---|
| **Aaditya Soni — Team Lead** | Overall architecture management, coordination between members, helps any and all |
| **Middleware & Pipeline** | Builds the routing layer, agent connectors, feedback loop to the AI agent |
| **Verification Systems** | Claim extraction, local check, trusted source check, contradiction detector |
| **Local Knowledge Base** | Source curation, wiki-style fact structure, embeddings, update scheduler |
| **UI / Client** | Universal UI client (browser extension + dashboard), verdict display, side-by-side correction view |

*(Once the rest of the team confirms who's taking which piece, this table gets filled in with names.)*

## 4. Development Phases

### Phase 0 — Foundations 
- Finalize tech stack from README proposal.
- Set up repo structure as outlined in README.
- Define the schema for a "fact entry" (claim, source, last-verified date, confidence/category, links to related facts).
- Define the schema for a "verdict" (claim text, verdict type, evidence used, source, correction if applicable).

### Phase 1 — Source Curation & Local Facts DB v0 
- Manually sort and whitelist authentic sources (the step everyone agreed has to start manual).
- Stand up the wiki-style local knowledge base structure (nodes + source links).
- Seed it with an initial fact set in one or two test domains (pick something narrow first — don't try to cover everything at once).
- Build the embeddings/index layer for semantic lookup.

### Phase 2 — Middleware Skeleton 
- Build the basic routing: UI client → middleware → target AI agent → middleware → UI client, with no verification yet (plumbing first).
- Build at least one agent connector end-to-end to prove the pipe works.

### Phase 3 — Claim Extraction 
- Build the response-to-atomic-claims breakdown.
- Test against real AI outputs to make sure claims are split correctly (the Python/Guido example is our baseline test case).

### Phase 4 — Verification Layers
- Layer 1: Local Check against the Phase 1 knowledge base.
- Layer 2: Trusted Source Check, including the `.gov` fallback search when keywords aren't found locally.
- Layer 3: Contradiction Detector — evaluate small/lightweight model options for entailment-style classification.
- Wire the four-verdict output (Verified / Wrong / Unverifiable / Hallucinated) end-to-end.

### Phase 5 — Feedback Loop 
- Build the correction-feedback path: when a hallucination is flagged, send a correction prompt back to the target AI agent and re-run the check on the new response.
- Decide on a retry limit (how many correction passes before we just show the user "Unverifiable/Hallucinated" instead of looping forever).

### Phase 6 — Universal UI Client 
- Build the browser extension / dashboard.
- Design the side-by-side incorrect/correct display for hallucination verdicts.
- Design how "Unverifiable" is communicated so it reads as useful caution, not as a system failure.

### Phase 7 — Knowledge Base Maintenance Pipeline 
- Build the scheduled refresh job for the local facts database.
- Define how often sources get re-checked and how stale facts get flagged or removed.

### Phase 8 — Integration Testing 
- End-to-end tests across multiple target AI agents.
- Stress-test claim extraction on long, multi-claim responses.
- Check latency of the full pipeline (prompt → multi-layer check → possible correction loop → final response).

### Phase 9 — Pilot / Demo 
- Run the full pipeline on a narrow, well-curated knowledge domain as a live demo.
- Collect verdict accuracy data: how often Verified/Wrong/Unverifiable/Hallucinated calls match human judgment on a test set.

## 5. Milestones at a Glance

| Milestone | Target |
|---|---|
| Repo + schema finalized | End of Week 1 |
| Local facts DB v0 live (narrow domain) | End of Week 3 |
| Middleware plumbing working (no verification) | End of Week 4 |
| Claim extraction working | End of Week 5 |
| All 3 verification layers + 4 verdicts working | End of Week 8 |
| Feedback/correction loop working | End of Week 9 |
| UI client showing real verdicts | End of Week 10 |
| Full pipeline integration test pass | End of Week 12 |
| Demo-ready pilot | Week 12+ |

*(Timeline is a working draft — adjust once the team confirms availability and splits up the roles in Section 3.)*

## 6. Open Risks & Questions

These came up implicitly in our discussion and need actual answers before/while we build:

- **Latency:** multi-layer checking plus a possible correction loop back to the AI agent could make responses noticeably slower. Need to decide an acceptable max round-trip time.
- **Retry limit:** how many correction passes do we allow before giving up and surfacing "Unverifiable/Hallucinated" instead of looping?
- **Trusted source whitelist governance:** who decides what counts as "authentic," and how do we update that list over time without it becoming a bottleneck?
- **Contradiction detector model choice:** build vs. use an existing small NLI model — needs a proper evaluation, not just a default pick.
- **Coverage limits:** we've already agreed we can't claim zero hallucinations — need to decide how we communicate "Unverifiable" to users so it builds trust instead of reading as the system being broken.
- **Knowledge base scope:** which domain(s) do we start with? Trying to cover "everything" on day one isn't realistic — need to pick a narrow vertical for the first working version.
- **Update cadence for the local DB:** daily, weekly? Depends on the domain and how fast facts in it change.

## 7. Success Metrics (draft)

- % of claims correctly classified into the right verdict bucket, measured against a hand-labeled test set.
- False "Wrong" rate (we flag something as wrong when it was actually correct) — this is the costliest type of error to get wrong, since it erodes user trust.
- Latency of full pipeline (prompt-in to verified-response-out).
- Local Check hit rate (% of claims resolved without needing the slower trusted-source layer).

## 8. Immediate Next Steps

1. Confirm role assignments in Section 3 with the full team.
2. Lock the tech stack choices in `README.md` (anything anyone wants to challenge before we start building).
3. Pick the first narrow knowledge domain to seed the local facts database with.
4. Start Phase 0 and Phase 1 in parallel.