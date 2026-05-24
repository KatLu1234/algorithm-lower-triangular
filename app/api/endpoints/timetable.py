"""POST /api/v1/timetable/solve — 시간표 추천 라우트.

frontend ↔ server 계약:
  요청  TimetableRequest  { preference, top_n?, explain? }
  응답  TimetableResponse { selection?, infeasibility?, explanation? }

MVP 범위 (claude/base/CLAUDE.md §1 안전 순서 step 2):
  - DB·캐시·LLM 미연결. 건물 거리는 후보 강의에서 자동 추출 + 기본 5분.
  - explain=true 여도 explanation=null 반환 (LLM 단계는 별도 base 변경).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.libs.timeroom_parser import load_courses_from_csv
from app.libs.timetable import recommend
from app.schemas import (
    BuildingCode,
    Course,
    InfeasibilityReport,
    PreferenceVector,
    SelectionResult,
)

router = APIRouter()

# 기본 도보 분 — 같은 건물 0, 다른 건물 _DEFAULT_INTER_BUILDING_MIN.
# 추후 DB(building_travel_times) 또는 app/core/config.py 상수로 대체.
_DEFAULT_INTER_BUILDING_MIN = 5

# 샘플 CSV — 컨테이너에서는 /srv/sample_data.csv (Dockerfile.backend 참고).
# 로컬 dev에서는 프로젝트 루트의 sample_data.csv.
_SAMPLE_CSV_PATH = Path(__file__).resolve().parents[3] / "sample_data.csv"

_sample_courses_cache: list[Course] | None = None


def _load_sample_courses() -> list[Course]:
    """sample_data.csv 1회 로드 후 캐시. 파일 없으면 빈 리스트."""
    global _sample_courses_cache
    if _sample_courses_cache is None:
        if _SAMPLE_CSV_PATH.exists():
            _sample_courses_cache = load_courses_from_csv(_SAMPLE_CSV_PATH)
        else:
            _sample_courses_cache = []
    return _sample_courses_cache


class TimetableRequest(BaseModel):
    preference: PreferenceVector
    top_n: int = Field(default=3, ge=1, le=15)
    explain: bool = False


class TimetableResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "솔브 결과 envelope"})

    selection: SelectionResult | None = None
    infeasibility: InfeasibilityReport | None = None
    explanation: str | None = None


def _building_grid(preference: PreferenceVector) -> tuple[list[BuildingCode], list[list[int]]]:
    """후보 강의에서 사용된 건물을 모아 거리 행렬 생성. 슬롯 단위 building override도 포함."""
    used: set[BuildingCode] = set()
    for c in preference.courses:
        used.add(c.building)
        for s in c.times:
            if s.building is not None:
                used.add(s.building)
    buildings = sorted(used)
    n = len(buildings)
    walk = [
        [0 if i == j else _DEFAULT_INTER_BUILDING_MIN for j in range(n)]
        for i in range(n)
    ]
    return buildings, walk


class SampleCoursesResponse(BaseModel):
    """샘플 강의 카탈로그 응답."""

    courses: list[Course]
    source: str = Field(description="원본 데이터 소스 (파일명·버전 등)")


@router.get("/sample-courses", response_model=SampleCoursesResponse)
def sample_courses():
    """국민대 sample_data.csv를 파싱한 강의 풀을 반환.

    프론트가 초기 로드 시 호출해 입력 폼의 후보 강의 풀을 채운다.
    파일이 없거나(로컬 dev 워크트리·테스트 환경) 모두 시간 미정이면 빈 리스트.
    """
    courses = _load_sample_courses()
    return SampleCoursesResponse(
        courses=courses,
        source=_SAMPLE_CSV_PATH.name if _SAMPLE_CSV_PATH.exists() else "(none)",
    )


@router.post("/solve")
def solve(req: TimetableRequest):
    try:
        buildings, walk = _building_grid(req.preference)
        outcome = recommend(req.preference, buildings, walk, top_k=req.top_n)
    except ValueError as e:
        # PreferenceVector 검증 외 도메인 ValueError (recommend 내부의 활동선택·DP 등)
        return JSONResponse(
            status_code=400,
            content={"detail": str(e), "code": "VALIDATION_ERROR"},
        )
    except Exception as e:  # pragma: no cover - 방어선
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "code": "INTERNAL"},
        )

    if isinstance(outcome, InfeasibilityReport):
        body = TimetableResponse(
            selection=None,
            infeasibility=outcome,
            explanation=None,
        )
    else:
        # MVP: LLM 미연결 → explain 플래그와 무관하게 explanation=null
        body = TimetableResponse(
            selection=outcome,
            infeasibility=None,
            explanation=None,
        )
    return body
