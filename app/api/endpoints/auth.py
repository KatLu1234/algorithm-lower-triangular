"""인증 엔드포인트 — /api/v1/auth/*.

로컬 영속화(SQLite). 사용자·토큰은 `app/libs/auth_store.py` 가 관리하고
파일은 `settings.AUTH_DB_PATH` 에 저장된다. Supabase Auth 는 사용하지 않는다
(데이터 카탈로그용 `app/db/supabase.py` 는 별도로 그대로 유지).

에러 응답은 base/architecture.md §5.1 의 {detail, code} 표준.
"""
from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from app import schemas
from app.libs import auth_store

router = APIRouter()


def _to_public(u: auth_store._StoredUser) -> schemas.UserPublic:
    return schemas.UserPublic(id=u.id, email=u.email, display_name=u.display_name)


def _err(status_code: int, detail: str, code: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail, "code": code})


class _AuthError(Exception):
    """get_current_user 가 표준 에러 본문을 반환하도록 한 sentinel."""

    def __init__(self, status_code: int, detail: str, code: str):
        self.status_code = status_code
        self.detail = detail
        self.code = code


def get_current_user(
    authorization: str | None = Header(default=None),
) -> auth_store._StoredUser:
    """Authorization: Bearer <token> 헤더에서 사용자 해석."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _AuthError(401, "로그인이 필요합니다.", "AUTH_REQUIRED")
    token = authorization.split(" ", 1)[1].strip()
    user = auth_store.user_for_token(token)
    if user is None:
        raise _AuthError(401, "유효하지 않은 토큰입니다.", "AUTH_INVALID")
    return user


@router.post("/signup")
def signup(payload: schemas.SignupRequest):
    try:
        user = auth_store.signup(payload.email, payload.password, payload.display_name)
    except auth_store.EmailAlreadyExists:
        return _err(409, "이미 등록된 이메일입니다.", "EMAIL_TAKEN")
    token = auth_store.issue_token(user.id)
    return schemas.AuthResponse(token=token, user=_to_public(user))


@router.post("/login")
def login(payload: schemas.LoginRequest):
    try:
        user = auth_store.verify_login(payload.email, payload.password)
    except auth_store.InvalidCredentials:
        return _err(
            401,
            "이메일 또는 비밀번호가 올바르지 않습니다.",
            "INVALID_CREDENTIALS",
        )
    token = auth_store.issue_token(user.id)
    return schemas.AuthResponse(token=token, user=_to_public(user))


@router.get("/me", response_model=schemas.UserPublic)
def me(current=Depends(get_current_user)) -> schemas.UserPublic:
    return _to_public(current)


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)) -> dict:
    if authorization and authorization.lower().startswith("bearer "):
        auth_store.revoke_token(authorization.split(" ", 1)[1].strip())
    return {"ok": True}
