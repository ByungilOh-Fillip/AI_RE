from fastapi import FastAPI

from app.api.routes.system import router as system_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI_RE Backend API",
        version="0.1.0",
    )
    app.include_router(system_router)
    return app


app = create_app()
