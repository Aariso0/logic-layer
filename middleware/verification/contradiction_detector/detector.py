# Layer 3 of the verification pipeline.
# Takes a claim + retrieved evidence and runs an NLI-style classification
# (entailment / contradiction / neutral). Produces the final verdict that
# the middleware maps to one of: Verified / Wrong / Unverifiable / Hallucinated.