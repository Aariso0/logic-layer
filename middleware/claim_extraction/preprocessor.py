# Wraps spaCy's sentence splitter / entity recognizer so the LLM call only handles
# the semantic decomposition; surface-level splitting stays cheap and deterministic.