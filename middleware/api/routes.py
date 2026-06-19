# FastAPI router definitions for the middleware.
# Endpoints:
#   POST /v1/verify          — full pipeline: agent call → claim extraction → verification → response
#   POST /v1/extract-claims  — utility: raw text → atomic claims (debug/test)
#   GET  /v1/verdicts/{id}   — fetch verdict history for a prior request
#   GET  /healthz            — liveness/readiness