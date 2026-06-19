# API contract reference for the Logic Layer middleware.
# Describes the request/response shape for:
#   - POST /v1/verify
#   - POST /v1/extract-claims
#   - GET  /v1/verdicts/{id}
#   - GET  /healthz
# Plus the four-verdict output contract (Verified / Wrong / Unverifiable / Hallucinated).