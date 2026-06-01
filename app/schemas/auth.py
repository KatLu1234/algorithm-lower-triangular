"""인증(로그인/회원가입) 입출력 스키마.

프로토타입 단계의 메모리 기반 인증 — 추후 Supabase Auth 로 갈아끼울 때
요청·응답 모양은 그대로 유지(라우트·CRUD만 교체)할 수 있도록 설계.

`EmailStr` 은 별도 `email-validator` 패키지가 필요하므로 (requirements.txt
변경은 사용자 확인 필요 — CLAUDE.md §4.2) 가벼운 `@` 포함 검증만 한다.
"""
from pydantic import BaseModel, Field, field_validator


def _normalize_email(value: str) -> str:
    value = (value or "").strip().lower()
    if "@" not in value or len(value) < 3:
        raise ValueError("올바른 이메일 형식이 아닙니다.")
    return value


class SignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=4, max_length=128)
    display_name: str | None = Field(default=None, max_length=64)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return _normalize_email(v)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return _normalize_email(v)


class UserPublic(BaseModel):
    """클라이언트에 노출 가능한 사용자 정보 (비밀번호·해시 제외)."""
    id: str
    email: str
    display_name: str | None = None


class AuthResponse(BaseModel):
    """로그인·회원가입 성공 응답.

    프론트는 token 을 localStorage 에 저장하고 이후 호출의
    Authorization: Bearer <token> 헤더로 전달한다.
    """
    token: str
    user: UserPublic
