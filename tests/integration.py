# End-to-end / integration tests for the full pipeline.
# Covers:
#   - prompt → agent → claim extraction → 3-layer verification → verdict report
#   - feedback-loop correction flow
#   - latency budgets (PLAN.md §7) and known domain edge cases