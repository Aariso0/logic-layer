# Per-target-agent connector base class + concrete adapters.
# Each connector exposes a uniform .send(prompt) -> response interface so the middleware
# stays agent-agnostic (per README §3.1).