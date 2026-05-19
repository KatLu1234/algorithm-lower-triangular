"""SelectionResult — C 선택과 비교의 출력, 응답 단계의 입력.

권위 있는 출처: `claude/base/drafts/algorithm-tree.md` §9.6.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import CourseId
from .valuation import ScoredSchedule


class RationaleStatus(str, Enum):
    """강의가 결과에 들어갔는가 / 빠졌는가."""

    INCLUDED = "included"
    EXCLUDED = "excluded"


class StageCode(str, Enum):
    """C-3 사유 색인의 단계 코드."""

    # 포함 사유
    A1_MUST_INCLUDE = "A-1.must_include"
    B3_SELECTED = "B-3.selected_by_DP"

    # A-1 단계 배제 사유
    A1_USER_EXCLUDED = "A-1.user_excluded"
    A1_DATA_INVALID = "A-1.data_invalid"
    A1_BLACKOUT_CONFLICT = "A-1.blackout_conflict"
    A1_GROUP_EXCLUDED = "A-1.group_excluded"
    """과목 그룹 전체가 exclude_groups로 제외된 경우."""

    # A-2 단계 배제 사유
    A2_TIME_CONFLICT = "A-2.time_conflict"
    A2_TRAVEL_INFEASIBLE = "A-2.travel_infeasible"
    A2_GROUP_DUPLICATE = "A-2.group_duplicate"
    """같은 course_group_id의 다른 분반과 양립 불가 (그룹당 최대 1개 규칙)."""

    # A-3 단계 배제 사유
    A3_PRUNED = "A-3.pruned"

    # B-3 단계 배제 사유
    B3_SCORE_TOO_LOW = "B-3.score_too_low"
    B3_CREDIT_BUMPED = "B-3.credit_bumped"
    B3_GROUP_LOSER = "B-3.group_loser"
    """같은 그룹 안에서 다른 분반이 더 높은 점수로 선택됨."""

    # 최종 단계
    C1_NOT_IN_TOP_N = "C-1.not_in_top_n"


class Rationale(BaseModel):
    """한 강의가 결과에 들어갔거나 빠진 이유 한 줄."""

    model_config = ConfigDict(frozen=True)

    course_id: CourseId
    status: RationaleStatus
    stage_code: StageCode = Field(description="결정이 일어난 트리 단계")
    detail: str = Field(description="사람이 읽는 1줄 설명")
    related_course_ids: list[CourseId] = Field(
        default_factory=list,
        description="결정에 관여한 다른 강의들 (예: 시간 충돌 상대 또는 같은 그룹 다른 분반)",
    )
    score_contribution: Optional[float] = Field(
        default=None,
        description="포함된 강의의 v(c) 기여 (있을 때만)",
    )


class DiffInfo(BaseModel):
    """두 후보 시간표 간 공통·차이 (C-2 LCS 결과)."""

    model_config = ConfigDict(frozen=True)

    common: list[CourseId] = Field(description="두 시간표의 공통 강의 (백본)")
    only_in_left: list[CourseId] = Field(default_factory=list)
    only_in_right: list[CourseId] = Field(default_factory=list)
    edit_distance: Optional[int] = Field(default=None)


class SelectionResult(BaseModel):
    """C → 응답 (LLM-B) 인계 패키지."""

    model_config = ConfigDict(frozen=True)

    ranked_schedules: list[ScoredSchedule] = Field(
        description="N개 (다양성 후처리 후 확정 순서)",
    )
    pairwise_diff: dict[tuple[int, int], DiffInfo] = Field(
        default_factory=dict,
        description="(i, j) 순위 쌍 → 공통/차이",
    )
    course_rationale: dict[CourseId, Rationale] = Field(
        default_factory=dict,
        description="후보 풀의 모든 강의 ID → 사유. LLM-B 풀이의 단일 진실 출처.",
    )
    diversity_adjustment_applied: bool = Field(
        default=False,
        description="C-1 다양성 5% 양보가 적용됐는가",
    )
    notes: list[str] = Field(default_factory=list)

    @property
    def top_count(self) -> int:
        return len(self.ranked_schedules)

    def rationale_for(self, course_id: CourseId) -> Optional[Rationale]:
        return self.course_rationale.get(course_id)
