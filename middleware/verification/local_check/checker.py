# Layer 1 of the verification pipeline (cheapest/fastest).
# Looks up a claim against the local curated facts database.
# Returns: match + source citation, or "no local match" to escalate to Layer 2.