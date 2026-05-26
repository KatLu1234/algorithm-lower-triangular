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
    FeasibilityResult,
    InfeasibilityReason,
    InfeasibilityReport,
    PreferenceVector,
    SelectionResult,
)


def _max_reachable_credit_under_compat(
    feas: FeasibilityResult, prefs: PreferenceVector
) -> int:
    """양립 가능 부분집합 중 학점 합 최대치(must_include 포함, credit_max 상한 안에서).

    A-3 `_check_credit_reach`는 *요일별* activity selection으로 도달성 *상한*을 본다 —
    강의 단위 호환(이동시간·그룹 동일성)을 보지 못해 종종 과대평가된다. 그 결과
    feasibility는 통과해도 valuation 백트래킹이 모두 reject하는 케이스가 생긴다.
    본 헬퍼는 그 빈 결과에 한해 *강의 단위 호환 행렬* 기반으로 실제 최대 학점을
    한 번 더 계산해, 사용자에게 정확한 학점 한도 진단을 제공한다.

    NP-hard 일반 형태지만 N≤30 정도의 풀에서는 백트래킹으로 충분히 빠르다.
    그룹·카테고리 개수·필수 그룹 제약은 *반영하지 않는다* — 학점 한도 가능성만 본다.
    """
    candidates = feas.candidates
    by_id = {c.id: c for c in candidates}
    must_ids = sorted(feas.must_include_mask)
    optional_ids = [c.id for c in candidates if c.id not in feas.must_include_mask]

    must_credit = sum(by_id[i].credit for i in must_ids)
    # must 학점이 이미 상한 초과면 그 자체가 답 — feasibility A-3가 잡았어야 정상.
    if must_credit >= prefs.credit_max:
        return must_credit

    chosen: list[str] = list(must_ids)
    best = [must_credit]

    def compat_ok(cid: str) -> bool:
        for p in chosen:
            if not feas.is_compatible(cid, p):
                return False
        return True

    def dfs(pos: int, credit: int) -> None:
        if credit > best[0]:
            best[0] = credit
        if pos == len(optional_ids) or best[0] >= prefs.credit_max:
            return
        cid = optional_ids[pos]
        cred = by_id[cid].credit
        if credit + cred <= prefs.credit_max and compat_ok(cid):
            chosen.append(cid)
            dfs(pos + 1, credit + cred)
            chosen.pop()
        dfs(pos + 1, credit)

    dfs(0, must_credit)
    return best[0]


def _empty_result_diagnosis(
    feas: FeasibilityResult, prefs: PreferenceVector
) -> InfeasibilityReport:
    """B-3 빈 결과 — 학점 한도가 원인인지, 다른 hard 제약이 원인인지 구분한다."""
    max_credit = _max_reachable_credit_under_compat(feas, prefs)

    if max_credit < prefs.credit_min:
        # 진짜 학점 도달 불가 — credit_min 낮추거나 강의 풀 확장.
        return InfeasibilityReport(
            reason=InfeasibilityReason.CREDIT_CEILING_UNREACHABLE,
            stage="B-3",
            detail=(
                f"양립 가능한 강의 조합의 최대 학점 합은 {max_credit}학점이며, "
                f"학점 하한 {prefs.credit_min}학점에 미달합니다."
            ),
            resolution_hint=(
                f"학점 하한을 {max_credit}학점 이하로 낮추거나, "
                f"호환되는 강의를 추가 후보로 넣어 보세요. "
                f"(필수 강의·blackout·이동시간으로 일부 조합이 막혀 있을 수 있습니다.)"
            ),
            offending_course_ids=[],
        )

    # 학점은 충족 가능했지만 다른 hard 제약(그룹·카테고리 개수·중복 등)이 막은 경우.
    blockers: list[str] = []
    if prefs.must_include_groups:
        blockers.append("must_include_groups (그룹 필수 포함)")
    if prefs.category_count_min:
        blockers.append("category_count_min (카테고리 개수 하한)")
    if prefs.category_count_max:
        blockers.append("category_count_max (카테고리 개수 상한)")
    blockers_text = ", ".join(blockers) if blockers else "(미확정 제약)"

    return InfeasibilityReport(
        reason=InfeasibilityReason.CREDIT_CEILING_UNREACHABLE,
        stage="B-3",
        detail=(
            f"학점 한도는 충족 가능(최대 {max_credit}학점)하지만, "
            f"추가 hard 제약에 막혀 빈 결과: {blockers_text}."
        ),
        resolution_hint=(
            "필수 그룹·카테고리 개수 제약을 완화하거나, 호환되는 후보를 추가하세요."
        ),
        offending_course_ids=[],
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
        return _empty_result_diagnosis(feas, prefs)

    return selection(feas, val, prefs)
