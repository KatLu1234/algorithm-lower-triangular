"""LLM 메시지 조립기 (architecture.md §5.2).

llm-include의 프롬프트 파일을 *읽기만* 한다. import 대상으로 .py를 두지 않는다는
계층 규약을 지킨다.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable

# 워크트리 루트 — app/libs/llm_context.py 기준 ../.. 위. Docker 컨테이너에서는
# /srv/claude/llm-include/ (Dockerfile.backend가 함께 복사할 예정).
_LLM_INCLUDE_ROOT = Path(__file__).resolve().parents[2] / "claude" / "llm-include"


@lru_cache(maxsize=8)
def _read_prompt(name: str) -> str:
    """`claude/llm-include/prompts/<name>.md`의 '## 시스템 메시지 (그대로 LLM에 전달)'
    절 이후 본문을 system 메시지 텍스트로 추출. 절 헤더가 없으면 파일 전체 사용.
    """
    path = _LLM_INCLUDE_ROOT / "prompts" / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"prompt 파일 없음: {path}")
    text = path.read_text(encoding="utf-8")
    marker = "## 시스템 메시지"
    idx = text.find(marker)
    if idx < 0:
        return text.strip()
    # marker 뒤 첫 빈 줄까지 헤더, 그 다음 본문 시작
    after = text[idx:].split("\n", 1)[1] if "\n" in text[idx:] else ""
    return after.strip()


def _course_summary(courses: Iterable) -> list[dict]:
    """LLM 컨텍스트용 강의 요약 — id·name·professor·course_group_id만 추려 토큰 절약."""
    out = []
    for c in courses:
        out.append({
            "id": c.id,
            "name": c.name,
            "professor": c.professor,
            "course_group_id": c.course_group_id,
        })
    return out


def build_preference_extraction(
    text: str,
    current_preference: dict,
    candidate_courses: list,
) -> list[dict]:
    """LLM-A: 자연어 → PreferenceVector delta 메시지 배열.

    Returns:
        OpenAI 호환 [{role, content}] 배열. complete()에 그대로 넘긴다.
    """
    system = _read_prompt("preference_extract")
    user = (
        f'사용자 요청: "{text}"\n\n'
        f"현재 PreferenceVector (참고용 — delta는 변경할 키만):\n"
        f"{json.dumps(current_preference, ensure_ascii=False)}\n\n"
        f"candidate_courses (id·name·professor·course_group_id만):\n"
        f"{json.dumps(_course_summary(candidate_courses), ensure_ascii=False)}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
