# README — scripts/
#
# Operational scripts that don't belong inside the middleware service.
#
#   source_curation.py  — manual + assisted sorting of authentic sources (Phase 1)
#   db_updater.py       — scheduled refresh of the local facts database (Phase 7)
#
# All scripts are runnable directly with `python scripts/<name>.py` and read
# configuration from .env (see .env.example for the full list of variables).