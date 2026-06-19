# Content script injected into target AI agent pages.
# Reads the AI agent's response, sends it to the background worker for
# verification, and renders the verdict badge + side-by-side correction view
# in the host page.