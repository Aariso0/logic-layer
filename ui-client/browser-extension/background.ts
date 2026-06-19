# Service worker / background script for the extension.
# Bridges between the content script (which reads AI agent responses) and the
# Logic Layer middleware API. Handles auth tokens, retry logic, and surfacing
# the verdict report back into the page.