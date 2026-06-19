# FastAPI application entry point for Logic Layer's middleware.
# Mounts routes, configures CORS, wires dependency injection for the
# verification pipeline (local_check → trusted_source_check → contradiction_detector).