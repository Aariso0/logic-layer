# README — middleware/
#
# The FastAPI-based orchestration layer that sits between the universal UI
# client and any target AI agent. It owns:
#
#   - The HTTP API (api/)
#   - Claim extraction (claim_extraction/)
#   - The three verification layers (verification/local_check/,
#     verification/trusted_source_check/, verification/contradiction_detector/)
#   - The correction feedback loop (feedback_loop/)
#   - Configuration, agent connectors, and DB models (config/)
#
# See README.md §3 and PLAN.md §4 for how these pieces fit together.