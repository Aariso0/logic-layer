# Orchestrates the correction-feedback path: when a claim is flagged Hallucinated/Wrong,
# builds a correction prompt and sends it back to the target AI agent, then re-runs the
# verification pipeline on the new response. Bounded by FEEDBACK_LOOP_MAX_RETRIES.