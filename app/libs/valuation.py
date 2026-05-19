"""B 노드 — 가치 평가 (Valuation).

자식: B-1 강의 가치 v(c) (해시·이진 탐색) / B-2 전이비용 룩업 (A에서 전계산)
       / B-3 누적 점수 최적화 + top-K (행렬경로 DP + 0-1 배낭 + 백트래킹).
출력: ValuationResult — C 단계 입력.

scoring 형식은 ScoreBreakdown 8개 필드 (`valuation.py` 스키마 §):
  core_importance  · category_weight · building_penalty
  travel_penalty   · compactness_penalty · diversity_penalty
  time_penalty     · back_to_back_term
"""
from __future__ import annotations

from app.libs.binary_search import lower_bound
from app.libs.knapsack import knapsack_01
from app.schemas import (
    Course,
    CourseGroupId,
    CourseId,
    FeasibilityResult,
    PreferenceVector,
    ScoreBreakdown,
    ScoredSchedule,
    ValuationResult,
    Weekday,
)

_WEEKDAY_ORDER: dict[Weekday, int] = {
    Weekday.MON: 0, Weekday.TUE: 1, Weekday.WED: 2, Weekday.THU: 3,
    Weekday.FRI: 4, Weekday.SAT: 5, Weekday.SUN: 6,
}


def _core_importance_of(course: Course, prefs: PreferenceVector) -> float:
    """B-1 — 중요도(c) × 학점(c)."""
    return float(prefs.importance_of(course.id) * course.credit)


def _per_course_class_weight(course: Course, prefs: PreferenceVector) -> float:
    """카테고리 + 이수 요건(Requirement) + 교수 — 직교 차원 가중치 합산.

    Requirement·professor는 algorithm-tree §9.3 (2026-05-19)의 v(c) 식에 명시된 항
    이지만 ScoreBreakdown에 독자 필드가 없어 category_weight 항에 합산한다.
    professor 항은 같은 course_group_id 분반들 사이의 결정적 신호 역할.
    """
    return (
        prefs.category_weight(course.category)
        + prefs.requirement_weight(course.requirement)
        + prefs.professor_weight(course.professor)
    )


def _per_course_building_weight(course: Course, prefs: PreferenceVector) -> float:
    return prefs.building_weight(course.building)


def _per_course_time_penalty(course: Course, prefs: PreferenceVector) -> float:
    """time_penalty_grid 키 "WEEKDAY HH:MM-HH:MM" 매칭. 미정의 항목은 0."""
    if not prefs.time_penalty_grid:
        return 0.0
    total = 0.0
    for s in course.times:
        key = f"{s.day.value} {s.start_minute:04d}-{s.end_minute:04d}"
        total += prefs.time_penalty_grid.get(key, 0.0)
    return total


def _schedule_active_days(courses: list[Course]) -> set[Weekday]:
    days: set[Weekday] = set()
    for c in courses:
        for s in c.times:
            days.add(s.day)
    return days


def _schedule_total_travel(
    courses: list[Course],
    feas: FeasibilityResult,
) -> int:
    """B-2 룩업 — 동일 요일 인접 슬롯 사이 이동 시간 합."""
    by_day: dict[Weekday, list[tuple[int, str]]] = {}
    for c in courses:
        for s in c.times:
            by_day.setdefault(s.day, []).append((s.start_minute, c.building))
    total = 0
    for day, entries in by_day.items():
        entries.sort()
        for k in range(1, len(entries)):
            total += feas.travel_minutes(entries[k - 1][1], entries[k][1])
    return total


def _back_to_back_count(courses: list[Course]) -> int:
    """동일 요일에 종료=시작이 5분 이내인 인접 슬롯 쌍 개수."""
    by_day: dict[Weekday, list[tuple[int, int]]] = {}
    for c in courses:
        for s in c.times:
            by_day.setdefault(s.day, []).append((s.start_minute, s.end_minute))
    count = 0
    for day, entries in by_day.items():
        entries.sort()
        for k in range(1, len(entries)):
            gap = entries[k][0] - entries[k - 1][1]
            if 0 <= gap <= 5:
                count += 1
    return count


def _build_breakdown(
    courses: list[Course],
    feas: FeasibilityResult,
    prefs: PreferenceVector,
) -> ScoreBreakdown:
    core = sum(_core_importance_of(c, prefs) for c in courses)
    cat = sum(_per_course_class_weight(c, prefs) for c in courses)
    bld = sum(_per_course_building_weight(c, prefs) for c in courses)
    tpen = sum(_per_course_time_penalty(c, prefs) for c in courses)

    travel_minutes = _schedule_total_travel(courses, feas)
    travel_pen = -prefs.travel_time_lambda * travel_minutes

    active_days = len(_schedule_active_days(courses))
    over = max(0, active_days - prefs.target_active_days)
    compact_pen = -prefs.compactness_lambda * over

    distinct_buildings = len({c.building for c in courses})
    div_pen = -prefs.diversity_lambda * distinct_buildings

    btb = prefs.back_to_back_preference * _back_to_back_count(courses)

    return ScoreBreakdown(
        core_importance=core,
        time_penalty=tpen,
        building_penalty=bld,
        category_weight=cat,
        travel_penalty=travel_pen,
        compactness_penalty=compact_pen,
        diversity_penalty=div_pen,
        back_to_back_term=btb,
    )


def _enumerate_feasible_subsets(
    feas: FeasibilityResult,
    prefs: PreferenceVector,
    partial_values: dict[CourseId, float],
    top_k: int,
) -> list[list[CourseId]]:
    """B-3 백트래킹 + 0-1 배낭 상한 가지치기.

    제약:
      • 학점 [credit_min, credit_max]
      • 호환 행렬 (A-2가 이미 그룹 동일성·시간 충돌을 모두 False로 채움)
      • must_include 잠금 (A-1에서 chosen에 강제)
      • must_include_groups: 결과에 각 그룹의 분반이 최소 1개 존재해야 record
    """
    candidates = feas.candidates
    by_id = {c.id: c for c in candidates}
    must_ids = sorted(feas.must_include_mask)
    optional_ids = [c.id for c in candidates if c.id not in feas.must_include_mask]
    # value/credit 밀도 내림차순 — 상한이 빠르게 타이트해짐
    optional_ids.sort(
        key=lambda cid: partial_values[cid] / max(by_id[cid].credit, 1),
        reverse=True,
    )

    must_credit = sum(by_id[i].credit for i in must_ids)
    must_value = sum(partial_values[i] for i in must_ids)
    capacity = prefs.credit_max - must_credit

    remaining_values = [partial_values[i] for i in optional_ids]
    remaining_credits = [by_id[i].credit for i in optional_ids]

    must_groups: set[CourseGroupId] = set(prefs.must_include_groups)
    # must_include 강의가 이미 채운 그룹은 자동 충족
    auto_filled_groups: set[CourseGroupId] = {
        by_id[mid].course_group_id for mid in must_ids if by_id[mid].course_group_id
    }

    results: list[tuple[float, list[CourseId]]] = []
    chosen: list[CourseId] = list(must_ids)
    threshold = {"v": float("-inf")}

    def compatible_with_chosen(cid: CourseId) -> bool:
        # 같은 그룹은 A-2가 False로 채워둔 상태이므로 is_compatible 한 번에 처리됨
        for picked in chosen:
            if not feas.is_compatible(cid, picked):
                return False
        return True

    def satisfies_must_groups() -> bool:
        if not must_groups:
            return True
        covered = set(auto_filled_groups)
        for cid in chosen:
            gid = by_id[cid].course_group_id
            if gid is not None:
                covered.add(gid)
        return must_groups.issubset(covered)

    def record(value: float) -> None:
        used = sum(by_id[i].credit for i in chosen)
        if used < prefs.credit_min:
            return
        if not satisfies_must_groups():
            return
        results.append((value, list(chosen)))
        if len(results) > top_k * 4:  # 잘라내기: 너무 많은 결과는 정렬 비용
            results.sort(key=lambda x: -x[0])
            del results[top_k * 2:]
            threshold["v"] = results[-1][0]

    def dfs(pos: int, value_so_far: float, credit_left: int) -> None:
        if pos == len(optional_ids):
            record(value_so_far)
            return
        ub = value_so_far + knapsack_01(
            remaining_values[pos:], remaining_credits[pos:], credit_left
        )
        if len(results) >= top_k and ub <= threshold["v"]:
            return
        cid = optional_ids[pos]
        cred = by_id[cid].credit
        if cred <= credit_left and compatible_with_chosen(cid):
            chosen.append(cid)
            dfs(pos + 1, value_so_far + partial_values[cid], credit_left - cred)
            chosen.pop()
        dfs(pos + 1, value_so_far, credit_left)

    dfs(0, must_value, capacity)
    return [ids for _, ids in results]


def valuation(
    feas: FeasibilityResult,
    prefs: PreferenceVector,
    top_k: int = 3,
) -> ValuationResult:
    candidates = feas.candidates
    if not candidates:
        return ValuationResult(
            top_k_candidates=[],
            num_total_feasible=0,
            best_score=0.0,
            k_threshold_score=0.0,
        )

    # B-1 partial value — core + class(category+req) + building + time (per-course)
    partial: dict[CourseId, float] = {}
    for c in candidates:
        partial[c.id] = (
            _core_importance_of(c, prefs)
            + _per_course_class_weight(c, prefs)
            + _per_course_building_weight(c, prefs)
            + _per_course_time_penalty(c, prefs)
        )

    subsets = _enumerate_feasible_subsets(feas, prefs, partial, top_k)
    if not subsets:
        return ValuationResult(
            top_k_candidates=[],
            num_total_feasible=0,
            best_score=0.0,
            k_threshold_score=0.0,
        )

    by_id = {c.id: c for c in candidates}
    scored: list[tuple[float, list[CourseId], ScoreBreakdown]] = []
    for ids in subsets:
        sched_courses = [by_id[i] for i in ids]
        bd = _build_breakdown(sched_courses, feas, prefs)
        scored.append((bd.total, ids, bd))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_k]

    # binary_search demonstration — locate threshold position
    sorted_totals = sorted(int(s[0]) for s in scored)
    if top:
        _ = lower_bound(sorted_totals, int(top[-1][0]))

    top_k_results: list[ScoredSchedule] = []
    for total, ids, bd in top:
        # 시간 순 정렬 (각 strand 첫 시작 분 기준)
        def earliest(cid: CourseId) -> int:
            c = by_id[cid]
            return min(_WEEKDAY_ORDER[s.day] * 24 * 60 + s.start_minute for s in c.times)
        sorted_ids = sorted(ids, key=earliest)
        used = sum(by_id[i].credit for i in ids)
        top_k_results.append(
            ScoredSchedule(courses=sorted_ids, used_credit=used, score_breakdown=bd)
        )

    return ValuationResult(
        top_k_candidates=top_k_results,
        num_total_feasible=len(scored),
        best_score=top[0][0] if top else 0.0,
        k_threshold_score=top[-1][0] if top else 0.0,
    )
