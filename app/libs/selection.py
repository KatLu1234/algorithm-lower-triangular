"""C 노드 — 선택과 비교 (Selection).

자식: C-1 상위 N개 정렬·다양성 (안정 합병 정렬) / C-2 쌍 비교 (LCS)
       / C-3 강의별 사유 색인 (해시 + StageCode 분류).
출력: SelectionResult — 최종 응답·LLM-B 컨텍스트.
"""
from __future__ import annotations

from app.libs.lcs import lcs
from app.libs.merge_sort import merge_sort
from app.schemas import (
    Course,
    CourseId,
    DiffInfo,
    FeasibilityResult,
    PreferenceVector,
    Rationale,
    RationaleStatus,
    ScoreBreakdown,
    ScoredSchedule,
    SelectionResult,
    StageCode,
    ValuationResult,
)

_DIVERSITY_JACCARD_THRESHOLD = 0.8
_DIVERSITY_PENALTY_RATIO = 0.05  # product.md §4.2 — 5% 양보 한도


def _jaccard(a: list[CourseId], b: list[CourseId]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def _apply_diversity(
    schedules: list[ScoredSchedule],
) -> tuple[list[ScoredSchedule], bool]:
    """C-1 — top과 Jaccard > 0.8이면 5% 감점 후 안정 정렬 재배치."""
    if len(schedules) <= 1:
        return list(schedules), False
    top = schedules[0]
    adjusted: list[ScoredSchedule] = [top]
    applied = False
    for s in schedules[1:]:
        if _jaccard(top.courses, s.courses) > _DIVERSITY_JACCARD_THRESHOLD:
            applied = True
            bd = s.score_breakdown
            scaled = ScoreBreakdown(
                core_importance=bd.core_importance * (1 - _DIVERSITY_PENALTY_RATIO),
                time_penalty=bd.time_penalty,
                building_penalty=bd.building_penalty,
                category_weight=bd.category_weight,
                travel_penalty=bd.travel_penalty,
                compactness_penalty=bd.compactness_penalty,
                diversity_penalty=bd.diversity_penalty,
                back_to_back_term=bd.back_to_back_term,
            )
            adjusted.append(
                ScoredSchedule(courses=s.courses, used_credit=s.used_credit, score_breakdown=scaled)
            )
        else:
            adjusted.append(s)
    resorted = merge_sort(adjusted, key=lambda x: x.total_score, reverse=True)
    return resorted, applied


def _pairwise_diffs(
    schedules: list[ScoredSchedule],
) -> dict[tuple[int, int], DiffInfo]:
    """C-2 — LCS로 공통 백본 + 차이 추출. 키 (i, j)는 1-indexed, i < j."""
    diffs: dict[tuple[int, int], DiffInfo] = {}
    for i in range(len(schedules)):
        for j in range(i + 1, len(schedules)):
            a = sorted(schedules[i].courses)
            b = sorted(schedules[j].courses)
            backbone = lcs(a, b)
            backbone_set = set(backbone)
            only_left = [c for c in schedules[i].courses if c not in backbone_set]
            only_right = [c for c in schedules[j].courses if c not in backbone_set]
            diffs[(i + 1, j + 1)] = DiffInfo(
                common=backbone,
                only_in_left=only_left,
                only_in_right=only_right,
                edit_distance=None,
            )
    return diffs


def _rationale_index(
    feas: FeasibilityResult,
    prefs: PreferenceVector,
    ranked: list[ScoredSchedule],
    partial_values: dict[CourseId, float],
) -> dict[CourseId, Rationale]:
    """C-3 — 강의별 포함·배제 사유. StageCode로 단계 추적.

    그룹 관련 사유 코드:
      • A1_GROUP_EXCLUDED — exclude_groups로 인해 풀에서 제거
      • A2_GROUP_DUPLICATE — 같은 그룹 다른 분반과 양립 불가 (A-2가 False로 채운 결과)
      • B3_GROUP_LOSER — 같은 그룹 다른 분반이 상위에 선택됨
    """
    # 어느 순위에 들어갔는가
    appearance: dict[CourseId, list[int]] = {}
    for rank, s in enumerate(ranked, start=1):
        for cid in s.courses:
            appearance.setdefault(cid, []).append(rank)

    by_id = {c.id: c for c in feas.candidates}
    out: dict[CourseId, Rationale] = {}

    # 풀에 살아남은 강의: 포함됐거나 점수 부족 / 그룹 동료에게 밀림
    for c in feas.candidates:
        ranks = appearance.get(c.id, [])
        if ranks:
            is_must = c.id in feas.must_include_mask
            stage = StageCode.A1_MUST_INCLUDE if is_must else StageCode.B3_SELECTED
            detail = (
                f"필수 포함 강의로 잠금됨 (순위 {ranks})."
                if is_must
                else f"DP 최적화 결과 상위에 선택됨 (순위 {ranks})."
            )
            out[c.id] = Rationale(
                course_id=c.id,
                status=RationaleStatus.INCLUDED,
                stage_code=stage,
                detail=detail,
                related_course_ids=[],
                score_contribution=partial_values.get(c.id),
            )
        else:
            # 같은 group_id 분반 중 다른 게 결과에 들어갔는지 검사
            same_group_winners: list[CourseId] = []
            if c.course_group_id is not None:
                for other in feas.candidates:
                    if (
                        other.id != c.id
                        and other.course_group_id == c.course_group_id
                        and other.id in appearance
                    ):
                        same_group_winners.append(other.id)
            if same_group_winners:
                out[c.id] = Rationale(
                    course_id=c.id,
                    status=RationaleStatus.EXCLUDED,
                    stage_code=StageCode.B3_GROUP_LOSER,
                    detail=f"같은 과목 그룹 {c.course_group_id!r}의 다른 분반이 상위에 선택됨.",
                    related_course_ids=same_group_winners,
                    score_contribution=partial_values.get(c.id),
                )
            else:
                out[c.id] = Rationale(
                    course_id=c.id,
                    status=RationaleStatus.EXCLUDED,
                    stage_code=StageCode.B3_SCORE_TOO_LOW,
                    detail="DP 결과 상위 후보에 들지 못함 (점수·학점 trade-off).",
                    related_course_ids=[],
                    score_contribution=partial_values.get(c.id),
                )

    # 입력 풀에 있었으나 A-1에서 잘린 강의는 별도 사유로 기록
    pool_ids = {c.id for c in prefs.courses}
    survivor_ids = {c.id for c in feas.candidates}
    pool_by_id = {c.id: c for c in prefs.courses}
    for cid in pool_ids - survivor_ids:
        pool_course = pool_by_id[cid]
        if cid in prefs.exclude:
            out[cid] = Rationale(
                course_id=cid,
                status=RationaleStatus.EXCLUDED,
                stage_code=StageCode.A1_USER_EXCLUDED,
                detail="사용자 exclude 목록에 포함됨.",
                related_course_ids=[],
                score_contribution=None,
            )
        elif (
            pool_course.course_group_id is not None
            and pool_course.course_group_id in prefs.exclude_groups
        ):
            out[cid] = Rationale(
                course_id=cid,
                status=RationaleStatus.EXCLUDED,
                stage_code=StageCode.A1_GROUP_EXCLUDED,
                detail=f"과목 그룹 {pool_course.course_group_id!r}이 exclude_groups에 포함됨.",
                related_course_ids=[],
                score_contribution=None,
            )
        else:
            out[cid] = Rationale(
                course_id=cid,
                status=RationaleStatus.EXCLUDED,
                stage_code=StageCode.A1_BLACKOUT_CONFLICT,
                detail="모든 시간대가 blackout과 겹쳐 풀에서 제외됨.",
                related_course_ids=[],
                score_contribution=None,
            )
    return out


def selection(
    feas: FeasibilityResult,
    val: ValuationResult,
    prefs: PreferenceVector,
) -> SelectionResult:
    ranked, applied = _apply_diversity(val.top_k_candidates)
    diffs = _pairwise_diffs(ranked)

    # 사유 색인용 partial 값 — B-1과 동일 식. 여기서는 별도 호출자 의존 없이 단독 계산.
    from app.libs.valuation import (  # 순환 회피 위해 지연 import
        _core_importance_of,
        _per_course_building_weight,
        _per_course_class_weight,
        _per_course_time_penalty,
    )
    partial: dict[CourseId, float] = {}
    for c in feas.candidates:
        partial[c.id] = (
            _core_importance_of(c, prefs)
            + _per_course_class_weight(c, prefs)
            + _per_course_building_weight(c, prefs)
            + _per_course_time_penalty(c, prefs)
        )

    rationale = _rationale_index(feas, prefs, ranked, partial)

    return SelectionResult(
        ranked_schedules=ranked,
        pairwise_diff=diffs,
        course_rationale=rationale,
        diversity_adjustment_applied=applied,
        notes=[],
    )
