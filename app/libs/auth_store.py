"""로컬 SQLite 기반 사용자·세션 저장소.

저장 위치: `settings.AUTH_DB_PATH` (기본 `<project_root>/data/auth.db`).
DB 파일과 부모 디렉터리는 첫 사용 시점에 자동 생성한다.

스키마(2개 테이블):
  users  — 사용자 한 명당 한 행. 비밀번호는 PBKDF2-SHA256(200k iter, 16B salt)로
            해싱되어 BLOB 컬럼에 보관. 평문은 어디에도 남기지 않는다.
  tokens — 세션 토큰 한 개당 한 행. user_id 로 users 와 연결, ON DELETE CASCADE.

stdlib(`sqlite3`)만 사용 — 외부 의존성 없음.

기존 외부 API(인메모리 시절과 동일 시그니처)를 유지하므로 라우터 코드는
바뀌지 않는다.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings

_PBKDF2_ITERATIONS = 200_000
_SALT_BYTES = 16

# sqlite3 connection 한 개를 모듈 전역으로 두고 lock 으로 직렬화.
# FastAPI 동기 라우트에서 충분히 빠르고, 여러 connection 의 동기화 이슈를 피한다.
_conn: sqlite3.Connection | None = None
_lock = threading.Lock()


@dataclass
class _StoredUser:
    """라우터·내부 양쪽에서 쓰는 사용자 표현. 비밀번호 관련 필드는 노출 안 함."""
    id: str
    email: str
    display_name: str | None


class EmailAlreadyExists(Exception):
    pass


class InvalidCredentials(Exception):
    pass


def _db_path() -> Path:
    """설정된 경로를 Path 로. 상대경로면 프로젝트 루트 기준."""
    raw = settings.AUTH_DB_PATH or "data/auth.db"
    p = Path(raw)
    if not p.is_absolute():
        # config.py 는 app/ 안에 있으므로 부모를 두 번 올라가면 project root.
        project_root = Path(__file__).resolve().parents[2]
        p = project_root / p
    return p


def _ensure_conn() -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        return _conn
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False: FastAPI 스레드풀에서 호출되어도 동일 connection 사용.
    # 모든 쓰기/읽기는 _lock 으로 직렬화하므로 안전.
    conn = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id           TEXT PRIMARY KEY,
            email        TEXT NOT NULL UNIQUE,
            display_name TEXT,
            salt         BLOB NOT NULL,
            pw_hash      BLOB NOT NULL,
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS tokens (
            token      TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    _conn = conn
    return conn


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )


def _row_to_user(row: sqlite3.Row | tuple) -> _StoredUser:
    return _StoredUser(id=row[0], email=row[1], display_name=row[2])


# ─────────────────────────────────────────────────────────────────────────────
# 공개 API — 기존 인메모리 모듈과 동일 시그니처

def signup(email: str, password: str, display_name: str | None) -> _StoredUser:
    email_norm = email.strip().lower()
    salt = os.urandom(_SALT_BYTES)
    pw_hash = _hash_password(password, salt)
    user_id = str(uuid.uuid4())
    with _lock:
        conn = _ensure_conn()
        try:
            conn.execute(
                "INSERT INTO users (id, email, display_name, salt, pw_hash) "
                "VALUES (?, ?, ?, ?, ?);",
                (user_id, email_norm, display_name, salt, pw_hash),
            )
        except sqlite3.IntegrityError:
            # email UNIQUE 위반.
            raise EmailAlreadyExists()
    return _StoredUser(id=user_id, email=email_norm, display_name=display_name)


def verify_login(email: str, password: str) -> _StoredUser:
    email_norm = email.strip().lower()
    with _lock:
        conn = _ensure_conn()
        row = conn.execute(
            "SELECT id, email, display_name, salt, pw_hash FROM users WHERE email = ?;",
            (email_norm,),
        ).fetchone()
    if row is None:
        raise InvalidCredentials()
    salt: bytes = row[3]
    stored_hash: bytes = row[4]
    if not hmac.compare_digest(_hash_password(password, salt), stored_hash):
        raise InvalidCredentials()
    return _StoredUser(id=row[0], email=row[1], display_name=row[2])


def issue_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    with _lock:
        conn = _ensure_conn()
        conn.execute(
            "INSERT INTO tokens (token, user_id) VALUES (?, ?);",
            (token, user_id),
        )
    return token


def user_for_token(token: str) -> _StoredUser | None:
    with _lock:
        conn = _ensure_conn()
        row = conn.execute(
            "SELECT u.id, u.email, u.display_name "
            "FROM tokens t JOIN users u ON u.id = t.user_id "
            "WHERE t.token = ?;",
            (token,),
        ).fetchone()
    if row is None:
        return None
    return _row_to_user(row)


def revoke_token(token: str) -> None:
    with _lock:
        conn = _ensure_conn()
        conn.execute("DELETE FROM tokens WHERE token = ?;", (token,))
