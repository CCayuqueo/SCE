from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.headers = headers


async def handle_api_error(request: Request, error: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status,
        content={
            "error": {"code": error.code, "message": error.message, "details": None}
        },
        headers={"Cache-Control": "no-store", **(error.headers or {})},
    )


async def handle_validation_error(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    # input y ctx pueden incluir contraseñas u otros datos privados.
    details = [
        {"field": list(item["loc"]), "type": item["type"]} for item in error.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Revisa los datos ingresados.",
                "details": details,
            }
        },
        headers={"Cache-Control": "no-store"},
    )
