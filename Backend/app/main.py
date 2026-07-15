from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors.handlers import register_error_handlers
from app.api.middleware.request_context import RequestContextMiddleware
from app.api.routes.chat import router as chat_router
from app.api.routes.system import router as system_router
from app.infrastructure.database.connection import Database
from app.infrastructure.logging import configure_logging
from app.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    selected_settings = settings or get_settings()
    database = Database(selected_settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        await database.dispose()

    app = FastAPI(
        title="AI_RE Backend API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.database = database
    if settings is not None:
        app.dependency_overrides[get_settings] = lambda: selected_settings

    configure_logging(selected_settings.log_level)
    register_error_handlers(app)
    app.add_middleware(
        RequestContextMiddleware,
        max_body_bytes=selected_settings.max_request_body_bytes,
        timeout_seconds=selected_settings.request_timeout_seconds,
    )
    app.include_router(system_router)
    app.include_router(chat_router)
    return app


app = create_app()
