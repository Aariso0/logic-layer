# Adapter that abstracts over local-model vs. API-hosted NLI backends.
# Loads the model once at startup; exposes a single .classify(claim, evidence) call.