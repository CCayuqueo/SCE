from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.auth.rate_limit import AuthRateLimiter
from app.auth.router import router as auth_router
from app.core.config import Settings
from app.core.database import make_engine
from app.core.errors import ApiError, handle_api_error, handle_validation_error
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = Settings()
    app.state.auth_rate_limit = AuthRateLimiter()
    engine = make_engine(app.state.settings)
    app.state.db = engine
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="SRC", version="1.0.0", lifespan=lifespan)
app.add_exception_handler(ApiError, handle_api_error)
app.add_exception_handler(RequestValidationError, handle_validation_error)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/api/v1/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/v1/health/ready",
    response_model=dict[str, str],
    responses={503: {"description": "PostgreSQL no disponible"}},
)
def ready(request: Request) -> dict[str, str] | JSONResponse:
    try:
        with request.app.state.db.connect() as connection:
            connection.execute(text("SELECT 1"))
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
