# Scheduled (or manual) refresh of the local facts database.
# Steps:
#   1. Walk local-knowledge-base/facts/ + local-knowledge-base/sources/
#   2. For each source, re-fetch and re-validate reachability + authenticity
#   3. Re-embed all verified facts and rebuild the vector index in embeddings/
#   4. Update last_verified timestamps; mark unreachable/disputed facts as stale
#
# Triggered by KB_REFRESH_CRON (see .env.example) or run manually:
#   python scripts/db_updater.py --dry-run