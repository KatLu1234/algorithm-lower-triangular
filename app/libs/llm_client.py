"""Upstage Solar API 호출 — LLM 단일 진입점.

architecture.md §5.3: LLM 호출은 본 모듈 한 곳에서만 일어난다. 다른 곳에서
직접 HTTPS 호출하지 않는다. requirements.txt에 새 의존을 추가하지 않기 위해
표준 라이브러리(urllib·json)로만 호출한다.

사용:
    from app.libs.llm_client import complete, LLMUnavailableError, LLMTimeoutError
    try:
        text = complete(messages, response_format="json_object")
    except LLMUnavailableError:
        ...  # 키 미설정 or 공급자 다운
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

from app.core.config import settings


class LLMError(Exception):
    """LLM 호출 실패 기본 예외."""


class LLMUnavailableError(LLMError):
    """공급자 미설정/도달 불가."""


class LLMTimeoutError(LLMError):
    """제한 시간 초과."""


class LLMBadResponseError(LLMError):
    """공급자가 비정상 응답(파싱 실패·빈 본문 등)."""


def _build_payload(
    messages: list[dict],
    *,
    temperature: float,
    response_format: str | None,
) -> dict:
    payload: dict = {
        "model": settings.UPSTAGE_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if response_format == "json_object":
        payload["response_format"] = {"type": "json_object"}
    return payload


def complete(
    messages: list[dict],
    *,
    temperature: float = 0.1,
    response_format: str | None = None,
) -> str:
    """OpenAI 호환 /chat/completions 호출 → assistant content 문자열 반환."""
    if not settings.UPSTAGE_API_KEY:
        raise LLMUnavailableError("UPSTAGE_API_KEY 환경변수가 비어 있습니다.")

    body = json.dumps(
        _build_payload(messages, temperature=temperature, response_format=response_format)
    ).encode("utf-8")

    req = urllib.request.Request(
        settings.UPSTAGE_API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.UPSTAGE_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=settings.UPSTAGE_TIMEOUT_S) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        # 4xx/5xx — 본문에 에러 메시지가 있을 수 있어 일부 추출 (시크릿 노출 금지)
        snippet = ""
        try:
            snippet = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        raise LLMUnavailableError(f"Upstage HTTP {e.code}: {snippet}") from e
    except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
        raise LLMTimeoutError(f"Upstage 도달 실패/타임아웃: {e}") from e

    try:
        data = json.loads(raw.decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise KeyError
        return content
    except (KeyError, ValueError, IndexError, TypeError) as e:
        raise LLMBadResponseError(f"Upstage 응답 형식 불일치: {e}") from e
