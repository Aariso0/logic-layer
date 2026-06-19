# Tests for middleware/claim_extraction/.
# Covers:
#   - sentence/entity preprocessor edge cases
#   - LLM-based decomposition against the README §3.2 baseline (Python/Guido/1991)
#   - empty / single-claim / very long input handling