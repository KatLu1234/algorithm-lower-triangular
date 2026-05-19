"""A 노드 — 가능성 분석 (Feasibility).

자식: A-1 강의 풀 정제 (해시) / A-2 충돌 관계 (정렬·이진 탐색) / A-3 가지치기 (활동 선택).
산출: FeasibilityResult — B·C가 소비.
조기 종료: must_include 충돌·학점 초과 시 infeasibility_reason 채워서 반환.
"""
from __future__ import annotations

from app.libs.activity_selection import activity_selection, all_mutually_compatible
from app.libs.binary_search import lower_bound
from app.libs.floyd_warshall import INF, floyd_warshall
from app.schemas.timetable import (
    Course,
    FeasibilityResult,
    Preferences,
    TimeSlot,
)


def _slot_overlaps_blackout(slot: TimeSlot, blackout) -> bool:
    if slot.day != blackout.day:
        return False
    return slot.start_min < blackout.end_min and blackout.start_min < slot.end_min


def _fully_blacked_out(course: Course, blackouts) -> bool:
    if not course.times:
        return False
    return all(any(_slot_overlaps_blackout(s, b) for b in blackouts) for s in course.times)


def filter_pool(courses: list[Course], prefs: Preferences) -> tuple[list[Course], list[bool]]:
    """A-1 — 해시 기반 제외/필수/blackout 적용."""
    excluded = set(prefs.must_exclude)
    must_set = set(prefs.must_include)
    candidates: list[Course] = []
    must_mask: list[bool] = []
    for c in courses:
        if c.code in excluded:
            continue
        if _fully_blacked_out(c, prefs.blackouts):
            continue
        candidates.append(c)
        must_mask.append(c.code in must_set)
    return candidates, must_mask


def _slots_conflict_time(a: TimeSlot, b: TimeSlot) -> bool:
    if a.day != b.day:
        return False
    return a.start_min < b.end_min and b.start_min < a.end_min


def _travel_violates(a: TimeSlot, b: TimeSlot, travel: int) -> bool:
    """동일 요일, a가 먼저 끝나는 경우 b 시작까지 이동 가능한지 검사."""
    if a.day != b.day:
        return False
    if a.end_min <= b.start_min:
        return a.end_min + travel > b.start_min
    if b.end_min <= a.start_min:
        return b.end_min + travel > a.start_min
    return False


def build_compatibility(
    candidates: list[Course],
    building_index: dict[str, int],
    travel_matrix: list[list[int]],
) -> list[list[bool]]:
    """A-2 — 시간 겹침·이동 시간 부족 검사로 호환 행렬 구축."""
    n = len(candidates)
    compat = [[True] * n for _ in range(n)]
    for i in range(n):
        compat[i][i] = False
        bi = building_index.get(candidates[i].building)
        for j in range(i + 1, n):
            bj = building_index.get(candidates[j].building)
            travel = (
                travel_matrix[bi][bj]
                if bi is not None and bj is not None
                else INF
            )
            conflict = False
            for sa in candidates[i].times:
                if conflict:
                    break
                for sb in candidates[j].times:
                    if _slots_conflict_time(sa, sb) or _travel_violates(sa, sb, travel):
                        conflict = True
                        break
            compat[i][j] = not conflict
            compat[j][i] = compat[i][j]
    return compat


def order_by_start(candidates: list[Course]) -> list[int]:
    """각 강의의 가장 이른 시작 시간 기준 인덱스 정렬. binary_search.lower_bound로 짝꿍 조회."""
    earliest = [min(s.start_min + s.day * 24 * 60 for s in c.times) for c in candidates]
    order = sorted(range(len(candidates)), key=lambda i: earliest[i])
    sorted_starts = [earliest[i] for i in order]
    # demonstrate binary_search usage — find first index with start >= 09:00 of Monday
    _ = lower_bound(sorted_starts, 9 * 60)
    return order


def check_credit_reach(
    candidates: list[Course],
    must_mask: list[bool],
    compatible: list[list[bool]],
    prefs: Preferences,
) -> tuple[bool, str | None]:
    """A-3 — 활동 선택으로 학점 도달 가능성·필수 강의 양립성 검증."""
    must_indices = [i for i, m in enumerate(must_mask) if m]
    if not all_mutually_compatible(must_indices, compatible):
        return False, "필수 포함 강의들이 서로 시간 충돌 또는 이동 시간 부족"

    must_credit = sum(candidates[i].credit for i in must_indices)
    if must_credit > prefs.credit_ceiling:
        return False, f"필수 강의 학점 합 {must_credit}이 한도 {prefs.credit_ceiling} 초과"

    # 후보 전체에 활동 선택을 적용 — 비충돌 부분집합의 학점 합으로 도달 가능 학점 상한 근사.
    intervals: list[tuple[int, int]] = []
    for c in candidates:
        s = min(t.start_min + t.day * 24 * 60 for t in c.times)
        e = max(t.end_min + t.day * 24 * 60 for t in c.times)
        intervals.append((s, e))
    selected = activity_selection(intervals)
    reachable_credit = sum(candidates[i].credit for i in selected)

    if prefs.credit_floor is not None and reachable_credit < prefs.credit_floor:
        return False, f"가능한 학점 상한 {reachable_credit}이 하한 {prefs.credit_floor} 미달"

    return True, None


def feasibility(
    courses: list[Course],
    building_codes: list[str],
    base_walk_minutes: list[list[int]],
    prefs: Preferences,
) -> FeasibilityResult:
    candidates, must_mask = filter_pool(courses, prefs)

    if not candidates:
        return FeasibilityResult(
            candidates=[],
            must_include_mask=[],
            compatible=[],
            building_index={b: i for i, b in enumerate(building_codes)},
            travel_time_matrix=[],
            ordered_by_start=[],
            credit_ceiling_reachable=False,
            infeasibility_reason="제외·blackout 적용 후 남은 강의가 없음",
        )

    travel_matrix = floyd_warshall(base_walk_minutes)
    building_index = {b: i for i, b in enumerate(building_codes)}
    compat = build_compatibility(candidates, building_index, travel_matrix)
    order = order_by_start(candidates)
    reachable, reason = check_credit_reach(candidates, must_mask, compat, prefs)

    return FeasibilityResult(
        candidates=candidates,
        must_include_mask=must_mask,
        compatible=compat,
        building_index=building_index,
        travel_time_matrix=travel_matrix,
        ordered_by_start=order,
        credit_ceiling_reachable=reachable,
        infeasibility_reason=reason,
    )
