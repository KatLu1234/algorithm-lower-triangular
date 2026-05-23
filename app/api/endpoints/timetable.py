"""POST /api/v1/timetable/solve — 시간표 추천 라우트.

frontend ↔ server 계약:
  요청  TimetableRequest  { preference, top_n?, explain? }
  응답  TimetableResponse { selection?, infeasibility?, explanation? }

MVP 범위 (claude/base/CLAUDE.md §1 안전 순서 step 2):
  - DB·캐시·LLM 미연결. 건물 거리는 후보 강의에서 자동 추출 + 기본 5분.
  - explain=true 여도 explanation=null 반환 (LLM 단계는 별도 base 변경).
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.libs.timetable import recommend
from app.schemas import (
    BuildingCode,
    InfeasibilityReport,
    PreferenceVector,
    SelectionResult,
)

router = APIRouter()

# 기본 도보 분 — 같은 건물 0, 다른 건물 _DEFAULT_INTER_BUILDING_MIN.
# 추후 DB(building_travel_times) 또는 app/core/config.py 상수로 대체.
_DEFAULT_INTER_BUILDING_MIN = 5


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
    """후보 강의에서 사용된 건물을 모아 거리 행렬 생성."""
    buildings = sorted({c.building for c in preference.courses})
    n = len(buildings)
    walk = [
        [0 if i == j else _DEFAULT_INTER_BUILDING_MIN for j in range(n)]
        for i in range(n)
    ]
    return buildings, walk


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
