"""루트 — 최적 시간표 추천 알고리즘.

A 가능성 분석 → B 가치 평가 → C 선택과 비교. A에서 infeasibility가 검출되면
B·C를 건너뛰고 InfeasibilityReport만 채워 조기 종료한다 (§9.8).
"""
from __future__ import annotations

from app.libs.feasibility import feasibility
from app.libs.selection import selection
from app.libs.valuation import valuation
from app.schemas.timetable import (
    InfeasibilityReport,
    Preferences,
    TimetableInput,
    TimetableResult,
)


def _suggestions_for(reason: str, prefs: Preferences) -> list[str]:
    suggestions: list[str] = []
    if "필수 강의 학점 합" in reason:
        suggestions.append("필수 포함 강의 일부를 해제하거나 학점 한도를 올려보세요.")
    if "필수 포함 강의들이 서로" in reason:
        suggestions.append("필수 포함 강의 중 시간이 겹치는 항목을 검토하세요.")
    if "하한 미달" in reason:
        suggestions.append("학점 하한을 낮추거나 후보 강의를 추가하세요.")
    if "남은 강의가 없음" in reason:
        suggestions.append("제외 목록 또는 blackout 시간대를 조정해 후보를 확보하세요.")
    if not suggestions:
        suggestions.append("입력 제약을 한 가지씩 완화해 다시 시도하세요.")
    return suggestions


def recommend(payload: TimetableInput) -> TimetableResult:
    feas = feasibility(
        payload.courses,
        payload.building_codes,
        payload.base_walk_minutes,
        payload.preferences,
    )

    if not feas.credit_ceiling_reachable or feas.infeasibility_reason is not None:
        reason = feas.infeasibility_reason or "도달 가능한 학점 조합이 없음"
        return TimetableResult(
            infeasibility=InfeasibilityReport(
                reason=reason,
                suggestions=_suggestions_for(reason, payload.preferences),
            )
        )

    val = valuation(feas, payload.preferences)
    if not val.top_k_candidates:
        return TimetableResult(
            infeasibility=InfeasibilityReport(
                reason="제약을 모두 만족하는 시간표 조합이 없음",
                suggestions=_suggestions_for("남은 강의가 없음", payload.preferences),
            )
        )

    sel = selection(feas, val)
    return TimetableResult(selection=sel)
