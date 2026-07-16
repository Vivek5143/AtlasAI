"""FastAPI application entrypoint for InsightForge AI.

This module intentionally contains only the backend foundation required to
bootstrap the service. Business logic, routing modules, persistence, and
AI-specific integrations will be added in later steps.
"""

from fastapi import FastAPI


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="InsightForge AI",
        description="AI-powered Business Intelligence Platform",
        version="1.0.0",
    )

    @app.get("/", tags=["Root"])
    async def read_root() -> dict[str, str]:
        """Return a simple confirmation that the backend is running."""
        return {"message": "InsightForge AI Backend Running Successfully 🚀"}

    return app


app = create_application()
