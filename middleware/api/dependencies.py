# Per-request dependency wiring (DB sessions, vector store client, agent connector).
# Keeps route handlers thin — they pull dependencies from here.