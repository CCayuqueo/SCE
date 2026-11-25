import json
import logging
import re
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.core.errors import ApiError, handle_api_error

logger = logging.getLogger("src.requests")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.propagate = False

REQUEST_ID = re.compile("[0-9a-f]{32}")


async def log_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
    supplied = request.headers.get("x-request-id", "")
    request_id = supplied if REQUEST_ID.fullmatch(supplied) else uuid4().hex
    started = perf_counter()
    error = None
    try:
        response = await call_next(request)
    except Exception as exception:  # noqa: BLE001 - frontera de solicitudes HTTP
        # No se registran URL, cuerpos, cookies, nombres de archivos ni parámetros SQL.
        error = type(exception).__name__
        response = await handle_api_error(
            request, ApiError(500, "INTERNAL_ERROR", "Ocurrió un error interno.")
        )

    response.headers["X-Request-ID"] = request_id
    logger.info(
        json.dumps(
            {
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "status": response.status_code,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
                "error": error,
            },
            ensure_ascii=False,
        )
    )
    return response
