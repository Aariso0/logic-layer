# Database schema definitions (SQLAlchemy models) for verdict history, logs, metadata.
# Tables:
#   - verdicts: claim_id, verdict_type, evidence_used, source_id, created_at
#   - requests: request_id, prompt, agent_id, latency_ms, created_at
#   - sources: source_id, domain, last_verified, status