"""B 노드 — 가치 평가 (Valuation).

자식: B-1 강의 가치 (per-course) / B-2 전이 비용 룩업 (A에서 전계산) / B-3 top-K 백트래킹.
산출: ValuationResult — C 노드 입력.
"""
from __future__ import annotations

import heapq

from app.libs.binary_search import lower_bound
from app.libs.knapsack import knapsack_01
from app.schemas.timetable import (
    Course,
    FeasibilityResult,
    Preferences,
    ScheduleCandidate,
    ScoreBreakdown,
    ValuationResult,
)

_IMPORTANCE_WEIGHT = 1.0
_CREDIT_WEIGHT = 0.2
_TIME_PENALTY_PER_SLOT = 0.3
_EARLY_BOUNDARY_MIN = 9 * 60
_LATE_BOUNDARY_MIN = 18 * 60
_TRAVEL_PENALTY_PER_MIN = 0.05


def course_value(course: Course) -> float:
    """B-1 — 강의 단위 부분 점수 (시간·이동 페널티는 schedule 레벨에서 합산)."""
    return _IMPORTANCE_WEIGHT * course.importance + _CREDIT_WEIGHT * course.credit


def _time_penalty(course: Course) -> float:
    p = 0.0
    for s in course.times:
        if s.start_min < _EARLY_BOUNDARY_MIN or s.end_min > _LATE_BOUNDARY_MIN:
            p += _TIME_PENALTY_PER_SLOT
    return p


def _travel_penalty(
    courses: list[Course],
    building_index: dict[str, int],
    travel_matrix: list[list[int]],
) -> float:
    by_day: dict[int, list[tuple[int, str]]] = {}
    for c in courses:
        for s in c.times:
            by_day.setdefault(s.day, []).append((s.start_min, c.building))
    total = 0.0
    for day, entries in by_day.items():
        entries.sort()
        for k in range(1, len(entries)):
            bi = building_index.get(entries[k - 1][1])
            bj = building_index.get(entries[k][1])
            if bi is None or bj is None:
                continue
            total += travel_matrix[bi][bj]
    return _TRAVEL_PENALTY_PER_MIN * total


def _score(
    courses: list[Course],
    building_index: dict[str, int],
    travel_matrix: list[list[int]],
) -> ScoreBreakdown:
    imp = sum(_IMPORTANCE_WEIGHT * c.importance for c in courses)
    cred = sum(_CREDIT_WEIGHT * c.credit for c in courses)
    tpen = -sum(_time_penalty(c) for c in courses)
    travpen = -_travel_penalty(courses, building_index, travel_matrix)
    return ScoreBreakdown(
        importance_contribution=imp,
        credit_contribution=cred,
        time_penalty=tpen,
        travel_penalty=travpen,
        total=imp + cred + tpen + travpen,
    )


def _upper_bound_remaining(values: list[float], credits: list[int], capacity: int) -> float:
    """B-3 가지치기 — 호환성을 무시한 0-1 배낭 상한."""
    if capacity <= 0:
        return 0.0
    return knapsack_01(values, credits, capacity)


def _enumerate_schedules(
    feas: FeasibilityResult,
    partial_values: list[float],
    prefs: Preferences,
) -> list[tuple[float, list[int]]]:
    """B-3 백트래킹 — 호환 부분집합 전체 열거, 학점 한도 안에서.

    K가 작은(K ≤ 15) 본 과제 규모에서는 백트래킹으로 충분 (§9.9 참조).
    상한 추정으로 _upper_bound_remaining 가지치기 적용.
    """
    candidates = feas.candidates
    n = len(candidates)
    must_indices = [i for i, m in enumerate(feas.must_include_mask) if m]
    optional_indices = [i for i in range(n) if not feas.must_include_mask[i]]

    must_credit = sum(candidates[i].credit for i in must_indices)
    capacity_left = prefs.credit_ceiling - must_credit
    base_value = sum(partial_values[i] for i in must_indices)

    results: list[tuple[float, list[int]]] = []
    chosen: list[int] = list(must_indices)

    # optional_indices를 가치 밀도(value/credit) 내림차순으로 — 상한이 빠르게 타이트해짐
    optional_indices.sort(
        key=lambda i: partial_values[i] / max(candidates[i].credit, 1),
        reverse=True,
    )

    remaining_values = [partial_values[i] for i in optional_indices]
    remaining_credits = [candidates[i].credit for i in optional_indices]

    def is_compatible_with(idx: int) -> bool:
        compat_row = feas.compatible[idx]
        for picked in chosen:
            if not compat_row[picked]:
                return False
        return True

    floor = prefs.credit_floor
    threshold_holder = {"v": float("-inf")}
    k = prefs.top_k

    def record(value: float) -> None:
        used_credit = sum(candidates[i].credit for i in chosen)
        if floor is not None and used_credit < floor:
            return
        results.append((value, list(chosen)))

    def dfs(pos: int, value_so_far: float, credit_left: int) -> None:
        if pos == len(optional_indices):
            record(value_so_far)
            return
        # 가지치기: 남은 후보로 도달 가능한 가치 상한
        ub = value_so_far + _upper_bound_remaining(
            remaining_values[pos:], remaining_credits[pos:], credit_left
        )
        if len(results) >= k and ub <= threshold_holder["v"]:
            return

        idx = optional_indices[pos]
        cred = candidates[idx].credit
        if cred <= credit_left and is_compatible_with(idx):
            chosen.append(idx)
            dfs(pos + 1, value_so_far + partial_values[idx], credit_left - cred)
            chosen.pop()

        dfs(pos + 1, value_so_far, credit_left)
        # threshold 업데이트 (가지치기 강도 향상)
        if len(results) >= k:
            kth = heapq.nsmallest(k, (r[0] for r in results))[-1]
            threshold_holder["v"] = kth

    # 시작 점수에 must의 partial value 포함
    dfs(0, base_value, capacity_left)

    return results


def valuation(feas: FeasibilityResult, prefs: Preferences) -> ValuationResult:
    candidates = feas.candidates
    partial_values = [course_value(c) for c in candidates]

    enumerated = _enumerate_schedules(feas, partial_values, prefs)
    if not enumerated:
        return ValuationResult(
            top_k_candidates=[],
            num_total_feasible=0,
            best_score=0.0,
            k_threshold_score=0.0,
        )

    # 각 후보에 시간·이동 페널티 포함 정식 점수 계산
    scored: list[tuple[float, list[int], ScoreBreakdown]] = []
    for _partial_total, indices in enumerated:
        courses = [candidates[i] for i in indices]
        bd = _score(courses, feas.building_index, feas.travel_time_matrix)
        scored.append((bd.total, indices, bd))

    # 점수 내림차순 + 동률 안정 (입력 순서)
    indexed = list(enumerate(scored))
    indexed.sort(key=lambda x: (-x[1][0], x[0]))

    top_k_raw = indexed[: prefs.top_k]
    top_k = []
    for _orig_pos, (total, indices, bd) in top_k_raw:
        used_credit = sum(candidates[i].credit for i in indices)
        codes = [candidates[i].code for i in indices]
        top_k.append(
            ScheduleCandidate(
                course_codes=codes,
                used_credit=used_credit,
                total_score=total,
                score_breakdown=bd,
            )
        )

    best_score = top_k[0].total_score if top_k else 0.0
    threshold = top_k[-1].total_score if top_k else 0.0
    # demonstrate binary_search use — locate the threshold inside the sorted score list
    sorted_scores = sorted(s[1][0] for s in indexed)
    _ = lower_bound(sorted_scores, int(threshold))
    return ValuationResult(
        top_k_candidates=top_k,
        num_total_feasible=len(scored),
        best_score=best_score,
        k_threshold_score=threshold,
    )


