"""C 노드 — 선택과 비교 (Selection).

자식: C-1 상위 N개 정렬·다양성 (안정 합병 정렬) / C-2 쌍 비교 (LCS) / C-3 사유 색인 (해시).
산출: SelectionResult — 최종 응답.
"""
from __future__ import annotations

from app.libs.lcs import lcs
from app.libs.merge_sort import merge_sort
from app.schemas.timetable import (
    CourseRationale,
    FeasibilityResult,
    PairwiseDiff,
    ScheduleCandidate,
    SelectionResult,
    ValuationResult,
)

_DIVERSITY_JACCARD_THRESHOLD = 0.8
_DIVERSITY_PENALTY_RATIO = 0.05  # product.md §4.2 — 5% 양보 한도


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def diversity_adjust(
    candidates: list[ScheduleCandidate],
) -> tuple[list[ScheduleCandidate], bool]:
    """C-1 — 상위와 Jaccard > 0.8이면 5% 점수 감점 후 안정 정렬로 재배치."""
    if len(candidates) <= 1:
        return list(candidates), False
    top = candidates[0]
    adjusted = [candidates[0]]
    applied = False
    for c in candidates[1:]:
        if _jaccard(top.course_codes, c.course_codes) > _DIVERSITY_JACCARD_THRESHOLD:
            applied = True
            new_total = c.total_score * (1 - _DIVERSITY_PENALTY_RATIO)
            adjusted.append(c.model_copy(update={"total_score": new_total}))
        else:
            adjusted.append(c)
    resorted = merge_sort(adjusted, key=lambda x: x.total_score, reverse=True)
    return resorted, applied


def pairwise_compare(candidates: list[ScheduleCandidate]) -> list[PairwiseDiff]:
    """C-2 — 상위 K개의 두 쌍씩 공통 백본·차이 추출 (LCS 기반)."""
    diffs: list[PairwiseDiff] = []
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            a = sorted(candidates[i].course_codes)
            b = sorted(candidates[j].course_codes)
            backbone = lcs(a, b)
            backbone_set = set(backbone)
            only_a = [c for c in candidates[i].course_codes if c not in backbone_set]
            only_b = [c for c in candidates[j].course_codes if c not in backbone_set]
            diffs.append(
                PairwiseDiff(
                    rank_a=i + 1,
                    rank_b=j + 1,
                    common_backbone=backbone,
                    only_in_a=only_a,
                    only_in_b=only_b,
                )
            )
    return diffs


def course_rationale(
    feas: FeasibilityResult,
    ranked: list[ScheduleCandidate],
) -> list[CourseRationale]:
    """C-3 — 강의별 포함 순위·배제 사유 색인 (해시)."""
    rank_index: dict[str, list[int]] = {}
    for rank, sched in enumerate(ranked, start=1):
        for code in sched.course_codes:
            rank_index.setdefault(code, []).append(rank)

    out: list[CourseRationale] = []
    for c in feas.candidates:
        ranks = rank_index.get(c.code, [])
        reason: str | None
        if ranks:
            reason = None
        else:
            reason = "상위 후보에 포함되지 않음 — 점수 합이 더 낮거나 호환 후보와 양립 불가"
        out.append(
            CourseRationale(
                code=c.code,
                included_in_ranks=ranks,
                excluded_reason=reason,
            )
        )
    return out


def selection(feas: FeasibilityResult, val: ValuationResult) -> SelectionResult:
    ranked, applied = diversity_adjust(val.top_k_candidates)
    diffs = pairwise_compare(ranked)
    rationale = course_rationale(feas, ranked)
    return SelectionResult(
        ranked_schedules=ranked,
        pairwise_diff=diffs,
        course_rationale=rationale,
        diversity_adjustment_applied=applied,
    )
