# Source-curation assistant.
# Manually-driven (per PLAN.md §4 Phase 1) but provides:
#   - bulk import of candidate URLs from a CSV/JSON list
#   - interactive review queue (mark authentic / rejected / needs investigation)
#   - generation of source-record markdown stubs in local-knowledge-base/sources/
#
# Usage: `python scripts/source_curation.py review` — opens the local CLI queue.