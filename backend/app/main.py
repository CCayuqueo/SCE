from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.auth.rate_limit import AuthRateLimiter
from app.auth.router import router as auth_router
from app.auth.supabase import SupabaseAuth
from app.core.config import Settings
from app.core.database import make_engine
from app.core.errors import ApiError, handle_api_error, handle_validation_error
from app.core.request_log import log_request
from app.image_processing.adapter import ImageProcessor
from app.image_processing.upload_limit import (
    LimitUploadBody,
    UploadBodyTooLarge,
    handle_large_upload,
)
from app.overlap.router import router as overlap_router
from app.rooms.router import router as rooms_router
from app.schedules.router import router as schedules_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = Settings()
    app.state.image_processor = ImageProcessor(app.state.settings)
    app.state.auth_rate_limit = AuthRateLimiter()
    app.state.supabase_auth = (
        SupabaseAuth(app.state.settings) if app.state.settings.supabase_url else None
    )
    engine = make_engine(app.state.settings)
    app.state.db = engine
    try:
        yield
    finally:
        engine.dispose()
        if app.state.supabase_auth:
            app.state.supabase_auth.client.close()


health = APIRouter(prefix="/api/v1/health")


@health.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@health.get(
    "/ready",
    response_model=dict[str, str],
    responses={503: {"description": "PostgreSQL no disponible"}},
)
def ready(request: Request) -> dict[str, str] | JSONResponse:
    try:
        with request.app.state.db.connect() as connection:
            connection.execute(text("SELECT 1"))
            if request.app.state.settings.supabase_url:
                connection.execute(
                    text(
                        "SELECT src_auth.identity_email('00000000-0000-0000-0000-000000000000'::uuid)"
                    )
                )
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Base de datos no disponible.",
                    "details": None,
                }
            },
        )
    return {"status": "ok"}


def create_app(*, api_docs: bool = True) -> FastAPI:
    application = FastAPI(
        title="SRC",
        version="1.0.0",
        lifespan=lifespan,
        openapi_url="/openapi.json" if api_docs else None,
    )
    application.add_exception_handler(ApiError, handle_api_error)
    application.add_exception_handler(UploadBodyTooLarge, handle_large_upload)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.add_middleware(LimitUploadBody)
    application.middleware("http")(log_request)
    for router in (
        auth_router,
        users_router,
        rooms_router,
        schedules_router,
        overlap_router,
        health,
    ):
        application.include_router(router)
    return application


app = create_app()
