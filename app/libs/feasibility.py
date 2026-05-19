"""A 노드 — 가능성 분석 (Feasibility).

자식: A-1 강의 풀 정제 (해시·blackout) / A-2 충돌 관계 (정렬·이진 + Floyd-Warshall)
       / A-3 가지치기 (활동 선택 + 학점 도달 가능성).
출력: FeasibilityResult. 조기 종료 시 infeasibility 필드를 채워 B·C를 건너뛴다.
"""
from __future__ import annotations

from app.libs.activity_selection import activity_selection
from app.libs.floyd_warshall import floyd_warshall
from app.schemas import (
    BuildingCode,
    Course,
    CourseId,
    FeasibilityResult,
    InfeasibilityReason,
    InfeasibilityReport,
    PreferenceVector,
    TimeSlot,
    Weekday,
)

_WEEKDAY_ORDER: dict[Weekday, int] = {
    Weekday.MON: 0, Weekday.TUE: 1, Weekday.WED: 2, Weekday.THU: 3,
    Weekday.FRI: 4, Weekday.SAT: 5, Weekday.SUN: 6,
}
_LARGE_TRAVEL = 10**6


def _fully_blacked_out(course: Course, prefs: PreferenceVector) -> bool:
    if not course.times:
        return False
    return all(
        any(bw.overlaps_slot(s) for bw in prefs.blackout_windows)
        for s in course.times
    )


def filter_pool(prefs: PreferenceVector) -> tuple[list[Course], set[CourseId]]:
    """A-1 — exclude·blackout 필터 + must_include 잠금 플래그."""
    candidates: list[Course] = []
    must_mask: set[CourseId] = set()
    for c in prefs.courses:
        if c.id in prefs.exclude:
            continue
        if _fully_blacked_out(c, prefs):
            continue
        candidates.append(c)
        if c.id in prefs.must_include:
            must_mask.add(c.id)
    return candidates, must_mask


def build_travel_table(
    building_codes: list[BuildingCode],
    base_walk_minutes: list[list[int]],
) -> tuple[dict[tuple[BuildingCode, BuildingCode], int], list[list[int]]]:
    """Floyd-Warshall (DP) — 모든 쌍 최단 이동 시간 dict + 보조 행렬."""
    shortest = floyd_warshall(base_walk_minutes)
    table: dict[tuple[BuildingCode, BuildingCode], int] = {}
    for i, bi in enumerate(building_codes):
        for j, bj in enumerate(building_codes):
            if i == j:
                continue
            table[(bi, bj)] = shortest[i][j]
    return table, shortest


def _travel(a: BuildingCode, b: BuildingCode, table: dict) -> int:
    if a == b:
        return 0
    if (a, b) in table:
        return table[(a, b)]
    if (b, a) in table:
        return table[(b, a)]
    return _LARGE_TRAVEL


def _travel_violation(sa: TimeSlot, sb: TimeSlot, travel: int) -> bool:
    if sa.day != sb.day:
        return False
    if sa.end_minute <= sb.start_minute:
        return sa.end_minute + travel > sb.start_minute
    if sb.end_minute <= sa.start_minute:
        return sb.end_minute + travel > sa.start_minute
    return False


def build_compatibility(
    candidates: list[Course],
    travel_table: dict[tuple[BuildingCode, BuildingCode], int],
) -> dict[tuple[CourseId, CourseId], bool]:
    """A-2 — 시간 겹침·이동 시간 부족 검사. 키는 정렬된 (id, id)."""
    compat: dict[tuple[CourseId, CourseId], bool] = {}
    n = len(candidates)
    for i in range(n):
        ci = candidates[i]
        for j in range(i + 1, n):
            cj = candidates[j]
            travel = _travel(ci.building, cj.building, travel_table)
            conflict = False
            for sa in ci.times:
                if conflict:
                    break
                for sb in cj.times:
                    if sa.overlaps(sb) or _travel_violation(sa, sb, travel):
                        conflict = True
                        break
            key: tuple[CourseId, CourseId] = tuple(sorted((ci.id, cj.id)))  # type: ignore[assignment]
            compat[key] = not conflict
    return compat


def _earliest_min(course: Course) -> int:
    return min(_WEEKDAY_ORDER[s.day] * 24 * 60 + s.start_minute for s in course.times)


def order_by_start(candidates: list[Course]) -> list[CourseId]:
    """시간 순 시퀀스 (B-3 행렬경로 DP가 소비)."""
    return [c.id for c in sorted(candidates, key=_earliest_min)]


def _all_pairs_compatible(
    ids: list[CourseId],
    compatible: dict[tuple[CourseId, CourseId], bool],
) -> tuple[bool, list[CourseId]]:
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            key: tuple[CourseId, CourseId] = tuple(sorted((ids[a], ids[b])))  # type: ignore[assignment]
            if not compatible.get(key, False):
                return False, [ids[a], ids[b]]
    return True, []


def _check_credit_reach(
    candidates: list[Course],
    must_mask: set[CourseId],
    compatible: dict[tuple[CourseId, CourseId], bool],
    prefs: PreferenceVector,
) -> tuple[bool, InfeasibilityReport | None]:
    """A-3 — 필수 양립성·학점 도달 가능성 (활동 선택 기반)."""
    by_id = {c.id: c for c in candidates}
    must_ids = [c.id for c in candidates if c.id in must_mask]

    ok, offending = _all_pairs_compatible(must_ids, compatible)
    if not ok:
        return False, InfeasibilityReport(
            reason=InfeasibilityReason.MUST_INCLUDE_PAIR_CONFLICT,
            stage="A-3",
            detail=f"필수 강의가 서로 시간 충돌 또는 이동 시간 부족: {offending}",
            resolution_hint="필수 포함 강의 중 충돌하는 한쪽을 해제하세요.",
            offending_course_ids=offending,
        )

    must_credit = sum(by_id[i].credit for i in must_ids)
    if must_credit > prefs.credit_max:
        return False, InfeasibilityReport(
            reason=InfeasibilityReason.CREDIT_CEILING_UNREACHABLE,
            stage="A-3",
            detail=f"필수 강의 학점 합 {must_credit}이 상한 {prefs.credit_max} 초과",
            resolution_hint="필수 강의 일부를 해제하거나 학점 상한을 높이세요.",
            offending_course_ids=must_ids,
        )

    # 활동 선택으로 비충돌 부분집합의 학점 상한 근사
    intervals: list[tuple[int, int]] = []
    for c in candidates:
        ranges = [
            (_WEEKDAY_ORDER[s.day] * 24 * 60 + s.start_minute,
             _WEEKDAY_ORDER[s.day] * 24 * 60 + s.end_minute)
            for s in c.times
        ]
        s_min = min(r[0] for r in ranges)
        e_max = max(r[1] for r in ranges)
        intervals.append((s_min, e_max))
    picked = activity_selection(intervals)
    reachable_credit = sum(candidates[i].credit for i in picked)
    if reachable_credit < prefs.credit_min:
        return False, InfeasibilityReport(
            reason=InfeasibilityReason.CREDIT_CEILING_UNREACHABLE,
            stage="A-3",
            detail=f"활동 선택 기준 도달 가능 학점 {reachable_credit}이 하한 {prefs.credit_min} 미달",
            resolution_hint="후보 강의를 더 추가하거나 학점 하한을 낮추세요.",
            offending_course_ids=[],
        )
    return True, None


def feasibility(
    prefs: PreferenceVector,
    building_codes: list[BuildingCode],
    base_walk_minutes: list[list[int]],
) -> FeasibilityResult:
    candidates, must_mask = filter_pool(prefs)

    if not candidates:
        return FeasibilityResult(
            candidates=[],
            must_include_mask=set(),
            compatible={},
            travel_time_table={},
            ordered_by_start=[],
            credit_ceiling_reachable=False,
            infeasibility=InfeasibilityReport(
                reason=InfeasibilityReason.EMPTY_POOL,
                stage="A-1",
                detail="exclude·blackout 적용 후 남은 강의가 없음",
                resolution_hint="제외 목록 또는 blackout을 조정해 후보를 확보하세요.",
                offending_course_ids=[],
            ),
        )

    # 필수 강의 중 풀에서 제거된 게 있으면 A-1 단계에서 잡힘
    missing_must = prefs.must_include - must_mask
    if missing_must:
        return FeasibilityResult(
            candidates=candidates,
            must_include_mask=must_mask,
            compatible={},
            travel_time_table={},
            ordered_by_start=[],
            credit_ceiling_reachable=False,
            infeasibility=InfeasibilityReport(
                reason=InfeasibilityReason.MUST_INCLUDE_BLACKOUT_CONFLICT,
                stage="A-1",
                detail=f"필수 강의가 exclude 또는 blackout과 충돌해 풀에서 빠짐: {sorted(missing_must)}",
                resolution_hint="해당 필수 강의의 blackout 또는 exclude 설정을 해제하세요.",
                offending_course_ids=sorted(missing_must),
            ),
        )

    travel_table, _ = build_travel_table(building_codes, base_walk_minutes)
    compat = build_compatibility(candidates, travel_table)
    ordered = order_by_start(candidates)
    reachable, infeas = _check_credit_reach(candidates, must_mask, compat, prefs)

    return FeasibilityResult(
        candidates=candidates,
        must_include_mask=must_mask,
        compatible=compat,
        travel_time_table=travel_table,
        ordered_by_start=ordered,
        credit_ceiling_reachable=reachable,
        infeasibility=infeas,
    )
