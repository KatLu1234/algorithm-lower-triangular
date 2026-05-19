"""루트 — 최적 시간표 추천 알고리즘.

A 가능성 분석 → B 가치 평가 → C 선택과 비교.
A에서 infeasibility가 검출되면 B·C를 건너뛰고 InfeasibilityReport만 반환한다 (§9.8).

PreferenceVector는 알고리즘 트리가 받는 *유일한 입력 형태*이며, 건물 코드·기본
도보 이동 시간 행렬은 별도 인자로 받는다 (현재 스키마에는 캠퍼스 지도 입력이
PreferenceVector 안에 없음).
"""
from __future__ import annotations

from typing import Union

from app.libs.feasibility import feasibility
from app.libs.selection import selection
from app.libs.valuation import valuation
from app.schemas import (
    BuildingCode,
    InfeasibilityReason,
    InfeasibilityReport,
    PreferenceVector,
    SelectionResult,
)


def recommend(
    prefs: PreferenceVector,
    building_codes: list[BuildingCode],
    base_walk_minutes: list[list[int]],
    top_k: int = 3,
) -> Union[SelectionResult, InfeasibilityReport]:
    feas = feasibility(prefs, building_codes, base_walk_minutes)

    if not feas.is_feasible:
        # mypy: is_feasible False 일 땐 infeasibility != None
        assert feas.infeasibility is not None
        return feas.infeasibility

    val = valuation(feas, prefs, top_k=top_k)
    if val.is_empty:
        return InfeasibilityReport(
            reason=InfeasibilityReason.CREDIT_CEILING_UNREACHABLE,
            stage="B-3",
            detail="제약을 모두 만족하는 시간표 조합이 없음 (백트래킹 결과 0개).",
            resolution_hint="학점 한도·필수 강의·blackout 중 하나를 완화하세요.",
            offending_course_ids=[],
        )

    return selection(feas, val, prefs)
