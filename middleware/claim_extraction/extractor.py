# Breaks a raw AI agent response into atomic, independently-verifiable claims.
# Combines LLM function-calling (semantic decomposition) with spaCy sentence/entity
# splitting. Output: ordered list of claim strings + their source spans.