from fastapi import HTTPException, Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import ApiError, handle_api_error


class UploadBodyTooLarge(HTTPException):
    def __init__(self) -> None:
        super().__init__(413)


async def handle_large_upload(request: Request, _: UploadBodyTooLarge):
    return await handle_api_error(
        request,
        ApiError(413, "IMAGE_TOO_LARGE", "La captura excede el límite de tamaño."),
    )


class LimitUploadBody:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not (
            scope["type"] == "http"
            and scope["method"] == "POST"
            and scope["path"].endswith("/schedules/me/upload")
        ):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        limit = request.app.state.settings.max_upload_mb * 1024**2 + 64 * 1024
        received = 0

        async def bounded_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise UploadBodyTooLarge()
            return message

        await self.app(scope, bounded_receive, send)
