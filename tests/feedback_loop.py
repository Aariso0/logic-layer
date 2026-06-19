# Tests for middleware/feedback_loop/.
# Covers:
#   - correction prompt is built correctly when a claim is flagged
#   - retry cap (FEEDBACK_LOOP_MAX_RETRIES) is enforced
#   - "Unverifiable/Hallucinated" surfaced to the UI after the retry cap is hit