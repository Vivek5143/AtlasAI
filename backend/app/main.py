from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router


def create_application() -> FastAPI:
    app = FastAPI(
        title="Atlas AI",
        description="AI-powered Business Intelligence Platform",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["Root"])
    async def read_root() -> dict[str, str]:
        return {
            "message": "Atlas AI Backend Running Successfully 🚀"
        }

    app.include_router(api_router)

    return app


app = create_application()