from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.exc import DBAPIError

from app.auth.dependencies import (
    AppSettings,
    CsrfUser,
    CurrentUser,
    Db,
    limit,
    require_json,
)
from app.auth.router import clear_session_cookie
from app.auth.schemas import UserView
from app.users.schemas import (
    DeletionInput,
    DeletionPreview,
    PasswordUpdate,
    ProfileUpdate,
)
from app.users.service import (
    change_password,
    delete_account,
    deletion_conflict,
    describe_deletion,
    owned_rooms,
    preview_version,
    update_profile,
)

router = APIRouter(prefix="/api/v1/users/me", tags=["users"])
json_body = [Depends(require_json)]


@router.get("")
def read_profile(response: Response, db: Db, auth: CurrentUser) -> UserView:
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return UserView.model_validate(auth.user)


@router.patch("", dependencies=json_body)
def save_profile(
    data: ProfileUpdate, request: Request, response: Response, db: Db, auth: CsrfUser
) -> UserView:
    if data.email is not None and data.email != auth.user.email:
        limit(request, "reauth", auth.user.email)
    update_profile(db, auth.user, data)
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return UserView.model_validate(auth.user)


@router.put("/password", status_code=204, dependencies=json_body)
def save_password(
    data: PasswordUpdate, request: Request, response: Response, db: Db, auth: CsrfUser
) -> None:
    limit(request, "reauth", auth.user.email)
    change_password(db, auth, data.current_password, data.new_password)
    db.commit()
    response.headers["Cache-Control"] = "no-store"


@router.get("/deletion-preview")
def deletion_preview(response: Response, db: Db, auth: CurrentUser) -> DeletionPreview:
    preview, _ = describe_deletion(db, auth.user, owned_rooms(db, auth.user))
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    response.headers["ETag"] = preview_version(preview)
    return preview


@router.post("/deletion", status_code=204, dependencies=json_body)
def remove_account(
    data: DeletionInput,
    request: Request,
    response: Response,
    db: Db,
    auth: CsrfUser,
    settings: AppSettings,
) -> None:
    limit(request, "reauth", auth.user.email)
    try:
        delete_account(db, auth.user, data, request.headers.get("if-match"))
        db.commit()
    except DBAPIError as error:
        if getattr(error.orig, "sqlstate", None) in {"23503", "40001", "40P01"}:
            raise deletion_conflict() from error
        raise
    clear_session_cookie(response, settings)
