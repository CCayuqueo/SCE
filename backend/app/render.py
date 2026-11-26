from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.main import create_app

web = Path(__file__).resolve().parents[1] / "web"
app = create_app(api_docs=False)
app.mount("/assets", StaticFiles(directory=web / "assets"), name="assets")


@app.middleware("http")
async def security_headers(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    if response.status_code == 200 and request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


@app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
def frontend(path: str) -> FileResponse:
    if path not in {"", "login", "register", "app"} and not path.startswith("app/"):
        raise HTTPException(404)
    return FileResponse(web / "index.html", headers={"Cache-Control": "no-cache"})
