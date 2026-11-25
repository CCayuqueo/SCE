from fastapi import APIRouter, Depends, Request, Response

from app.auth.dependencies import (
    SESSION_COOKIE,
    AppSettings,
    CsrfUser,
    CurrentUser,
    Db,
    limit,
    require_json,
    require_origin,
)
from app.auth.schemas import LoginInput, RegistrationInput, SessionView, UserView
from app.auth.security import csrf_token
from app.auth.service import login, register

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
public_write = [Depends(require_origin), Depends(require_json)]


def set_session_cookie(response: Response, token: str, settings: AppSettings) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=settings.app_env != "development",
        samesite="lax",
        path="/",
        max_age=settings.session_ttl_hours * 3600,
    )


@router.post("/register", status_code=201, dependencies=public_write)
def register_user(
    data: RegistrationInput,
    request: Request,
    response: Response,
    db: Db,
    settings: AppSettings,
) -> UserView:
    limit(request, "register", data.email)
    user, token = register(db, data, settings, request.cookies.get(SESSION_COOKIE))
    db.commit()
    set_session_cookie(response, token, settings)
    return UserView.model_validate(user)


@router.post("/login", dependencies=public_write)
def login_user(
    data: LoginInput,
    request: Request,
    response: Response,
    db: Db,
    settings: AppSettings,
) -> SessionView:
    limit(request, "login", data.email)
    user, token = login(db, data, settings, request.cookies.get(SESSION_COOKIE))
    db.commit()
    set_session_cookie(response, token, settings)
    return SessionView(user=UserView.model_validate(user), csrf_token=csrf_token(token))


@router.get("/me")
def get_me(response: Response, db: Db, auth: CurrentUser) -> SessionView:
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return SessionView(
        user=UserView.model_validate(auth.user), csrf_token=csrf_token(auth.token)
    )


@router.post("/logout", status_code=204)
def logout_user(
    response: Response, db: Db, auth: CsrfUser, settings: AppSettings
) -> None:
    db.delete(auth.session)
    db.commit()
    clear_session_cookie(response, settings)


def clear_session_cookie(response: Response, settings: AppSettings) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=settings.app_env != "development",
        samesite="lax",
    )
