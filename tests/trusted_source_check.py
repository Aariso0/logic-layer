# Tests for middleware/verification/trusted_source_check/.
# Covers:
#   - whitelisted-domain resolution
#   - .gov fallback search when whitelisted sources don't match
#   - rate-limit handling and retry behavior